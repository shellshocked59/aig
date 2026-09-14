# Arena Phase 9A: stepwise action-ID control

Phase 9A is an offline representation experiment. Action-ID selection is available
independently of structured stepwise control; normal gameplay defaults are unchanged.
No live inference, connectivity check, provider preflight or new full match was run.

Phase 8C completed 3/6 matches per repair arm, with 0/3 successful repairs and 82
requests per arm. First-response invalidity was 3.85% in both arms, and all paired
command traces were identical. Repair V2 changed an illegal enemy Heal into an
illegal self Heal without recovering the decision. Its 20/24 repair-only result
(versus V1's 8/24) did not transfer to match reliability. See the unchanged
[Phase 8C results](arena-repair-v2-fullmatch-results.md). Repair V1 remains default.

The hypothesis is that selecting an existing legal action removes the observed
unit/target-reference reconstruction error. Stepwise execution makes this possible:
each decision has one current state, a complete legal catalog and one action to
execute before rebuilding the observation. This does not establish better tactics
or prove that Qwen will copy IDs reliably.

## Contracts and architecture

| Domain | Frozen structured control | Experimental action-ID control |
| --- | --- | --- |
| Control | arena-control-stepwise-v1 | arena-control-stepwise-action-id-v1 |
| Observation | arena-observation-v2 | arena-observation-v3 |
| Prompt | arena-step-prompt-v1 | arena-step-prompt-v2 |
| Output schema | arena-turn-plan-schema-v1 | arena-step-action-id-schema-v1 |
| Repair | arena-step-repair-v1 (V2 experimental) | arena-action-id-repair-v1 |
| Probe benchmark | arena-benchmark-v2 | arena-benchmark-v4 |

**Version collision:** the authoritative checkout already uses
`arena-benchmark-v3` for the frozen structured full-match orchestrator. Its artifact
and hash remain unchanged. The new benchmark therefore uses `arena-benchmark-v4`,
rather than redefining V3. `arena-probes-v1`, `qwen-config-v1`, `luna-config-v1`,
rules, scenario, legal queries, action variants and heuristic policy remain fixed.

`ai/action_id.py` defines `ArenaActionIdStepProvider.create_step_choice`, immutable
`ArenaActionIdDecision`, both model adapters, the heuristic adapter and controller.
The adapters reuse the existing Ollama/OpenAI transport, settings, telemetry and
one-repair loop. The only shared transport extensions are overridable output-schema
hooks; their defaults preserve the prior structured request schemas and names.

The controller builds V3, validates the choice against that observation, resolves
the complete action, then uses the existing planned-action/command boundary and
authoritative execution. It rebuilds V3 after every action. No ID mapping survives
the decision: `A03` may mean a different action next time. An ID absent from the
current catalog fails, even if it existed previously. Five decisions is the safety
bound; 0 AP requests nothing. Explicit EndTurn is accepted, and provider failure
preserves the exact command prefix without a fallback or automatic EndTurn.

## Catalog, schema and repair

V3 retains all V2 information. Its legal catalog has this shape:

```json
{"legal_actions":[{"id":"A01","action":{"type":"attack","unit_id":"actor","target_id":"enemy"}}]}
```

The existing `action_order` remains actor ID, action type, target ID, then position
y/x. IDs are assigned in that exact order, starting at 1, padded to
`max(2, digits(catalog_size))`: A01 through A99, or A001 through A100 for 100 entries.
There is no fixed namespace limit or tactical ranking. Complete action semantics
remain visible. The catalog hash is SHA-256 of canonical JSON for the ordered list
`[[id, complete_action], ...]`; observation bytes and hashes are deterministic.

Both providers receive the same 125-byte strict schema:

```json
{"additionalProperties":false,"properties":{"action_id":{"type":["string","null"]}},"required":["action_id"],"type":"object"}
```

`{"action_id":"A17"}` selects a listed ID; `{"action_id":null}` intentionally ends
the turn. Extra fields and other field types fail `schema_validation`; malformed
JSON fails `malformed_json`; a syntactically valid unknown string fails
`invalid_action_id`. Transport/provider failures remain separate. Schema support
is covered with fake transports; actual server compatibility awaits the pilot.

Prompt V2 asks for one current ID or null, forbids ID modification and action-field
reconstruction, and explains fresh observations and ID locality. It has no tactical
priorities. Repair V1 supplies the exact failure category, sanitized rejected ID,
and the same current observation/catalog, asking for an exact listed ID or null.
There is at most one repair; a second invalid response ends with `repair_failed`,
while individual attempt categories remain available. Arbitrary rejected strings
are redacted; bounded ID-shaped values can be retained. Raw rejected output is not
persisted.

Decision traces include observation/hash, catalog hash, selected ID, resolved
action, membership, initial validity, repair attempts/results, authoritative command
result, AP and resulting state hash. Offline verification rebuilds the catalog at
each command boundary and checks the persisted resolution and replay. No timings
or secrets enter the catalog hash.

## Offline proof and baseline

The study checks all seven frozen probe states and nine historical Qwen
`invalid_reference` decision occurrences from Phase 7F and both Phase 8C arms.
Those nine occurrences represent **one unique failing state**, not nine independent
failures. Across these states, 684 catalog entries were individually executed on
detached state with exact AP-cost checks. Every V3 underlying action list equals
V2's ordered list, with unique IDs and unique complete actions; all V1 facts and
state snapshots round-trip unchanged.

There were 18 historical invalid attempts. The 12 retained Phase 8C rejected
decisions contain illegal actions absent from V3; they cannot resolve through a
valid current ID. Phase 7F did not retain its six rejected objects, so those exact
objects cannot be reconstructed. Its states and legal catalogs were still checked.
This is structural evidence only.

The heuristic adapter asks the unchanged structured stepwise heuristic for its
normal action and maps it to the current ID. All seven offline probe turns match
the structured heuristic's complete command traces and replay exactly: 27 AP,
24 selected actions, zero external requests.

| Probe | IDs in decision order | Resolved actions in order | AP | Outcome |
| --- | --- | --- | ---: | --- |
| finish_or_core | A02, A01, A01, A01, A01 | Finish body; attack red-core four times | 5 | No immediate victory |
| fireball_friendly_fire | A12, A02, A48, A45 | Fireball (4,1); attack enemy2; ally finishes enemy2; ally bashes enemy | 5 | No immediate victory |
| revive_decision | A21, A02, A21, A21 | Revive ally; heal ally; ally attacks enemy twice | 5 | Ally active |
| shield_bash_position | A24, A12, A25, A09, A19 | Bash enemy; move (3,2); bash enemy; move (4,1); bash enemy | 5 | Fresh positions respected |
| snipe_vs_basic | A24, A01, A01, A01 | Snipe enemy; attack enemy2 three times | 5 | No immediate victory |
| team_elimination | A01 | Attack enemy | 1 | Victory |
| winning_core_line | A02 | Attack red-core | 1 | Victory |

Full objects, command traces, snapshots and replay results are in
`.local/arena-phase9a-preparation-01/heuristic-probes/`; the repeated verified study
is `study-verified.json` in the same preparation directory. Repeated ID strings
in the table are resolved independently at each step.

## Size and context assessment

Canonical UTF-8 bytes, captured through fake transports with the unchanged profiles:

| Representative state | V2 / V3 observation | Ollama structured / ID request | OpenAI structured / ID request |
| --- | ---: | ---: | ---: |
| snipe_vs_basic probe | 3,385 / 3,935 | 7,753 / 5,815 | 7,372 / 5,797 |
| Opening full-match state | 6,462 / 7,650 | 11,430 / 10,304 | 11,049 / 10,286 |
| Historical midgame | 3,337 / 3,579 | 7,679 / 5,349 | 7,298 / 5,331 |

Observation growth is 16.25%, 18.38% and 7.25%, respectively. Transport requests
shrink because the schema drops from 2,567 bytes (Ollama) or 2,209 (OpenAI) to 125.
Representative logical structured outputs are 115/126/125 bytes versus 19-byte ID
outputs; actual generated token counts and OpenAI's nullable structured wire fields
must be measured live. Null EndTurn is 18 bytes.

For observation text alone, the same bytes/3ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“4 estimate gives V2 versus V3 ranges
of 847ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“1,129 versus 984ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“1,312 tokens for the probe, 1,616ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“2,154 versus 1,913ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“2,550
for opening, and 835ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“1,113 versus 895ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“1,193 for midgame. These exclude instructions,
schema and repair feedback.

Using request bytes divided by 3ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“4 as a rough input-token estimate gives
1,454ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“1,939 (probe), 2,576ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“3,435 (opening), and 1,338ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“1,783 (midgame). With Qwen's
4,096 context and unchanged 256 output reserve, estimated remaining headroom is
1,901ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“2,386, 405ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“1,264 and 2,057ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“2,502 tokens. Anchoring message growth to historical
Qwen prompt counts instead gives opening input 2,626ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“2,736 and midgame 1,350ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“1,360.
These are estimates, not Qwen tokenization or a fit guarantee: schema transport
bytes need not equal prompt tokens, and repair adds text. Opening states merit
particular occupancy monitoring. Do not alter `qwen-config-v1`.

Across all seven initial probe states, `fireball_friendly_fire` is the tightest
sample: 70 actions, a 10,613-byte Ollama action-ID request, an estimated
2,654–3,538 input tokens and 302–1,186 tokens of headroom after the output reserve.
The per-probe estimates are retained in `probe-context.json`. This makes actual
input-token/context telemetry an essential pilot measurement, especially on repair.

## Verification and preservation

The 27 dedicated tests cover deterministic V3 bytes/hashes and V2 golden hashes,
namespace capacity, complete catalogs and AP, both fake transports, schema errors,
successful/failed repair, rejected-output sanitization, stale/removed IDs, Attack,
Revive, Shield Bash, Fireball, Finish, EndTurn, AP bounds, request ceilings, replay
tampering, heuristic equivalence and benchmark metrics. The full Python suite
passed: **1,163 tests run, 5 skipped, no failures** (1,158 passed). The accepted
result is recorded in `python-regression-accepted.log` in the preparation directory.
Earlier logs are retained: an obsolete V3-is-unknown assertion was corrected;
editing that test during an earlier run also tripped a source-guard test. All 16
Observation V2 tests and the affected source-guard test passed on focused reruns,
followed by the clean full-suite pass. No frontend tests/build were needed because
frontend/build files were untouched.

The pre-existing inventory contains 5,341 files. Eight files differ from it:
observation.py, ollama.py, openai.py, benchmark_versions.py, test_arena_repair.py,
arena-ai.md, arena-benchmarking.md and test_arena_observation_v2.py, for the explicit
V3/schema/version extensions, preservation checks and documentation. The old V2
test's unsupported-version case now uses V999 because V3 explicitly exists;
its default-V1 assertions remain unchanged. The other 5,333 files retain exact byte
hashes, including all 5,131 inventoried historical evidence files.
The old source hashes are additionally checked
after reversing only the enumerated additive dispatch/schema hooks. Frozen V1/V2
observations, prompt and repair contracts, prior benchmark artifacts, game,
heuristic, profiles and Empire remain covered by regression checks. Frontend and
build files were not touched.

## Future Qwen pilot: prepared, not executed

Phase 9A files added: `backend/aig/arena/ai/action_id.py`,
`backend/aig/arena/action_id_benchmark.py`,
`backend/aig/arena/benchmark_artifacts/arena-benchmark-v4.json`,
`scripts/arena-action-id-study.py`, `tests/test_arena_action_id.py`,
`tests/fixtures/arena-action-id-golden.json`,
`tests/fixtures/arena-phase9a-source-extensions.json`, and this document.
Files extended: `ai/observation.py`, `ai/ollama.py`, `ai/openai.py`,
`benchmark_versions.py`, `tests/test_arena_repair.py`,
`tests/test_arena_observation_v2.py`, `docs/arena-ai.md`, and
`docs/arena-benchmarking.md`. Other pre-existing worktree changes belong to earlier
phases and were retained.

First authorize seven `arena-probes-v1` turns, one trial per probe, Qwen only.
There are at most 35 normal decisions and 35 repairs: **70 requests total**, with
zero preflights. Stop on the first failed turn, accounting discrepancy or replay
failure; preserve all artifacts and do not replace trials. The heuristic baseline
uses 24 decisions, but that does not predict the model's choices or request count.

From `C:\code\aig`, the exact proposed command is:

```powershell
.venv/Scripts/python.exe -B -m aig.arena.action_id_benchmark --provider ollama --probe all --probe-trials 1 --request-ceiling 70 --output .local/arena-phase9b-qwen-action-id-pilot-01
```

The module fixes the action-ID control/observation/prompt/schema/repair/benchmark
versions explicitly and rejects non-v1 model configurations. It guards source and
settings before each transport attempt. The output directory must be new.
Execution needs separate user authorization; sandbox connectivity restrictions
must be handled through the existing approval mechanism when authorized.

Compare with the frozen structured stepwise Qwen evidence using the same probes,
model, v1 profile and fresh-state semantics. Measure first-response schema and
overall validity, valid-ID rate, invalid-ID attempts, repair attempts/success,
executed AP, decisions/turn, explicit EndTurn, tactical outcomes, latency, input and
output tokens, and context occupancy. EndTurn is a valid decision but excluded from
the non-null ID membership denominator. Missing transport output is not proof of
schema validity. Retain per-attempt categories alongside aggregate metrics.

Improved reliability would support the reconstruction hypothesis; frequent invalid
IDs would show discrete selection remains difficult. Tactical quality is a separate
outcome. No expanded repetitions, Luna pilot or full matches are authorized here.
**Stop point: request authorization for the command above; do not execute it.**
