# V5 prompt contract experiment

Environment V5 is frozen for this experiment. Only the selected planner prompt
changes. Prompt v1 retains its exact historical bytes and remains the default;
select `--prompt-version v2` explicitly. The six-field schema, executor, scenario
v3, replan interval 5, action cap 256, and luna-config-v1 remain fixed.

Prompt v2 retains all v1 instructions, changes the version label, and appends:

```text
Game rules and strategic action semantics:
All civilizations are permanently at war. There is no peace or alliance system.
Undefended enemy cities can be captured by eligible units entering them:
Warriors, Scouts, and Spearmen can capture; ranged units and Settlers cannot.
Losing your final city eliminates you, even if units or Settlers remain.
Conquest victory occurs when only one normal civilization remains.
Barbarians do not count as normal civilizations for conquest victory.
DEFEND represents protecting territory against a current local military threat.
```

The question is whether making the actual objective and action meaning explicit
reduces stalled wars. There is no added instruction to attack more often or
change a particular production choice.

## Design and reproduction

Run two fresh all-faction Luna simulations per prompt, capped at 100 turns.
These are prompt comparisons on identical initial states, not head-to-head games
between prompts. Each command runs one pair (two simulations) and performs its
own live preflight. Output directories must be new. Run v1, then v2; this fixed
order is a limitation because remote model behavior can vary over time.

```powershell
$env:AIG_AI_REPLAN_INTERVAL = '5'
$env:AIG_AI_MAX_ACTIONS = '256'
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a openai --provider-b openai --games 1 --turns 100 --environment-version v5 --scenario-version v3 --prompt-version v1 --plan-schema-version v1 --luna-config-version v1 --output .local/prompt-v1-new
.venv\Scripts\python.exe -m aig.ai.benchmark --provider-a openai --provider-b openai --games 1 --turns 100 --environment-version v5 --scenario-version v3 --prompt-version v2 --plan-schema-version v1 --luna-config-version v1 --output .local/prompt-v2-new
```

Compare conquest completion, victory turn, turn caps, and DEFEND activations with
no visible threat. Check provider purity, replay, initial-state hashes, and
configuration equality before interpretation. Two trials per condition are a
pilot, insufficient to establish conquest reliability or model intelligence.
No visible threat is an observation metric, not proof that defense was irrational.

## Historical context

- Heuristic: reliable conquest in the fixed deterministic control, turn 75.
- Luna V5 trial 1: substantial military power but no conquest by turn 100;
  50 DEFEND activations without a visible threat.
- Luna V5 trial 2: conquest on turn 46; 12 such DEFEND activations.
- Qwen: retired from primary testing after V4; retained as the small-model baseline.

The historical Luna victory was 29 turns earlier than the heuristic control.
Both normal factions used the same provider in each run; this was not Luna
defeating the heuristic. Historical evidence remains in
`.local/benchmark-environment-v5-live-20260911/`.

## September 11, 2026 results

| Prompt | Trial | Result | DEFEND without visible threat |
| --- | --- | --- | --- |
| v1 | 1 | Turn 100 cap, no winner | 54 |
| v1 | 2 | A conquest, turn 48 | 17 |
| v2 | 1 | A conquest, turn 45 | 5 |
| v2 | 2 | A conquest, turn 45 | 7 |

The v1 split recurred; neither v2 run stalled. This pilot supports the hypothesis
that the explicit game contract improves conquest completion. It does not
establish reliability, statistical significance, or a change in intelligence.
DEFEND counts aggregate both civilizations and cover games of different lengths.
Both v2 victories occurred 30 turns before the historical heuristic control.

All four runs were pure Luna with successful command replay. Initial-state
hashes matched, and recorded configurations were equal except for the prompt.
The runner's backend source digests matched before and after all four trials.
Comparison against the earlier V5 source manifest found changes only in
`prompts.py`, `test_experiment_versions.py`, and `docs/benchmarking.md`;
the environment, scenario, schema, profiles, and executor were preserved.
Offline verification: 25 versioning tests and 14 OpenAI provider tests passed.

The initial sandbox preflight failed with `connection_failure`, starting zero
trials. Its diagnostics were retained. The network-enabled retry completed all
four trials under the existing strict provider safeguards. No Qwen run was made.

Evidence: `.local/benchmark-v5-prompt-comparison-20260911-retry-1/`, containing
`results.json`, `comparison.json`, source digests, and per-prompt `summary.json`
files plus initial/final snapshots and command/plan/activation/inference traces.
The failed preflight is in `.local/benchmark-v5-prompt-comparison-20260911/`.
