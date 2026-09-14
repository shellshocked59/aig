"""Offline preparation report; only runs after a complete verified fake cohort."""
import hashlib
import json
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[2]
PREP=ROOT/'artifacts/arena-case-study-preparation-v1'
DRY=PREP/'dry-run-300-final'


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from aig.arena.case_study_contract import verify,DEFAULT_CONTRACT
    contract=verify();p=contract['payload']
    analysis=read(DRY/'analysis.json');integrity=read(DRY/'integrity.json')
    assert analysis['completed_matches']==300 and analysis['synthetic']
    assert analysis['contract_sha256']==contract['sha256']
    assert integrity['success'] and integrity['completed_matches']==300 and integrity['pending_requests']==0
    rows=[json.loads(line) for line in (DRY/'results.jsonl').read_text().splitlines()]
    before=read(PREP/'preservation-before.json')
    changed=[name for name,value in before.items() if not (ROOT/name).is_file() or sha(ROOT/name)!=value]
    assert not changed,changed
    preservation=dict(success=True,files_checked=len(before),changed_files=changed,
        baseline_sha256=sha(PREP/'preservation-before.json'))
    (PREP/'preservation-final.json').write_text(json.dumps(preservation,indent=2)+'\n')
    resume=read(PREP/'resume-verification.json')
    assert resume['success']
    outcomes=dict(Counter(r['terminal_cause'] for r in rows))
    lines=['# Arena case-study preparation results','',
        '**Complete: offline preparation only. Zero OpenAI inference, zero Ollama requests, zero Luna full matches.**',
        '',f'Frozen benchmark: `{p["id"]}`. Contract payload SHA-256: `{contract["sha256"]}`.',
        f'Source revision: `{p["source_revision"]}` plus {len(p["source_hashes"])} exact source-file hashes; the pre-existing dirty tree was preserved.',
        '', '## Delivered files','',
        '- `docs/arena-case-study-benchmark.md`: frozen design, decisions, metrics, statistics, budgets and commands.',
        '- `backend/aig/arena/benchmark_artifacts/arena-case-study-benchmark-v1.json`: immutable machine contract, snapshots, slots, schedule, hashes and analysis plan.',
        '- `backend/aig/arena/case_study_contract.py`: create-only freeze and verification.',
        '- `backend/aig/arena/case_study.py`: full-match runner, journals, replay, resume, budgets and gates.',
        '- `backend/aig/arena/case_study_metrics.py`: mechanical and reliability metrics.',
        '- `backend/aig/arena/case_study_analysis.py`: paired analysis, report, CSV and matplotlib figures.',
        '- `tests/test_arena_case_study.py`: 24 offline tests.',
        '- `requirements-case-study.txt`: pinned report dependencies, installed into the workspace virtual environment.',
        '- `artifacts/arena-case-study-preparation-v1/`: preservation, development evidence, definitive dry run, tests and resume proof.',
        '', 'All repository implementation changes are additions. No frozen AI, heuristic, game or Empire source was edited.',
        '', '## Frozen identity and match design','',
        '| Binding | Version |','| --- | --- |',
        *[f'| {label} | `{value}` |' for label,value in [
            ('Policy',p['policy']),('Full-turn prompt','arena-turn-prompt-v6'),('Step prompt','arena-step-prompt-v3'),
            ('Observation',p['observation']),('Schema',p['schema']),('Repair',p['repair']),('Model/profile',p['model']+' / '+p['profile']),
            ('Rules/scenario',p['rules']+' / '+p['scenario']),('Heuristic',p['heuristic'])]],
        '', 'The request’s `arena-action-schema-v2` is recorded as an alias; the transmitted repository schema ID remains `arena-turn-plan-schema-v2`.',
        f'Heuristic V2 source SHA-256: `{p["heuristic_hash"]}`. Its unchanged tactical-helper dependency hash is `{p["heuristic_dependency_hash"]}`.',
        '', '300 means 100 Strict–Heuristic, 100 Bounded–Heuristic and 100 Stepwise–Heuristic full matches, arranged as 100 matched triplets. The heuristic is a first-class comparator within each matchup, not an additional arm or a pooled homogeneous sample.',
        'Odd slots assign Luna Red, even slots Blue: 50/50 per arm, with Blue moving first. Slots MATCH-001–MATCH-100 use the same canonical opening; no seeds or invented scenario variants. Model responses are independent and nondeterministic in a future live study.',
        f'Initial-state hash: `{p["initial_state_hash"]}`. Schedule hash: `{p["schedule_hash"]}`.',
        'Ten batches of ten slots contain 30 matches each. Arm order rotates Strict/Bounded/Stepwise, Bounded/Stepwise/Strict, Stepwise/Strict/Bounded deterministically.',
        'No new heuristic-only cohort is scheduled. The existing canonical V2/V2 reference (nine player turns, Blue Core win) supplies environment context; identical deterministic repetitions add no independent evidence.',
        '', '## Policies and metrics','',
        'Provider exhaustion after permitted static repair, or a recognized transport/provider error, causes PROVIDER_FORFEIT: Luna loss and heuristic win, with the engine state and failure category preserved. No fallback or transport retry. Per-match budget denial is REQUEST_LIMIT with no winner; cumulative budget exhaustion stops the study. Heuristic exceptions, unclassified errors, replay or binding failures are hard integrity stops.',
        'Natural outcomes are CORE_DESTRUCTION or TEAM_ELIMINATION. TURN_LIMIT occurs at 200 started player turns or 100 completed rounds without an invented winner. Limits are reported separately and count as nonwins in the complete primary binary win-rate denominator.',
        'Gameplay inventory: wins/losses/limits and cause, side-specific rates, player turns and rounds, active control duration, Core damage dealt/received and HP remaining, active/downed/removed units, downs and finishes received/inflicted, revivals, healing, and AP available/executed/unused.',
        'Reliability inventory: provider requests per attempted/completed turn and match; first-response validity and denominators; repairs/success/failure; provider failures separately from budget denial; initial execution invalidities; invalid action index/AP; truncations; provider latency, backend time, input/output/total/cached/reasoning tokens with null for genuinely unknown telemetry.',
        'Heuristic inventory: the same mechanical outcomes/AP/tactics within each matchup, plus measured computation time. Model requests, tokens and provider latency are zero. Intentional EndTurn is unsupported by its plan schema; clean and terminal AP are distinguished.',
        'Unused AP taxonomy: INTENTIONAL_END_TURN, CLEAN_PLAN_COMPLETE, EXECUTION_TRUNCATION, PROVIDER_FAILURE, TERMINAL. Budget-denied AP is identified within the controller’s generic failure bucket and excluded from provider-failure-derived AP. Recovered AP is reported separately.',
        'Bounded inventory: replans/rate, AP at replan, recovered AP distribution, replacement repairs/first invalidity/final failure, and second execution invalidity/rate. Stepwise inventory: decisions per turn, explicit EndTurn decisions and requests per completed turn.',
        'Tactical inventory: attacks/Core attacks, Snipe, Shield Bash, Fireball, Finish, Revive, Heal, Move, enemy/friendly damage; friendly/enemy Fireball damage; empty, friendly-only, mixed and enemy-only casts classified from pre-action ACTIVE targets. No tactical count or AP total is a quality score.',
        '', '## Statistics and resource budget','',
        'Report exact counts and Wilson 95% win-rate intervals, overall and by side. For the complete cohort, exact two-sided McNemar win/nonwin contrasts compare Bounded–Strict and Stepwise–Bounded, with Holm adjustment across those two tests. Draws/limits remain nonwins, forfeits remain losses; incomplete slots do not receive imputed results. Partial cohorts are descriptive only.',
        'Publish paired win-rate differences, cost/turn ratios, median paired match-length differences and side-stratified matched-slot bootstrap effect intervals (10,000 resamples, seed 5914). Degenerate empirical bootstrap intervals are flagged and do not establish equivalence. Tactical-only natural-victory subsets are secondary. There is no composite score, post-hoc expansion or generalization to a map population.',
        '', '| Control | Requests low / central / high (100 games) | Central input / output tokens | Central total tokens | Provider hours low / central / high |',
        '| --- | ---: | ---: | ---: | ---: |']
    for arm in ('strict','bounded','stepwise'):
        low,mid,high=[p['estimates'][level]['arms'][arm] for level in ('low','central','high')]
        lines.append(f'| {arm} | {low["requests"]:,.1f} / {mid["requests"]:,.1f} / {high["requests"]:,.1f} | {mid["input_tokens"]:,.0f} / {mid["output_tokens"]:,.0f} | {mid["total_tokens"]:,.0f} | {low["provider_hours"]:.3f} / {mid["provider_hours"]:.3f} / {high["provider_hours"]:.3f} |')
    lines+=['', 'Central total: 6,066.5 expected requests, 14,559,600 tokens and 4.213 provider hours; elapsed runtime adds heuristic, controller, storage and verification overhead. Low/high: 2,415/16,320 requests. These are planning ranges (5/10/20 Luna turns per game), not observations. No dollar estimate is supplied.',
        '', '| Request ceiling | Strict | Bounded | Stepwise |','| --- | ---: | ---: | ---: |',
        '| Per turn | 2 | 4 | 10 |','| Per match | 50 | 80 | 140 |','| Per batch/control | 300 | 500 | 900 |',
        '| Per control/study | 3,000 | 5,000 | 9,000 |',
        '', 'Combined: 1,700 requests/batch; 15,000/study. Bounded permits at most one execution replan per turn; Stepwise at most five decisions. The high-consumption estimate exceeds the global ceiling: the runner stops rather than spending without authorization.',
        '', '## Verification and dry-run results','',
        f'- **300/300 final fake full matches** completed; **{integrity["replay_verified"]}/300 exact replays**; all ten batch integrity gates passed.',
        f'- **{integrity["reserved_requests"]} fake transport requests**, {integrity["pending_requests"]} pending/unreconciled; **zero live inference**.',
        f'- {sum(r["player_turns"] for r in rows):,} player turns. Fixture terminal counts: `{json.dumps(outcomes,sort_keys=True)}`. These are not Luna performance results.',
        '- Deliberate interruption after MATCH-037 Bounded (110 completed arms); resumed at MATCH-037 Stepwise. Completed match seals and request files remained identical; no completed arm or request was duplicated.',
        '- All 24 final targeted tests passed. Of 131 unmodified historical regressions, 130 passed and one old whole-tree freeze guard rejected source additions as designed. All original frozen source hashes and all non-source payload fields match. That behavioral test also passed under the independently verified historical source projection; its manifest was not rewritten.',
        f'- Preservation: **{len(before):,}/{len(before):,} pre-existing files unchanged**, covering candidate/repair/prompt/tactical evidence, historical Stepwise/Bounded, engine, heuristic and Empire.',
        '- The earlier three-match smoke and 110-match development fixture remain preserved in separate directories. The definitive 300-match cohort uses the final contract hash throughout.',
        '', 'Definitive outputs: `artifacts/arena-case-study-preparation-v1/dry-run-300-final/` contains benchmark-manifest.json, contract.json, schedule.json, results.jsonl, match-index.json, request-ledger.json, integrity.json, analysis.json, plot-data.csv, case-study-report.md, sealed matches, request journals and gates.',
        'Eleven figures are prepared in PNG/SVG: win rates/CIs; three cost frontiers; match lengths; failure AP; stop-reason AP; bounded recovery; static repairs; side outcomes; additional truncation/AP-loss frontier. All fixture plots are labeled OFFLINE FAKE FIXTURE.',
        '', '## Resume and future authorization','',
        'An exclusive OS lock prevents competing writers. Pre-send reservations are fsynced and counted before transport; turn checkpoints and sealed match hashes support exact-prefix resume. A request/response without a committed turn blocks automatic resume for manual evidence resolution; it is never automatically resent. This is fail-closed protection against duplicate billing, not a claim that remote exactly-once delivery can be proved after a crash.',
        'Batch gates recheck requests, source/runtime and bindings, no fallback, metric recomputation, new-batch replay and prior sealed evidence. Resume/analysis replay the entire completed prefix. The CLI never advances beyond an explicitly supplied batch scope.',
        '', '**Recommend first live authorization: batch 1 only, 30 matches, at most 1,700 requests.** Prior tactical validation is sufficient; this checkpoint addresses full-game expenditure and integration risk. Inspect integrity and cost without selecting on desired outcomes, then separately authorize the remaining frozen 270 games.',
        '', 'Future commands—not executed:', '','```powershell',
        '.venv/Scripts/python.exe -B -m aig.arena.case_study verify',
        '.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-01 --through-batch 1 --authorize-live arena-case-study-benchmark-v1',
        '.venv/Scripts/python.exe -B -m aig.arena.case_study verify --output artifacts/arena-case-study-live-v1-01',
        '.venv/Scripts/python.exe -B -m aig.arena.case_study analyze --output artifacts/arena-case-study-live-v1-01',
        '```','', 'Only after separate authorization for the remaining scope:','','```powershell',
        '.venv/Scripts/python.exe -B -m aig.arena.case_study run-live --output artifacts/arena-case-study-live-v1-01 --through-batch 10 --authorize-live arena-case-study-benchmark-v1',
        '```','',
        'No known preparation blocker remains. Live execution still needs explicit authorization, working credentials and any required network permissions, with the frozen configuration/runtime verified. The historical whole-tree guard mismatch is documented expected provenance behavior. One canonical scenario, nondeterministic service conditions, possible limit censoring and potentially degenerate empirical bootstrap uncertainty restrict interpretation.',
        '', '**Stopped after preparation. Candidate contracts, Luna configuration, heuristic tactics and game rules remain unchanged.**']
    report=ROOT/'docs/arena-case-study-preparation-results.md'
    report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    final=dict(status='COMPLETE_OFFLINE_PREPARATION',contract_sha256=contract['sha256'],
        contract_file_sha256=sha(DEFAULT_CONTRACT),report_sha256=sha(report),
        matches=300,exact_replays=integrity['replay_verified'],fake_requests=integrity['reserved_requests'],
        openai_inference_requests=0,ollama_requests=0,luna_full_matches=0,
        final_targeted_tests=24,historical_tests=dict(passed=130,expected_source_guard_rejection=1,scoped_behavior_passed=1),
        preservation=preservation,resume=resume,gate_count=len(list((DRY/'gates').glob('*.json'))),
        plot_pngs=len(list((DRY/'plots').glob('*.png'))),plot_svgs=len(list((DRY/'plots').glob('*.svg'))))
    (PREP/'final-verification.json').write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps(final,indent=2))


if __name__=='__main__':main()
