"""Read-only command observations and descriptive benchmark statistics."""

from collections import Counter
from dataclasses import asdict
from statistics import mean, median

from aig.commands import AttackUnit, EndActivation, FoundCity, MoveUnit
from aig.knowledge import visible_enemy_units, vision_positions, known_resources
from aig.economy import city_yields, worked_positions, resource_yields, Yields
from aig.research import available_technologies
from aig.state import UnitType


FAILURE_CATEGORIES = (
    "transport_failure", "timeout", "non_2xx", "malformed_ollama_envelope",
    "malformed_json_content", "schema_validation", "invalid_strategic_references",
    "repair_failed", "heuristic_fallback",
    "authentication_failure", "permission_denied", "model_not_available", "rate_limit",
    "connection_failure", "api_error", "malformed_openai_response", "refusal",
    "incomplete_response", "empty_output",
    "dns_failure", "provider_exception", "provider_mismatch", "configuration_failure",
)
COUNTERS = (
    "activations_completed", "cities_founded", "settlers_produced", "attacks_executed",
    "kills", "unit_losses", "damage_dealt", "movement_commands", "combat_commands",
    "commands", "activations_with_no_production_target", "city_activations_without_production_target",
    "city_activations_without_target_with_production", "production_generated_without_target",
    "activations_without_research_target_with_choices", "idle_movable_units",
    "idle_movable_combat_units", "activations_ending_with_movable_combat_units",
    "plans_created", "provider_calls", "plans_reused", "plan_changes", "target_changes",
    "posture_changes", "production_priority_changes", "research_priority_changes",
    "invalidated_plans", "fallback_count",
    "tiles_newly_revealed", "tiles_newly_revealed_by_scouts", "scout_movement_commands",
    "significant_discovery_replans",
    "resource_discoveries_by_scouts", "cities_founded_near_known_resources",
    "known_resources_in_radius_at_founding", "city_center_resources_used",
    "resource_tile_workings", "activations_working_resources",
    "resource_bonus_food", "resource_bonus_production", "resource_bonus_gold",
)


def statistics(values) -> dict:
    values = list(values)
    return dict(samples=len(values), min=min(values) if values else None,
                max=max(values) if values else None, mean=mean(values) if values else None,
                median=median(values) if values else None)


def inference_metrics(traces: list[dict], context_size: int | None) -> dict:
    attempts = [a for trace in traces for a in trace.get("attempts", [])]
    failures = Counter({category: 0 for category in FAILURE_CATEGORIES})
    for attempt in attempts:
        if attempt.get("error_category"):
            failures[attempt["error_category"]] += 1
    failures["heuristic_fallback"] = sum(bool(t["fallback_used"]) for t in traces)
    failures["repair_failed"] = sum(t.get("retry_count", 0) > 0 and t["fallback_used"] for t in traces)
    tokens = {key: statistics(a.get("metrics", {})[key] for a in attempts
                             if key in a.get("metrics", {}))
              for key in ("prompt_eval_count", "eval_count")}
    timings = {"request_wall_clock_seconds": statistics(a["wall_clock_seconds"] for a in attempts
                                                        if "wall_clock_seconds" in a)}
    for raw, normalized in (("total_duration", "ollama_total_seconds"),
                            ("prompt_eval_duration", "prompt_eval_seconds"),
                            ("eval_duration", "generation_seconds")):
        timings[normalized] = statistics(a["metrics"][raw] / 1_000_000_000 for a in attempts
                                        if raw in a.get("metrics", {}))
    maximum = tokens["prompt_eval_count"]["max"]
    # Preserve Ollama counters/timings; cloud usage has its own names and totals.
    cloud_keys = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens")
    cloud_attempts = [a for t in traces if t.get("requested_provider") == "openai"
                      for a in t.get("attempts", [])]
    cloud_usage = {}
    if cloud_attempts:
        for key in cloud_keys:
            values = [a["metrics"][key] for a in cloud_attempts if key in a.get("metrics", {})]
            cloud_usage[key] = dict(statistics(values), total=sum(values) if values else None)
    return dict(requests=len(attempts), retries=sum(t.get("retry_count", 0) for t in traces),
                repair_success_count=sum(t.get("retry_count", 0) > 0 and not t["fallback_used"] for t in traces),
                fallback_count=failures["heuristic_fallback"], failures=dict(failures),
                schema_invalid_responses=failures["schema_validation"],
                malformed_responses=(failures["malformed_ollama_envelope"] + failures["malformed_json_content"]
                                     + failures["malformed_openai_response"]),
                **({"openai_usage": cloud_usage} if cloud_attempts else {}),
                tokens=tokens, timings=timings, context_size=context_size,
                maximum_prompt_tokens=maximum,
                maximum_prompt_context_percent=(100 * maximum / context_size
                                                if maximum is not None and context_size else None),
                request_wall_clock_total_seconds=sum(a.get("wall_clock_seconds", 0) for a in attempts))


class RunMetrics:
    def __init__(self, state, controllers, command_writer):
        from aig.ai.multifront_metrics import MultiFrontMetrics
        self.multifront = MultiFrontMetrics(state)
        from aig.ai.conquest_metrics import ConquestMetrics
        self.conquest = ConquestMetrics(state)
        from aig.ai.barbarian_metrics import BarbarianMetrics
        self.barbarians = BarbarianMetrics(state)
        self.controllers = controllers
        self.command_writer = command_writer
        self.players = {p: Counter({key: 0 for key in COUNTERS}) for p in state.turn_order}
        self.produced = {p: Counter() for p in state.turn_order}
        self.postures = {p: Counter() for p in state.turn_order}
        self.ages = {p: [] for p in state.turn_order}
        self.distances = {p: [] for p in state.turn_order}
        self.founded = []
        self.resources_worked = {p: set() for p in state.players}
        self.first_resource = {p: None for p in state.players}
        self.initial_technologies = {p: set(s.researched_technologies) for p, s in state.players.items()}
        self.activation = 0
        self.pending = None
        self.first_contacts = {p: dict(enemy_city=None, enemy_unit=None) for p in state.players}
        self.replan_visibility = {p: [] for p in state.players}
        self._contacts(state, turn=state.turn, activation=0)

    def _contacts(self, state, *, turn, activation):
        for actor, player in state.players.items():
            if self.first_resource[actor] is None and known_resources(state, actor):
                self.first_resource[actor] = dict(turn=turn, activation=activation)
            for kind, observed in (("enemy_city", bool(player.knowledge.discovered_cities)),
                                   ("enemy_unit", any(not state.is_barbarian(u.owner_id)
                                                      for u in visible_enemy_units(state, actor)))):
                if observed and self.first_contacts[actor][kind] is None:
                    self.first_contacts[actor][kind] = dict(turn=turn, activation=activation)

    def observe(self, phase, state, command):
        self.conquest.observe(phase, state, command, self.activation)
        self.barbarians.observe(phase, state, command, self.activation)
        actor = command.actor_id
        counts = self.players[actor]
        if phase == "before":
            self.pending = dict(turn=state.turn, activation=self.activation,
                                player_activation=counts["activations_completed"], player_id=actor,
                                command=dict(type=type(command).__name__, **asdict(command)), outcome={})
            self.explored_before = {p: set(s.knowledge.explored_positions) for p, s in state.players.items()}
            self.units_before = {u.id: (u.owner_id, u.unit_type.value, u.hp) for u in state.units.values()}
            if isinstance(command, FoundCity):
                center = state.units[command.settler_unit_id].position
                self.founding_resources = [r for r in known_resources(state, actor)
                    if max(abs(r["position"]["x"]-center.x), abs(r["position"]["y"]-center.y)) <= 1]
            if isinstance(command, EndActivation) and not state.is_barbarian(actor):
                self._activation_end(state, actor, self.pending["outcome"])
            return

        self._contacts(state, turn=self.pending["turn"], activation=self.activation)
        revealed = {}
        for player_id, player in state.players.items():
            count = len(player.knowledge.explored_positions - self.explored_before[player_id])
            self.players[player_id]["tiles_newly_revealed"] += count
            revealed[player_id] = count
        scout = isinstance(command, MoveUnit) and self.units_before[command.unit_id][1] == "scout"
        counts["scout_movement_commands"] += scout
        if scout:
            counts["tiles_newly_revealed_by_scouts"] += revealed[actor]
        spawned_scout_sight = set().union(*(vision_positions(state.game_map, u.position, 3)
            for u in state.units.values() if u.id not in self.units_before
            and u.owner_id == actor and u.unit_type is UnitType.SCOUT))
        if spawned_scout_sight:
            counts["tiles_newly_revealed_by_scouts"] += len(spawned_scout_sight &
                (state.players[actor].knowledge.explored_positions - self.explored_before[actor]))
        outcome = self.pending["outcome"]
        outcome["conquest_events"] = self.conquest.last_events
        outcome["barbarian_events"] = self.barbarians.last_events
        outcome["tiles_newly_revealed"] = revealed
        outcome["resource_discoveries"] = {
            p: [r for r in known_resources(state, p)
                if (r["position"]["x"], r["position"]["y"]) not in
                {(v.x, v.y) for v in self.explored_before[p]}] for p in state.players}
        newly_known = state.players[actor].knowledge.explored_positions - self.explored_before[actor]
        scout_discoveries = newly_known if scout else newly_known & spawned_scout_sight
        counts["resource_discoveries_by_scouts"] += sum(
            p in state.tiles and state.tiles[p].resource is not None for p in scout_discoveries)
        counts["commands"] += 1
        counts["movement_commands"] += type(command).__name__ == "MoveUnit"
        if isinstance(command, AttackUnit):
            counts["attacks_executed"] += 1
            counts["combat_commands"] += 1
            damage, deaths = [], []
            for unit_id in (command.attacker_unit_id, command.target_unit_id):
                owner, kind, hp = self.units_before[unit_id]
                survivor = state.units.get(unit_id)
                lost_hp = hp - (survivor.hp if survivor else 0)
                source = (self.units_before[command.target_unit_id][0]
                          if unit_id == command.attacker_unit_id else actor)
                self.players[source]["damage_dealt"] += lost_hp
                damage.append(dict(unit_id=unit_id, source_player_id=source, hp_lost=lost_hp))
                if survivor is None:
                    self.players[owner]["unit_losses"] += 1
                    self.players[source]["kills"] += 1
                    deaths.append(dict(unit_id=unit_id, player_id=owner, type=kind))
            outcome.update(damage=damage, deaths=deaths)
        elif isinstance(command, FoundCity):
            counts["cities_founded"] += 1
            founded = {key: self.pending[key] for key in ("turn", "activation", "player_activation", "player_id")}
            founded["city_id"] = command.city_id
            founded["known_resources_in_radius"] = self.founding_resources
            center_resource = state.tiles[state.cities[command.city_id].position].resource
            founded["center_resource"] = center_resource.value if center_resource else None
            counts["cities_founded_near_known_resources"] += bool(self.founding_resources)
            counts["known_resources_in_radius_at_founding"] += len(self.founding_resources)
            counts["city_center_resources_used"] += center_resource is not None
            self.founded.append(founded)
            outcome["city_founded"] = founded
        elif isinstance(command, EndActivation):
            produced = [dict(unit_id=u.id, player_id=u.owner_id, type=u.unit_type.value)
                        for u in sorted(state.units.values(), key=lambda u: u.id) if u.id not in self.units_before]
            for unit in produced:
                if state.is_barbarian(unit["player_id"]):
                    continue
                self.produced[unit["player_id"]][unit["type"]] += 1
                self.players[unit["player_id"]]["settlers_produced"] += unit["type"] == "settler"
            outcome["units_produced"] = [u for u in produced if not state.is_barbarian(u["player_id"])]
            counts["activations_completed"] += 1
        self.command_writer.write(self.pending)

    def _activation_end(self, state, actor, outcome):
        counts = self.players[actor]
        cities = [c for c in state.cities.values() if c.owner_id == actor]
        # Sample the actual pre-growth assignments that this EndActivation resolves.
        workings = [p for c in cities for p in [c.position, *worked_positions(state, c)]
                    if state.tiles[p].resource is not None]
        bonus = sum((resource_yields(state.tiles[p].resource) for p in workings), Yields())
        self.resources_worked[actor].update(workings)
        counts["resource_tile_workings"] += len(workings)
        counts["activations_working_resources"] += bool(workings)
        for key in ("food", "production", "gold"):
            counts["resource_bonus_" + key] += getattr(bonus, key)
        outcome["resource_bonus_yields"] = asdict(bonus)
        outcome["resource_tiles_worked"] = [asdict(p) for p in workings]
        unset = [c for c in cities if c.production_target is None]
        counts["activations_with_no_production_target"] += bool(unset)
        counts["city_activations_without_production_target"] += len(unset)
        generated = [(c, city_yields(state, c).production) for c in unset]
        counts["city_activations_without_target_with_production"] += sum(
            c.production_stored > 0 or amount > 0 for c, amount in generated)
        counts["production_generated_without_target"] += sum(amount for _, amount in generated)
        player = state.players[actor]
        no_research = player.research_target is None and bool(available_technologies(player))
        counts["activations_without_research_target_with_choices"] += no_research
        units = [u for u in state.units.values() if u.owner_id == actor]
        military = [u for u in units if u.unit_type is not UnitType.SETTLER]
        idle = sorted(u.id for u in units if u.moves_remaining > 0)
        idle_combat = sorted(u.id for u in military if u.moves_remaining > 0)
        counts["idle_movable_units"] += len(idle)
        counts["idle_movable_combat_units"] += len(idle_combat)
        counts["activations_ending_with_movable_combat_units"] += bool(idle_combat)
        target = state.cities.get(self.controllers[actor].previous_plan.target_city_id)
        distances = [max(abs(u.position.x - target.position.x), abs(u.position.y - target.position.y))
                     for u in military] if target else []
        self.distances[actor].extend(distances)
        outcome.update(idle_movable_unit_ids=idle, idle_movable_combat_unit_ids=idle_combat,
                       cities_without_production_target=sorted(c.id for c in unset),
                       no_research_target_with_choices=no_research,
                       combat_target_distances=distances,
                       production_stored_before_economy=sum(c.production_stored for c in cities))

    def record_plan(self, actor, controller):
        self.multifront.record(actor, controller)
        counts = self.players[actor]
        trace = controller.last_trace
        counts["plans_reused"] += trace is None
        self.ages[actor].append(controller.summary["planAgeTurns"])
        self.postures[actor][controller.previous_plan.posture.value] += 1
        if trace is None:
            return
        counts["significant_discovery_replans"] += trace["replan_reason"] in (
            "first_enemy_city_discovered", "first_enemy_military_contact",
            "first_camp_discovered", "first_barbarian_contact")
        view = trace["strategic_state"]
        self.replan_visibility[actor].append(dict(turn=trace["turn"],
            visible_enemy_military_strength=view["visible_enemy_military_strength"],
            nearest_visible_enemy_unit_distance=view["nearest_visible_enemy_unit_distance"],
            known_resource_count=len(view["known_resources"]),
            known_resources_by_type=dict(sorted(Counter(r["type"] for r in view["known_resources"]).items())),
            resources_inside_city_radii=sum(r["inside_own_city_radius"] for r in view["known_resources"]),
            resources_with_no_known_owner=[r for r in view["known_resources"] if r["ownerId"] is None]))
        counts["plans_created"] += 1
        counts["provider_calls"] += 1
        counts["invalidated_plans"] += trace["replan_reason"] == "invalid_target"
        counts["fallback_count"] += trace["fallback_used"]
        old = trace.get("invalidated_previous_plan") or trace["previous_plan"]
        new = trace["resulting_plan"]
        if old is not None:
            counts["plan_changes"] += old != new
            counts["target_changes"] += any(old[f] != new[f] for f in ("primary_enemy_id", "target_city_id"))
            for field in ("posture", "production_priority", "research_priority"):
                counts[field + "_changes"] += old[field] != new[field]

    def finish(self, state):
        players = {}
        for actor, counts in self.players.items():
            if state.is_barbarian(actor):
                continue
            cities = [c for c in state.cities.values() if c.owner_id == actor]
            units = [u for u in state.units.values() if u.owner_id == actor]
            player = state.players[actor]
            players[actor] = dict(counts, final_city_count=len(cities), total_population=sum(c.population for c in cities),
                                 final_gold=player.gold, final_science_stored=player.science_stored,
                                 technologies_researched=sorted(t.value for t in player.researched_technologies),
                                 research_completions=len(player.researched_technologies - self.initial_technologies[actor]),
                                 final_production_stored=sum(c.production_stored for c in cities),
                                 unused_settlers=sum(u.unit_type is UnitType.SETTLER for u in units),
                                 final_military_strength=sum(max(u.unit_type.combat_strength, u.unit_type.ranged_strength or 0)
                                                             * u.hp // 100 for u in units if u.unit_type is not UnitType.SETTLER),
                                 units_remaining_by_type=dict(sorted(Counter(u.unit_type.value for u in units).items())),
                                 units_produced_by_type=dict(sorted(self.produced[actor].items())),
                                 posture_counts=dict(sorted(self.postures[actor].items())))
            players[actor].update(
                resource_tiles_discovered=len(known_resources(state, actor)),
                resource_discoveries_by_type=dict(sorted(Counter(r["type"] for r in known_resources(state, actor)).items())),
                first_resource_discovered=self.first_resource[actor],
                resource_tiles_worked=len(self.resources_worked[actor]),
                explored_tile_count=len(player.knowledge.explored_positions),
                map_explored_percent=100 * len(player.knowledge.explored_positions) /
                    (state.game_map.width * state.game_map.height) if state.game_map.width else 0.0,
                discovered_enemy_city_count=len(player.knowledge.discovered_cities),
                first_contacts=self.first_contacts[actor],
                visibility_at_replans=self.replan_visibility[actor])
            self._averages(players[actor], self.ages[actor], self.distances[actor])
        barbarian_players, barbarian_observer = self.barbarians.finish(state)
        conquest, conquest_players = self.conquest.finish(state)
        fronts = self.multifront.finish()
        for actor in players:
            players[actor].update(fronts[actor])
            players[actor].update(barbarian_players[actor])
            players[actor].update(conquest_players[actor])
        numeric = [k for k, v in next(iter(players.values())).items()
                   if type(v) is int and all(type(p[k]) is int for p in players.values())
                   and k != "first_city_capture_turn"]
        total = {k: sum(p[k] for p in players.values()) for k in numeric}
        total['maximum_simultaneous_visible_enemy_civilizations'] = max(
            p['maximum_simultaneous_visible_enemy_civilizations'] for p in players.values())
        for field in ("units_remaining_by_type", "units_produced_by_type", "posture_counts", "resource_discoveries_by_type"):
            combined = Counter()
            for player in players.values():
                combined.update(player[field])
            total[field] = dict(sorted(combined.items()))
        self._averages(total, [v for values in self.ages.values() for v in values],
                       [v for values in self.distances.values() for v in values])
        total.update(global_turns_completed=state.turn, cities_founded_at=self.founded,
                     technologies_researched={p: m["technologies_researched"] for p, m in players.items()})
        total["world_resource_tiles"] = sum(t.resource is not None for t in state.tiles.values())
        total["barbarian_spawning"] = barbarian_observer
        total.update(conquest)
        total["world_resources_by_type"] = dict(sorted(Counter(t.resource.value for t in state.tiles.values()
                                                             if t.resource is not None).items()))
        return total, players

    @staticmethod
    def _averages(result, ages, distances):
        result["plan_age_turns"] = statistics(ages)
        result["combat_distance_to_target_tiles"] = statistics(distances)
        activations = result["activations_completed"]
        for field in ("commands", "movement_commands", "attacks_executed"):
            result[field + "_per_activation"] = result[field] / activations if activations else None
