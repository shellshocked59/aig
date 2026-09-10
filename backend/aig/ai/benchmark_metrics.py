"""Read-only command observations and descriptive benchmark statistics."""

from collections import Counter
from dataclasses import asdict
from statistics import mean, median

from aig.commands import AttackUnit, EndActivation, FoundCity
from aig.economy import city_yields
from aig.research import available_technologies
from aig.state import UnitType


FAILURE_CATEGORIES = (
    "transport_failure", "timeout", "non_2xx", "malformed_ollama_envelope",
    "malformed_json_content", "schema_validation", "invalid_strategic_references",
    "repair_failed", "heuristic_fallback",
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
    return dict(requests=len(attempts), retries=sum(t.get("retry_count", 0) for t in traces),
                repair_success_count=sum(t.get("retry_count", 0) > 0 and not t["fallback_used"] for t in traces),
                fallback_count=failures["heuristic_fallback"], failures=dict(failures),
                schema_invalid_responses=failures["schema_validation"],
                malformed_responses=failures["malformed_ollama_envelope"] + failures["malformed_json_content"],
                tokens=tokens, timings=timings, context_size=context_size,
                maximum_prompt_tokens=maximum,
                maximum_prompt_context_percent=(100 * maximum / context_size
                                                if maximum is not None and context_size else None),
                request_wall_clock_total_seconds=sum(a.get("wall_clock_seconds", 0) for a in attempts))


class RunMetrics:
    def __init__(self, state, controllers, command_writer):
        self.controllers = controllers
        self.command_writer = command_writer
        self.players = {p: Counter({key: 0 for key in COUNTERS}) for p in state.turn_order}
        self.produced = {p: Counter() for p in state.turn_order}
        self.postures = {p: Counter() for p in state.turn_order}
        self.ages = {p: [] for p in state.turn_order}
        self.distances = {p: [] for p in state.turn_order}
        self.founded = []
        self.initial_technologies = {p: set(s.researched_technologies) for p, s in state.players.items()}
        self.activation = 0
        self.pending = None

    def observe(self, phase, state, command):
        actor = command.actor_id
        counts = self.players[actor]
        if phase == "before":
            self.pending = dict(turn=state.turn, activation=self.activation,
                                player_activation=counts["activations_completed"], player_id=actor,
                                command=dict(type=type(command).__name__, **asdict(command)), outcome={})
            self.units_before = {u.id: (u.owner_id, u.unit_type.value, u.hp) for u in state.units.values()}
            if isinstance(command, EndActivation):
                self._activation_end(state, actor, self.pending["outcome"])
            return

        outcome = self.pending["outcome"]
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
            self.founded.append(founded)
            outcome["city_founded"] = founded
        elif isinstance(command, EndActivation):
            produced = [dict(unit_id=u.id, player_id=u.owner_id, type=u.unit_type.value)
                        for u in sorted(state.units.values(), key=lambda u: u.id) if u.id not in self.units_before]
            for unit in produced:
                self.produced[unit["player_id"]][unit["type"]] += 1
                self.players[unit["player_id"]]["settlers_produced"] += unit["type"] == "settler"
            outcome["units_produced"] = produced
            counts["activations_completed"] += 1
        self.command_writer.write(self.pending)

    def _activation_end(self, state, actor, outcome):
        counts = self.players[actor]
        cities = [c for c in state.cities.values() if c.owner_id == actor]
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
        counts = self.players[actor]
        trace = controller.last_trace
        counts["plans_reused"] += trace is None
        self.ages[actor].append(controller.summary["planAgeTurns"])
        self.postures[actor][controller.previous_plan.posture.value] += 1
        if trace is None:
            return
        counts["plans_created"] += 1
        counts["provider_calls"] += 1
        counts["invalidated_plans"] += trace["replan_reason"] == "invalid_target"
        counts["fallback_count"] += trace["fallback_used"]
        old, new = trace["previous_plan"], trace["resulting_plan"]
        if old is not None:
            counts["plan_changes"] += old != new
            counts["target_changes"] += any(old[f] != new[f] for f in ("primary_enemy_id", "target_city_id"))
            for field in ("posture", "production_priority", "research_priority"):
                counts[field + "_changes"] += old[field] != new[field]

    def finish(self, state):
        players = {}
        for actor, counts in self.players.items():
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
            self._averages(players[actor], self.ages[actor], self.distances[actor])
        numeric = [k for k, v in next(iter(players.values())).items() if type(v) is int]
        total = {k: sum(p[k] for p in players.values()) for k in numeric}
        for field in ("units_remaining_by_type", "units_produced_by_type", "posture_counts"):
            combined = Counter()
            for player in players.values():
                combined.update(player[field])
            total[field] = dict(sorted(combined.items()))
        self._averages(total, [v for values in self.ages.values() for v in values],
                       [v for values in self.distances.values() for v in values])
        total.update(global_turns_completed=state.turn, cities_founded_at=self.founded,
                     technologies_researched={p: m["technologies_researched"] for p, m in players.items()})
        return total, players

    @staticmethod
    def _averages(result, ages, distances):
        result["plan_age_turns"] = statistics(ages)
        result["combat_distance_to_target_tiles"] = statistics(distances)
        activations = result["activations_completed"]
        for field in ("commands", "movement_commands", "attacks_executed"):
            result[field + "_per_activation"] = result[field] / activations if activations else None
