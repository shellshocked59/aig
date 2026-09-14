"""Offline Phase 7D forensics. No provider construction, requests, or runner calls.

Run from repository root: .venv/Scripts/python.exe -B scripts/arena-phase7e-forensics.py
Writes only the new Phase 7E directory and documentation; preserves Phase 7D.
"""
import ast
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / '.local/arena-phase7d-stepwise-fullmatch-pilot-20260913-02'
OUT = ROOT / '.local/arena-phase7e-offline-forensics-20260913'

def offline(event, args):
    if event in ('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'):
        raise RuntimeError('Offline analysis prohibits network and child processes')

sys.addaudithook(offline)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'backend'))
from aig.arena.replay import replay, ArenaSimulation
from aig.arena.snapshots import digest, canonical_json, to_snapshot, from_snapshot, state_hash, command_from_dict
from aig.arena.ai.observation import build_observation, OBSERVATION_V2

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def save(p, value):
    p.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(str(x).replace('|', '/') for x in row) + ' |' for row in rows])

def team_state(snapshot):
    return {side: dict(active=sum(u['status'] == 'active' for u in snapshot['units'] if u['owner_id'] == side),
                       downed=sum(u['status'] == 'downed' for u in snapshot['units'] if u['owner_id'] == side),
                       retained=sum(u['owner_id'] == side for u in snapshot['units']),
                       hp=sum(u['hp'] for u in snapshot['units'] if u['owner_id'] == side),
                       core_hp=next(c['hp'] for c in snapshot['cores'] if c['owner_id'] == side))
            for side in ('blue', 'red')}

def short_state(s):
    return '; '.join(f"{side}: {v['active']} active/{v['downed']} downed/{4-v['retained']} removed, HP {v['hp']}, Core {v['core_hp']}" for side, v in s.items())

def main():
    before = read(OUT / 'preservation-before.json')
    historical = read(EVIDENCE / 'evidence-sha256.json')
    assert all(sha(EVIDENCE / p) == h for p, h in historical.items())
    frozen = read(EVIDENCE / 'source-before.json')
    assert all(sha(ROOT / p) == h for p, h in frozen['sourceFiles'].items())
    auxiliary = read(EVIDENCE / 'auxiliary-source-before.json')
    assert all(sha(ROOT / p) == h for p, h in auxiliary.items())
    summary = read(EVIDENCE / 'summary.json')
    manifest = read(EVIDENCE / 'manifest.json')
    analysis = read(EVIDENCE / 'analysis.json')
    tree = ast.parse((ROOT / 'backend/aig/arena/ai/stepwise.py').read_text())
    prompt = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'STEP_PROMPT' for t in n.targets))
    assert hashlib.sha256(prompt.encode()).hexdigest() == manifest['promptHash']
    feedback = ('Previous output failed validation (invalid_reference). Stepwise control requires zero or one action. '
                'Copy one complete action from the current legal_actions catalog, or return actions=[] '
                'to end the turn. Use the same schema. No reasoning or commentary.')
    # Evaluate only the pure feedback method's return expression, never a provider.
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == '_StepContract')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'repair_feedback')
    assert eval(compile(ast.Expression(method.body[0].value), '<feedback>', 'eval'), {'__builtins__': {}}, {'category': 'invalid_reference'}) == feedback
    failures, matches, decisions, mechanics = [], [], [], []
    verified_observations = 0
    for m in summary['matches']:
        mid = m['match_id']; directory = EVIDENCE / mid
        trace = read(directory / 'command-trace.json'); final = read(directory / 'final-snapshot.json')
        sim = replay(trace)
        assert to_snapshot(sim.state) == final
        assert digest(final) == m['verification']['final_state_hash']
        assert digest(trace) == m['verification']['command_trace_hash']
        assert read(directory / 'result.json') == {k: v for k, v in m.items() if k != 'match_id'}
        ds, ms, side_turns, prefix = [], [], Counter(), []
        for ix, turn in enumerate(m['turns'], 1):
            td = directory / 'turns' / f'turn-{ix:04d}'
            assert read(td / 'turn.json') == turn
            part = read(td / 'command-trace.json')
            assert part['initial_snapshot'] == (trace['initial_snapshot'] if ix == 1 else previous_final)
            previous_final = to_snapshot(replay(part).state)
            assert previous_final == read(td / 'final-snapshot.json')
            prefix.extend(part['entries'])
            side = turn['player_id']; provider = m['assignments'][side]; side_turns[side] += 1
            entries = part['entries']
            actions = Counter(e['command']['type'].removeprefix('arena_') for e in entries if e['command']['type'] != 'arena_end_turn')
            mech = dict(match_id=mid, player_turn=ix, side=side, provider=provider, actions=dict(actions),
                        **{k: sum(e[k] for e in entries) for k in ('ap_used', 'damage_dealt', 'core_damage', 'friendly_fire_damage', 'units_finished', 'units_revived')})
            ms.append(mech); mechanics.append(mech)
            local = ArenaSimulation(from_snapshot(part['initial_snapshot'])); cursor = 0
            for step in turn.get('steps', []):
                obs = build_observation(local.state, version=OBSERVATION_V2)
                assert obs.to_dict() == step['observation'] and obs.hash == step['observation_hash']
                verified_observations += 1
                assert step['legal_action_count'] == len(obs.to_dict()['legal_actions'])
                row = dict(match_id=mid, player_turn=ix, side_player_turn=side_turns[side], provider=provider, side=side,
                           step_index=step['step_index'], requests=step['provider_requests'], repairs=step['repair_requests'],
                           initial_invalid=not step['first_response_valid'], success=step['success'], repaired=step['repair_succeeded'],
                           latency=sum(a['wall_clock_seconds'] or 0 for a in step['attempts']))
                ds.append(row); decisions.append(row)
                if step['command_index'] is not None:
                    assert step['command_index'] == cursor
                    assert step['selected_action'] in obs.to_dict()['legal_actions']
                    local.execute(command_from_dict(entries[cursor]['command'])); cursor += 1
                assert state_hash(local.state) == step['resulting_state_hash']
                if not step['success']:
                    assert len(step['attempts']) == 2
                    assert all(a['error_category'] == 'invalid_reference' for a in step['attempts'])
                    assert step['decision'] is None and step['selected_action'] is None
                    assert all('raw_content' not in a for a in step['attempts'])
                    stop = to_snapshot(local.state)
                    f = dict(match_id=mid, provider=provider, model=step['model'], side=side, global_turn=step['turn'],
                             player_turn=ix, side_player_turn=side_turns[side], step_index=step['step_index'], ap=step['ap_before'],
                             observation_hash=obs.hash, state_hash_before_failed_decision=state_hash(local.state),
                             legal_action_count=step['legal_action_count'], observation=obs.to_dict(), stopping_snapshot=stop,
                             team_state=team_state(stop), attempts=step['attempts'],
                             initial_category='invalid_reference', repair_category='invalid_reference',
                             initial_raw=None, initial_parsed=None, repair_raw=None, repair_parsed=None,
                             unavailable_reason='Rejected outputs omitted by safe_inference; no parsed invalid plan persisted.',
                             exact_validator='parse_turn_plan reference branch OR parse_step catalog branch; branch not retained',
                             decisions_including_failure=len(ds), requests_including_failed_pair=sum(d['requests'] for d in ds),
                             repair_feedback_specificity='Generic / under-specified for exact mismatch; explicit catalog remedy present',
                             repair_behavior='Same category; A vs B vs C vs D unknowable without rejected outputs',
                             reconstructed_repair=dict(system_prompt=prompt, messages=[{'role':'user','content':'ArenaObservation:\n'+obs.canonical}, {'role':'user','content':feedback}],
                                                       provenance='Reconstructed from frozen source and retained observation, not retained HTTP payload'),
                             partial_command_trace=str((directory / 'command-trace.json').relative_to(ROOT)),
                             turn_command_trace=str((td / 'command-trace.json').relative_to(ROOT)), replay=m['verification'])
                    failures.append(f)
            assert to_snapshot(replay(part).state) == previous_final
        assert prefix == trace['entries'] and previous_final == final
        for side in ('blue', 'red'):
            for key in ('ap_used', 'damage_dealt', 'core_damage', 'friendly_fire_damage', 'units_finished', 'units_revived'):
                assert sum(x[key] for x in ms if x['side'] == side) == m['mechanical_metrics']['players'][side][key]
        match = dict(match_id=mid, assignments=m['assignments'], status=m['status'], winner=m['winner'],
                     terminal_mechanism=m['terminal_mechanism'], global_turns=m['global_turns'], player_turns=m['player_turns'],
                     decisions=len(ds), requests=sum(d['requests'] for d in ds), repairs=sum(d['repairs'] for d in ds),
                     latency=sum(d['latency'] for d in ds), final_state=team_state(final), terminal_snapshot=final,
                     mechanical_metrics=m['mechanical_metrics'], model_ap=sum(x['ap_used'] for x in ms if x['provider'] != 'heuristic'),
                     mechanics=ms, replay=True)
        matches.append(match)
    assert len(failures) == 6 and len(decisions) == 189
    providers = {}
    for p in ('ollama', 'openai'):
        ds = [d for d in decisions if d['provider'] == p]
        req = sum(d['requests'] for d in ds); invalid = sum(d['initial_invalid'] for d in ds)
        failed = sum(not d['success'] for d in ds); ap = sum(x['ap_used'] for x in mechanics if x['provider'] == p)
        providers[p] = dict(decisions=len(ds), requests=req, initial_invalid=invalid, repair_success=invalid-failed,
                            repair_failure=failed, fatal_rate=failed/len(ds), requests_per_ap=req/ap, ap=ap,
                            latency=sum(d['latency'] for d in ds))
        assert req + 1 == summary['requests'][p]
    assert sum(d['initial_invalid'] for d in decisions) == 16
    assert sum(d['repaired'] for d in decisions) == 10
    survival = {label: {str(n): (1-p)**n for n in (10, 25, 50, 75, 100)} for label, p in
                [('pooled', 6/189), ('Qwen', 3/76), ('Luna', 3/113)]}
    save(OUT / 'failure-ledger.json', failures)
    save(OUT / 'analysis.json', dict(matches=matches, providers=providers, decisions=decisions, survival=survival))
    lines = ['# Arena Phase 7E — stepwise full-match failure forensics', '',
             'Offline analysis of the eight Phase 7D attempts. Recommendation: **Option A, a bounded, side-balanced frozen reliability replication**, subject to separate live authorization. The evidence cannot establish a common actionable repair defect: rejected responses were deliberately omitted, and current feedback already gives the proposed catalog-copy remedy. Do not implement repair V2 or reopen stepwise architecture on these records alone.', '',
             '## 1. Experiment and evidence limits', '',
             'Evidence: [.local Phase 7D report](../.local/arena-phase7d-stepwise-fullmatch-pilot-20260913-02/report.md), summary.json, per-turn observations/telemetry, command traces and snapshots. The actual manifest says **arena-benchmark-v3**, with arena-control-stepwise-v1, arena-step-prompt-v1, arena-observation-v2, arena-turn-plan-schema-v1, arena-probes-v1, qwen-config-v1 and luna-config-v1. The task description names benchmark V2; this report preserves and describes the actual V3 full-match wrapper, without changing either artifact.', '',
             'Provider.last_trace temporarily held sanitized raw_content, but benchmark_provider.safe_inference persists only categories, numeric telemetry and IDs. Failed steps retain decision=null and resulting_plan=null. Neither null means actions=[]. No raw initial/repair decision, invalid parsed object, or exact validator detail exists in these persisted stopping records. No provider logs were queried. The six-entry [failure ledger](../.local/arena-phase7e-offline-forensics-20260913/failure-ledger.json) includes full legal catalogs, observations, telemetry, hashes, reconstructed request content and trace paths; null fields explicitly denote missing evidence.', '',
             '## 2. Eight-match ledger', '',
             table(['Match', 'Blue / Red', 'Result', 'Global / player turns', 'Decisions / requests / repairs', 'Model AP', 'Latency s'],
                   [[m['match_id'], ' / '.join(m['assignments'][s] for s in ('blue','red')), m['status'] + ('; winner '+m['winner'] if m['winner'] else '; repair_failed'),
                     f"{m['global_turns']} / {m['player_turns']}", f"{m['decisions']} / {m['requests']} / {m['repairs']}", m['model_ap'], f"{m['latency']:.3f}"] for m in matches]), '',
             'Global values above are persisted final zero-based round counters, not counts of model turns. Latency is summed transport wall time including repairs, excluding orchestration and preflight. All eight traces replayed exactly again offline. Two historical preflight requests are excluded from the 205 match requests; historical total remains 207. This phase sent zero requests.', '',
             '## 3. Six exact stopping points', '',
             table(['Match', 'Provider / side', 'Decision global round', 'Player turn / side turn', 'Step index (0-based)', 'AP', 'Catalog', 'Initial → repair', 'Decisions / requests through failure'],
                   [[f['match_id'], f"{f['provider']} / {f['side']}",f['global_turn'],f"{f['player_turn']} / {f['side_player_turn']}",f['step_index'],f['ap'],f['legal_action_count'],'invalid_reference → invalid_reference',f"{f['decisions_including_failure']} / {f['requests_including_failed_pair']}"] for f in failures]), '',
             'Side turn counts only the stopping side’s turns; self-play model exposure includes both sides. The stopping decision and its two requests are included. Strictly before that decision, subtract one decision and two requests. Failed decisions execute no action. The controller subsequently records EndTurn before the strict match runner stops, so final/partial snapshots can have a later round counter, next active side and refreshed AP. Stopping hashes below are verified before this housekeeping EndTurn.', '']
    for f in failures:
        lines += [f"### {f['match_id']}", '',
                  f"Observation SHA-256: `{f['observation_hash']}`. State before failed decision: `{f['state_hash_before_failed_decision']}`.", '',
                  short_state(f['team_state']) + '.', '',
                  'Sanitized initial decision: **unavailable**. Sanitized repair decision: **unavailable**. Both rejection categories: `invalid_reference`; exact detail/branch unavailable. Current-catalog validity failed at the overall contract level, but exact membership of an individual returned action cannot be tested. Near-copy status and differing unit_id/target_id/destination/target_position/type are unknown. Exact-error feedback: no; general catalog-copy feedback: yes. Repair behavior: same recorded category, exact repetition unknown.', '',
                  f"The catalog contains {f['legal_action_count']} actions. Copying any one exact entry in a valid plan, or returning a valid empty plan, was an available contract-level remedy. This says nothing about tactical quality or whether the model would follow it. Both response telemetry records and the complete catalog are in the JSON ledger. Partial replay: exact.", '']
    lines += ['## 4. Initial and repair taxonomy; validator order', '',
              'All six stopping initials and all six stopping repairs have the repository category `invalid_reference`. Do not relabel them `action_not_in_current_catalog`, `wrong_actor`, or `invalid_ability`: the branch was not retained. Across all match decisions, all 16 initial invalid responses also have invalid_reference; 10 repairs succeeded and 6 failed with invalid_reference.', '',
              table(['Question (applies to all 12 rejected responses)', 'Evidence-supported answer'], [
                  ['Transport/envelope accepted?', 'Yes, inferred: adapter returned content and application validation reached invalid_reference.'],
                  ['JSON syntactically valid?', 'Yes, inferred from passing strict_json before rejection.'],
                  ['Wire schema?', 'Application structure passed and satisfies the configured wire subset by code inspection; not independently revalidated without raw bytes.'],
                  ['arena-turn-plan-schema-v1?', 'Structural ArenaTurnPlan.from_dict passed; static/reference and stepwise acceptance did not.'],
                  ['0, 1 or >1 actions?', 'At least one. With AP=1, exactly one. Otherwise 1..AP (bounded by five); exact count unavailable.'],
                  ['Current catalog membership?', 'No valid step was accepted. If exactly one action, it cannot be an exact legal entry; which entry/field failed is unknown.'],
                  ['Actor and target valid?', 'Unknown: rejection could be own-unit ID, target ID/team/Core restriction, or later catalog membership.'],
                  ['AP sufficient?', 'Yes for the declared total action cost: current-AP check precedes every invalid_reference branch.'],
                  ['Exact validator?', 'parse_turn_plan static-reference branches OR parse_step catalog-membership branch. No exception detail retained.']]), '',
              'Order: strict JSON → structural plan (including ≤5 actions/≤5 AP) → current AP budget → actor/ability/target/board reference checks → stepwise ≤1 action → exact canonical catalog membership. Thus an invalid-reference error can precede the too-many-actions check. **Zero confirmed 2+ action origins; four of six stopping decisions remain potentially multi-action; the two AP=1 Qwen self-play stops are necessarily single-action.** This is not evidence that 0/6 actually returned multiple actions. No known malformed JSON, envelope failure, AP-budget rejection or invalid_ability at these stopping pairs. A later hidden issue cannot be excluded.', '',
              'A/B/C/D repair behavior cannot be separated: the same action may repeat, a different action may fail the same category, or one reference issue may be fixed while another causes the same category. E (malformed repair) is inconsistent with the recorded validator path. Use F/indeterminate if forced to choose a ledger label. Same-category recurrence is 6/6; exact repeated-invalid-decision rate is unknown.', '',
              '## 5. Repair prompt audit', '',
              'The following feedback is reconstructed exactly from the frozen stepwise source, checked against its pure return expression. It is identical for all six stopping pairs:', '', '```text', feedback, '```', '',
              'Every repair uses the original observation user message plus this second user message, with the same system prompt and wire schema. Ollama prepends the system message; Luna supplies it as Responses instructions. There is no assistant message containing the rejected output. Exact HTTP payload bytes were not saved; the ledger therefore labels reconstructed content explicitly.', '',
              table(['Feedback item', 'Present?'], [
                  ['Validation category', 'Yes: invalid_reference'], ['Action index', 'No'], ['Attempted actor ID/class', 'No; possible actors/classes exist in observation'],
                  ['Attempted action/target', 'No'], ['Exact membership mismatch', 'No'], ['Current AP', 'Yes, in original observation resent'],
                  ['Allowed action count', 'Yes, zero or one'], ['Current Observation V2 and full legal catalog', 'Yes, same observation resent'],
                  ['Original invalid output', 'No']]), '',
              '**Classification for each pair: GENERIC / UNDER-SPECIFIED about the exact failing object or field, but already specific about the required remedy.** It is inaccurate to describe current repair feedback as only the word invalid_reference. The suggested simplified catalog-copy instruction is already substantially present. Missing raw outputs prevent attributing failures to ignored useful feedback versus a particular confusing mismatch.', '',
              '## 6. Provider patterns and timing', '',
              'Qwen: 3 failed matches, all initial/repair invalid_reference, 3/3 same-category recurrence, exact-repeat rate unknown. Its two self-play trajectories and stopping observation/state hashes coincide; equal generated token counts do not prove equal rejected text. Luna: 3 failed matches, same categories and 3/3 category recurrence, exact-repeat rate unknown. Unlike Qwen, Luna recovered 10/13 initial-invalid decisions. Same coarse category does not prove the same underlying cause. These tiny, state-dependent samples are descriptive.', '',
              'Mechanical timing labels, defined only for this report: early = 0–2 completed global rounds at decision; mid = 3–5; late = ≥6. These are elapsed-round bins, not estimates of how close a battle was to ending. Counts: ' + str(dict(Counter('early' if f['global_turn'] <= 2 else 'mid' if f['global_turn'] <= 5 else 'late' for f in failures))) + '. Stopping unit counts, Core HP, AP, step and catalog sizes are above; all Core HP values are 30/30.', '',
              '## 7. Compound reliability', '',
              table(['Provider', 'Decisions', 'Initial invalid', 'Repair failure / attempted', 'Eventual decision failure', 'Requests / AP', 'Total latency s'],
                    [[p, v['decisions'],f"{v['initial_invalid']}/{v['decisions']} ({100*v['initial_invalid']/v['decisions']:.2f}%)",f"{v['repair_failure']}/{v['initial_invalid']} ({100*v['repair_failure']/v['initial_invalid']:.2f}%)",f"{100*v['fatal_rate']:.2f}%",f"{v['requests_per_ap']:.3f}",f"{v['latency']:.3f}"] for p,v in providers.items()]), '',
              'Pooled: 189 model decisions = 173 first-response valid + 16 initial invalid. Repairs: 10 successful + 6 failed. First-response invalid rate 16/189 = 8.47%; conditional repair failure 6/16 = 37.50%; eventual fatal decision rate 6/189 = 3.17%; eventual accepted decision rate 183/189 = 96.83%. Accepted includes 11 empty EndTurn decisions; 172 selected actions were current-catalog valid and executed. There were zero execution defects and zero heuristic fallback contamination.', '',
              'Completed matches consumed 35 model decisions and 35 requests; failed matches consumed 154 decisions and 170 requests. Individual counts through failure are 25, 25, 25, 53, 6 and 20 in schedule order. These are observed censored exposures, not required full-match lengths.', '',
              'For illustration only, assume constant independent fatal probability p and survival S(N)=(1-p)^N. N counts model decisions, not repairs or heuristic turns. Using pooled p=6/189:', '',
              table(['Model', '10 decisions', '25', '50', '75', '100'], [[p]+[f"{100*values[str(n)]:.1f}%" for n in (10,25,50,75,100)] for p,values in survival.items()]), '',
              'Independence and a stationary hazard are not established. Matches share starting states, Qwen self-play duplicates a trajectory, providers differ, and bad states can cluster failures. Do not fit a win-rate claim or extrapolate confidence from these eight attempts. Phase 7C’s 100% Qwen / 98.86% Luna first-response validity and 56/56 completed probe turns concern shorter selected state exposures. The full-match first-response rates are 96.05% and 88.50%, on different trajectories; this distribution shift and compounded exposure explain why reliable probes can coexist with six failed matches. No statistical contradiction follows.', '',
              '## 8. Completed Qwen and Luna mechanics', '']
    for m in matches:
        if m['status'] != 'completed':
            continue
        p = next(x for x in m['assignments'].values() if x != 'heuristic')
        model = 'Qwen' if p == 'ollama' else 'Luna'
        rows = [x for x in m['mechanics'] if x['provider'] == p]
        totals = Counter()
        for row in rows: totals.update(row['actions'])
        lines += [f"### {model}: {m['match_id']}", '',
                  f"{m['player_turns']} recorded player turns; final global counter {m['global_turns']}; {len(rows)} {model}-controlled turns. Winner {m['winner']} by {m['terminal_mechanism']}. AP per model turn: {[x['ap_used'] for x in rows]}; mean {sum(x['ap_used'] for x in rows)/len(rows):.2f}.", '',
                  'Action distribution (executed): `' + json.dumps(dict(totals),sort_keys=True) + '`.', '',
                  f"Unit damage {sum(x['damage_dealt']-x['core_damage'] for x in rows)}, including friendly damage {sum(x['friendly_fire_damage'] for x in rows)}; Core damage {sum(x['core_damage'] for x in rows)}. Finish {totals['finish']}; Revive {totals['revive']}; Fireball {totals['fireball']}; Shield Bash {totals['shield_bash']}; Snipe {totals['snipe']}. Both sides' full metrics and terminal snapshot are in derived analysis.json.", '',
                  'Terminal state: ' + short_state(m['final_state']) + '.', '']
        seqs = [s for s in analysis['representative_sequences'] if s['match_id']==m['match_id'] and s['provider']==p]
        for s in sorted(seqs,key=lambda s:s['player_turn'],reverse=True)[:2]:
            lines += [f"Player turn {s['player_turn']}, {s['ap']} AP: `{json.dumps(s['actions'],sort_keys=True)}`.", '']
        lines += [('Full-turn Qwen baseline: 22 accepted plans executed 0 AP. This completed stepwise match demonstrates fresh-decision multi-action execution and meaningful combat despite losing. The interface/observation/control changed together, so this is not an isolated causal effect.' if p=='ollama' else
                   'Frozen full-turn Luna lost all four heuristic matches. This one completed stepwise win is positive mechanical evidence, not evidence of superior stable strength: the other side-swapped attempt failed and cannot be discarded from the denominator.'), '']
    lines += ['## 9. Partial self-play', '']
    for m in matches[:4]:
        lines += [f"### {m['match_id']}", '', f"Stopped after {m['player_turns']} recorded player turns, {m['decisions']} model decisions, {m['requests']} requests ({m['repairs']} repairs). No winner. Final prefix: {short_state(m['final_state'])}.", '',
                  table(['Side','AP','Unit damage (incl. friendly)','Friendly damage','Core damage'],
                        [[s, v['ap_used'],v['damage_dealt']-v['core_damage'],v['friendly_fire_damage'],v['core_damage']] for s,v in m['mechanical_metrics']['players'].items()]), '',
                  f"Blue-minus-red mechanical differences: active units {m['final_state']['blue']['active']-m['final_state']['red']['active']}; retained unit HP {m['final_state']['blue']['hp']-m['final_state']['red']['hp']}; Core HP 0. These measure only material at stop, not position, initiative, future tactical advantage or who would have won.", '']
    lines += ['## 10. Request and latency implications', '',
              table(['Match', 'Requests / executed model AP', 'Latency through final prefix s'],
                    [[m['match_id'], f"{m['requests']}/{m['model_ap']} = {m['requests']/m['model_ap']:.3f}", f"{m['latency']:.3f}"] for m in matches]), '',
              'The match ledger reports all requests, repairs and latency through each stop. Requests strictly before the terminal invalid decision exclude its two attempts; latency for that pair is separately retained in failure-ledger.json. Qwen consumed 59 requests over its three failed matches and 20 in its completed match; Luna 111 and 15 respectively. Match-request cost per executed AP: Qwen 79/78=1.013; Luna 126/168=0.750. Lower requests/AP partly reflects two-AP actions and is not a tactical-quality score.', '',
              'No dollar cost is inferred. Luna’s historical match telemetry records 292,433 input tokens, 5,486 output and 55,682 cached input. Qwen records 163,513 prompt tokens and 2,883 generated tokens. Latency sums exclude local overhead and the two historical preflights. Failed-prefix means underestimate the work required if longer matches begin surviving.', '',
              '## 11. Terminology', '',
              table(['Term','Recommended report meaning'], [
                  ['Transport-valid','Adapter accepted response envelope/content; not game legality.'],
                  ['Schema-valid','JSON and wire/application structure accepted; specify which layer.'],
                  ['Statically valid','parse_turn_plan returned, including AP and reference checks.'],
                  ['Current-catalog valid','Exactly one action matches current catalog; empty valid decisions reported separately.'],
                  ['Executed','Authoritative command applied and appears in replay trace.'],
                  ['Repaired','Initially invalid decision subsequently accepted after the single repair; report action or EndTurn.'],
                  ['Failed decision','No accepted decision after allowed request(s).'],
                  ['Failed match','Strict runner stopped without gameplay winner; not a team-elimination loss.']]), '',
              'Historical first_valid in the stepwise analysis means accepted first response after the full step validator, not merely parseable JSON. plan_valid is a boundary result, not an independent wire-schema test. Legal/selected denominators exclude rejected outputs, so 100% selected-action legality is compatible with frequent initial invalid decisions. Always retain initial-invalid, repaired-success and repaired-failure counts separately. Do not rewrite historical reports.', '',
              '## 12. Cause assessment and options', '',
              'Model output reliability is the observed bottleneck. A repair-feedback weakness is plausible because exact errors and rejected outputs are absent, but a specific failure mechanism is unproven. Contract layering is real: the full-turn wire schema allows up to five actions while the stepwise prompt/parser requires at most one; these records do not establish multi-action violations as the cause. Diagnostic category conflation and discarded rejected output limit attribution. No authoritative execution, replay, observation mismatch or fallback defect was found. Do not call this an implementation defect merely because the diagnostics are coarse.', '',
              table(['Option','Information gained','Tradeoff / conclusion'], [
                  ['A — frozen replication','Estimates end-to-end completion and both reliability layers without changing contract.','More failures may consume requests; identical Qwen paths reduce new information. Preferred bounded next run.'],
                  ['B — repair-feedback V2 A/B','Tests whether factual mismatch plus rejected decision improves conditional recovery.','Existing remedy already says copy catalog; cannot select a targeted change from missing raw outputs. Would change provider reliability contract and requires separate design/authorization.'],
                  ['C — invalid decision ends turn, battle continues; no repair','Measures tactics under recoverable decision faults and avoids whole-match censoring.','Changes benchmark/control semantics and unused-AP penalty; no longer strict reliability. Separate policy/version required. Not recommended next.']]), '',
              '## 13. Recommended next experiment (design only)', '',
              'Choose **A as a bounded replication**, not an automatic large expansion. Proposed schedule: four model-vs-heuristic attempts per provider, two per side, alternating side order; eight intended attempts total, no replacement or retry, no self-play and no Qwen-vs-Luna. Preserve the actual V3 runner and every frozen model/prompt/schema/observation/repair/game contract. Use a new output directory and retain failed, unstarted and ceiling-stopped slots distinctly. Proposed ceiling: 400 requests/provider including preflight and repairs, 800 combined, subject to separate authorization. No authorization is implied here.', '',
              'Primary outcomes: initial-invalid/initial decisions, repaired-success/initial-invalid, repaired-failure/initial-invalid, fatal decisions/initial decisions, and completed/intended matches. Secondary: decisions to first failure, failure category, per-side completion, executed AP, requests/AP, summed transport latency and terminal mechanism. Fixed schedule; no optional stopping for a favorable win. Integrity failures retain hard-stop rules. Report repeated deterministic paths as replication with limited state diversity, not independent samples.', '',
              'Pilot model-vs-heuristic totals suggest a rough eight-attempt workload of 54 Qwen + 74 Luna = 128 match requests and about 128.4 + 120.0 = 248.3 transport seconds, before preflight/overhead; this doubles the two-attempt matchup observations and is not a ceiling forecast. Improved survival could increase exposure sharply. Keep request ceilings binding rather than promising completion.', '',
              'Why not B now: the user’s proposed simple instruction is already present; missing outputs prevent showing one shared correctable error or an exact repetition pattern. A is less assumption-dependent for the next reliability estimate. Its limitation remains: unchanged telemetry will not recover the missing forensic detail. If mechanistic repair research becomes the priority, separately authorize an evidence-retention design before a repair A/B; do not quietly modify the frozen replication.', '',
              'If B is subsequently selected, reserve **arena-step-repair-v1** for the current feedback and **arena-step-repair-v2** for a specified richer factual representation. These are proposed labels only, not existing manifest versions or implemented changes. Keep initial request byte-equivalent, use one repair in each arm and the same state/schema/model settings; preserve every initial-invalid event. Compare conditional repair recovery on a separately retained, sanitized fixed set of invalid-decision/observation pairs before full-match follow-up. Do not cherry-pick rescued cases or erase first-response failures. A benchmark provenance revision may be needed to record repair version; no such revision is made here.', '',
              '## 14. Offline verification and artifacts', '',
              f"Verified {len(historical)} Phase 7D files against its original SHA-256 inventory; checked {len(frozen['sourceFiles'])} frozen backend/source files against Phase 7D; reproduced all 8 full/partial traces and every turn boundary; rebuilt and hash-checked {verified_observations} current observations; reconciled command metrics, decisions and request ceilings. Step prompt hash remains `{manifest['promptHash']}`. Provider/model profile artifacts, benchmark/probe artifacts and all historical observations remain covered by byte hashes. Existing user changes were preserved.", '',
              'The analysis script installs an audit hook rejecting network connections/DNS and child-process launches; it imports domain replay and observation code only, never constructs providers or runs a benchmark. Zero live inference, probes, preflights, repairs or connectivity requests occurred. Command replay is offline verification, not a new full-match run. No full test suite was run because runtime packages were not edited.', '',
              'Code evidence: [stepwise parser and repair feedback](../backend/aig/arena/ai/stepwise.py), [static validator](../backend/aig/arena/ai/validation.py), [repair message construction](../backend/aig/arena/ai/provider.py), [persistence filter](../backend/aig/arena/benchmark_provider.py), [wire/application schema](../backend/aig/arena/ai/contracts.py), [Ollama adapter](../backend/aig/arena/ai/ollama.py), [Luna adapter](../backend/aig/arena/ai/openai.py). Historical comparisons: [Phase 7C](arena-stepwise-expanded-results.md) and [Phase 5](../.local/arena-phase5-fullmatches-20260913-01/report.md).', '',
              'Created: this document; `scripts/arena-phase7e-forensics.py`; `.local/arena-phase7e-offline-forensics-20260913/{preservation-before.json,failure-ledger.json,analysis.json,verification.json}`. verification.json records preservation counts and checks. The next experiment is neither implemented nor run.', '']
    (ROOT / 'docs/arena-stepwise-fullmatch-failure-analysis.md').write_text('\n'.join(lines), encoding='utf-8')
    changed = [p for p,h in before.items() if not (ROOT/p).is_file() or sha(ROOT/p) != h]
    assert not changed, changed
    assert all(sha(EVIDENCE / p) == h for p,h in historical.items())
    save(OUT / 'verification.json', dict(historical_files_verified=len(historical), preexisting_files_unchanged=len(before),
         source_files_verified=len(frozen['sourceFiles']), auxiliary_files_verified=len(auxiliary), replayed_matches=8, rebuilt_observations=verified_observations,
         prompt_hash=manifest['promptHash'], historical_evidence_byte_identical=True, runtime_unchanged=True,
         live_inference_requests=0, network_and_subprocess_audit_guard=True, decisions=189, match_requests=205,
         initial_invalid=16, repaired_success=10, repaired_failure=6))
    print(json.dumps(dict(failures=[{k:f[k] for k in ('match_id','global_turn','player_turn','side_player_turn','step_index','ap','legal_action_count')} for f in failures], providers=providers, verification=read(OUT/'verification.json')), indent=2))

if __name__ == '__main__':
    main()
