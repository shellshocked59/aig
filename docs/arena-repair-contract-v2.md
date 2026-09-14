# Candidate repair contract V2: implementation and frozen comparison

Implemented as an additive, opt-in repair binding. The paired experiment is prepared, integrity-checked, and **not run**. No OpenAI or Ollama inference, connectivity probes, live focused validation, or live matches occurred. Product defaults remain unchanged.

## Evidence and namespace audit

The [focused forensic report](arena-candidate-focused-forensics.md) and its [machine-readable evidence](../artifacts/arena-candidate-forensics/20260914-audit-v1/forensics.json) establish six repair episodes, two valid repairs, four failures. Existing candidate repair uses `ModelArenaTurnProvider.create_turn_plan`: one initial request, at most one static repair, same observation and schema. Its second user message contains only the failure category. The prior response is neither appended nor linked through provider response IDs. Thus the repairer cannot inspect the rejected tactical sequence. AP diagnostics and first-action legal-catalog failures lose their detail at the message boundary.

The namespace audit found `arena-step-repair-v1` and `arena-step-repair-v2` in `ai/repair.py`, plus `arena-action-id-repair-v1` in `ai/action_id.py`. Historical step repair V2 already echoes safely parsed V1 decisions and asks for one exact catalog action. Its old experiment uses six authored injected challenges and V2 observations. Those contracts, fixtures, experiments, results, and providers are unchanged. Reusing the historical V2 identifier for this candidate contract would misidentify both the schema and policy.

New identifiers in the **candidate repair namespace**:

| Identifier | Meaning |
| --- | --- |
| `arena-candidate-repair-v1` | Explicit name for the existing generic category-only candidate repair; byte-identical messages |
| `arena-candidate-repair-v2` | Opt-in enriched candidate repair |
| `arena-candidate-repair-context-v2` | Separate repair-input context schema |
| `arena-candidate-repair-prompt-v2` | Shared preserve-intent repair instruction |
| `arena-candidate-repair-comparison-v1` | Frozen six-episode, three-repetition paired screen |

The [manifest](../artifacts/arena-repair-contract-comparison-01/manifest.json) records source revision, all backend Python source hashes, prompt hash, schema version, ancestry, forensic hash, challenge hash, and schedule hash. The [seal](../artifacts/arena-repair-contract-comparison-01/seal.json) binds those artifacts, including the separate context schema and exact prompt text. A source revision alone does not describe this dirty workspace; byte hashes are authoritative.

## Implementation and input contract

Added [candidate_repair.py](../backend/aig/arena/ai/candidate_repair.py) provides `OpenAIRepairCandidateProvider` and `OllamaRepairCandidateProvider`. Both inherit the unchanged candidate provider and its existing single-repair loop through the existing rejection-evidence/message hooks. Select `repair_version=NEW` explicitly; the new classes themselves default to `OLD`. No factory, product default, candidate prompt binding, controller, parser, game rule, heuristic, or Empire source was changed.

The current authoritative observation remains the first user message, exactly as before. Its V4 legal-action catalog already supplies current legal alternatives; the second message references that catalog rather than duplicating it. The enriched second message contains:

- Version IDs, decision cardinality, observation hash, and original rejected-output SHA-256.
- A semantic `rejected_plan` with original action order, actors, targets, coordinates, and explicit EndTurn, when recoverable. Full-turn and bounded replacement retain the complete replacement proposal; stepwise retains its single action in the unchanged plan envelope.
- The existing validation category, index, field, and fixed message. Unsafe rejected free-text values are omitted.
- Available AP, total planned AP, amount over budget, and each action's authoritative AP cost.
- Per-action immutable reference/ability diagnostics, and first-action current legality diagnostics, including exact range/distance, target expected/actual status, or blocked LOS when the authoritative validator identifies that failure.

Reference checks isolate each action and temporarily remove only its AP masking in a detached diagnostic observation; the actual observation, validation result, and AP ledger remain unchanged. The first-action check reconstructs the current state and calls **read-only** `validate_command`; it never calls execution. The four range failures now identify the actual geometric defect rather than merely `invalid_reference`. AP-overbudget POSITION cases expose both the AP failure and the masked first-action range failure.

Later actions receive immutable reference/ability checks only. Later range, status, occupancy, and LOS are not predicted. A Bash followed by an Attack may still pass initial validation and become invalid after committed execution; that continues to trigger bounded replanning. A Move/Snipe sequence is not rejected because Snipe is outside range before the Move. No valid prefix is automatically committed or claimed to be sequentially executable. First-action current legality is recorded; the repair always returns a complete replacement.

Semantic extraction is bounded to six actions and 32,768 input characters. Unknown identifiers are redacted. Malformed JSON or unparseable actions produce `rejected_plan=null` with parse/schema diagnostics and the unchanged observation. A recoverable wrapper error can still retain valid semantic actions, including original EndTurn. No arbitrary raw prose is echoed into the repair request; extra fields and potential reasoning are not retained. This follows the historical repair safety convention.

## Repair objective and output

The shared prompt asks to correct the rejected output, preserve original intent, valid actions, targets, and ordering where legal, and make the smallest correction. It explicitly states that none of the rejected output has executed. It discourages substituting EndTurn merely because it validates easily, while retaining EndTurn for an intended stop or when no coherent valid repair remains. It adds no target ranking, AP-spending obligation, attack obligation, forced movement, or tactical similarity solver.

Both arms return the existing `arena-turn-plan-schema-v2` contract: a full plan for strict/bounded, or at most one semantic action for stepwise. No explanation, reasoning, repair notes, confidence, or AP ledger is requested in the output. The repository's concrete schema ID is `arena-turn-plan-schema-v2`; no new gameplay action schema was needed.

## Payload audit of the four failed trials

Both arms send the same frozen policy instructions, observation, Luna configuration, and control-specific output schema. OLD sends precisely the historical generic feedback. NEW replaces only that feedback with the shared repair instruction and enriched context.

| Episode | OLD feedback information | NEW additional facts |
| --- | --- | --- |
| R2 POSITION strict | `ap_budget` | Rejected `[Snipe(actor,enemy), Snipe(actor,reserve), EndTurn]`; available 3, planned 4, over by 1; costs 2/2/0; first Snipe distance 5, range 4 |
| R3 POSITION bounded initial | `ap_budget` | Rejected `[Snipe(actor,enemy), Snipe(actor,enemy), EndTurn]`, preserving repeated target and order; same 3/4/1 AP ledger and first-action 5/4 range diagnostic |
| R1 DOWNED bounded replacement | `invalid_reference` | The rejected replacement `[Attack(actor,enemy)]` at the post-Bash observation; available/planned 1/1; action index 0, distance 2, range 1 |
| R6 FIREBALL stepwise | `invalid_reference` | The rejected refreshed `[Attack(ally,enemy)]`, retaining original attacker; available/planned 1/1; index 0, distance 2, range 1; at-most-one cardinality |

The two other authentic episodes are retained: R4 POSITION stepwise (Snipe, distance 5/range 4, historical repair-to-EndTurn) and R5 FIREBALL bounded replacement (mage Attack, distance 3/range 2, historical valid Move repair). The [full payload audit](../artifacts/arena-repair-contract-comparison-01/payload-audit.md) prints all six enriched contexts and old/new payload hashes. [challenges.json](../artifacts/arena-repair-contract-comparison-01/challenges.json) contains the exact messages, instructions, schemas, raw historical output, observation, diagnostics, and historical telemetry for both arms.

## Telemetry and mechanical interpretation

Existing provider metrics and latency remain available. Additive rejected-decision telemetry records context, rejected-output hash, safe structured proposal, observation hash, version, and eventual repair outcome. `repair_comparison` records validity, safe parsed output, AP/action-count deltas, EndTurn introduction/preservation, error category, and repeated/new detailed diagnostic codes. Failed repairs are compared before the inherited redaction boundary discards raw text. No chain-of-thought is captured.

The repair-only runner preserves sanitized semantic JSON and an exact raw-output hash; it does not retain arbitrary rejected prose. The field documenting this representation prevents treating sanitized JSON as exact transport bytes. Provider tokens and wall latency are recorded per reserved slot. Input payload hashes resolve to the frozen complete messages.

Categories use mechanical rules:

- `EXACT_VALIDATION_FIX`: valid output with identical retained semantic actions, such as correcting a wrapper.
- `VALID_SUFFIX_TRIM`: valid nonempty exact prefix of the rejected action sequence.
- `VALID_INTENT_PRESERVED`: valid same-length sequence retaining type/actor/target at each index; a limited proxy, not a tactical judgment.
- `ENDTURN_ESCAPE`: **potential** escape when immediate EndTurn replaces attempted gameplay while current legal gameplay exists. This does not prove a coherent repair exists or that stopping was unnecessary.
- `REPEATED_SAME_ERROR` / `NEW_INVALIDITY`: validator category and detailed-code comparison; both original and repaired diagnostic codes remain inspectable.
- `MALFORMED`: parse/schema failure.
- `AMBIGUOUS`: valid changes outside these transparent relationships. A changed actor or a positioning replacement is not automatically deemed unrelated.

Original EndTurn preservation is separate from introduction. Empty completion remains distinct from explicit EndTurn. AP-valid, first-action range-valid, and immutable-reference-valid rates report known denominators; unparseable cases remain unknown. These are static diagnostics, not guarantees about later execution. Analysis is paired by episode/repetition and includes raw per-pair validity/category/count/AP deltas plus per-arm counts, rates, tokens, and latency. There is no LLM judge.

## Frozen experiment

The forensic report's exact recommendation is **6 saved invalid-first-response episodes × 2 contracts × 3 prespecified repetitions = 36 requests**. It is not 18 distinct failures. All six authentic episodes are included; no synthetic challenge was added. AP and range coverage, strict, bounded initial, bounded replacement, and stepwise are present. Reference/status/LOS cases are covered offline rather than expanding or silently replacing this cohort. There are no authentic reference/status/LOS failures in these six episodes.

The [schedule](../artifacts/arena-repair-contract-comparison-01/schedule.json) freezes 18 pair IDs and alternates arm order, balanced across pairs. Each arm gets exactly one request for the same observation and rejected proposal. Luna remains `gpt-5.6-luna`, `luna-config-v1`, reasoning `none`, max output 512, `store=False`, SDK retries zero. There is no initial-plan resampling, preflight inference, fallback, repair-of-repair, execution, or downstream decision. The hard ceiling is **36**, with no margin.

The runner verifies source/evidence/payload bindings before sending; refuses an existing live directory; durably reserves each slot before its transport call; persists every result; stops on a transport/provider failure; and seals results and ledger for analysis. A reservation counts even if the provider never received the request. Interrupted runs cannot be resumed or retried with this command. A separately authorized replacement experiment would need a new reviewed output root and accounting policy.

## Budget

Estimates use canonical payload character count divided by four, rounded up, including instructions, observation, context, and output schema. They are not tokenizer measurements and do not assume caching.

| Quantity | Estimate |
| --- | ---: |
| OLD input tokens/request | 2,326.5 |
| NEW input tokens/request | 2,835.7 |
| Added input tokens/request | 509.2 |
| Input tokens, all 36 slots | 92,919 |
| Historical repair output tokens/request | 44.17 |
| Expected input + output tokens | 94,509 |
| Maximum output allocation, 36 × 512 | 18,432 |
| Input estimate plus maximum output allocation | 111,351 |
| Historical mean repair latency | 1.309 seconds |
| 36-request historical latency extrapolation | 47.12 seconds |

The additional context may change provider latency and output length. File verification, scheduling, and network overhead are additional. No frozen pricing exists in this experiment, so no dollar estimate is provided.

Within the enriched context, the same character-based estimate averages 34.7 tokens for the rejected-plan object, 50.3 for the detailed-diagnostics array, and 37.1 for the per-action AP ledger. These are object-value estimates, not additive tokenizer measurements. The remaining increase includes the preserve-intent instruction, version/cardinality/hash fields, existing validation detail, AP totals, omission policy, catalog pointer, and serialization keys, minus the removed OLD feedback.

## Offline checks and preservation

The new 17-test suite covers all six forensic payloads and fake valid corrections, exact OLD messages, repeated AP/range failures, malformed initial/repair output, recoverable original EndTurn, valid EndTurn escape, AP suffix trim, 1–4 AP, unknown reference redaction, status and LOS, cardinality, strict/bounded/replacement/stepwise controller integration, unchanged replay, shared Ollama binding, frozen-payload corruption, 36 fake requests, no overwrite/resume, and stop-on-provider-failure accounting. Network/socket and real Responses calls are denied.

The [offline verification](../artifacts/arena-repair-contract-v2/verification.json) covers 47 passing tests: 17 new, 27 existing candidate, and 3 existing focused-runner tests. Another **24 historical repair tests passed**, for **71 passing tests total**. Historical candidate tests require a test-only source scope excluding exactly the two additive backend files, because their original inventory intentionally rejects additions. No historical manifest is regenerated and no production/live guard is bypassed. The initial unscoped candidate run failed that inventory assertion as expected. Historical repair regression results are retained in [historical-repair-tests.log](../artifacts/arena-repair-contract-v2/historical-repair-tests.log). An initial historical run encountered source-mutation guards while implementation edits were still in progress; the final run with stable source passed all 24 tests. PowerShell reported native-stderr redirection as an error while collecting the final unittest log; the log itself records `Ran 24 tests ... OK` with no test failures.

The before/after inventory verifies **16,380 pre-existing files byte-identical**, including historical V1/V4/V5, candidate focused/forensic evidence, repair snapshots, candidate prompts, observation/schema, controls, rules, heuristics, and Empire. Existing user changes were preserved. Only new files were added. Fake provider/controller tests exercise deterministic execution; no live validation or model-driven match was started.

## Future commands and gate

From `C:\code\aig`, offline verification is safe to repeat:

```powershell
.venv/Scripts/python.exe -m aig.arena.repair_contract_comparison verify --output artifacts/arena-repair-contract-comparison-01
```

After **separate live authorization**, the exact prepared command is:

```powershell
.venv/Scripts/python.exe -m aig.arena.repair_contract_comparison run --live --output artifacts/arena-repair-contract-comparison-01
```

Subsequent offline analysis:

```powershell
.venv/Scripts/python.exe -m aig.arena.repair_contract_comparison analyze --output artifacts/arena-repair-contract-comparison-01
```

Results will be under `live/result-NNN.json`, `live/request-ledger.jsonl`, and `live/completion.json`; analysis writes `analysis.json`. Those future live files do not exist at preparation completion. The prepared ledger template contains zero reservations.

A favorable descriptive screen requires higher repair validity, fewer repeated errors, and no increase in potential EndTurn escapes; inspect new invalidities, ambiguous structural changes, AP/range/reference compliance, tokens, and latency alongside those counts. Ties, mixed outcomes, incomplete accounting, or integrity failures do not justify promotion. This small repeated cohort is not a significance test or tactical-strength benchmark.

Even a favorable result requires separately authorized fresh matched candidate validation, likely eight snapshots × three controls. Only after reviewing that integration result should the full-match contract be frozen. This implementation authorizes neither that validation nor the 300-match benchmark.

## Files added

- `backend/aig/arena/ai/candidate_repair.py`: versioned context, prompt, diagnostics, classifier, opt-in provider bindings.
- `backend/aig/arena/repair_contract_comparison.py`: prepare/verify/run/analyze CLI and durable bounded request accounting.
- `tests/test_arena_candidate_repair.py`: offline regression cases and fake runner checks.
- `scripts/arena-repair-contract-offline.py`: network-denied regression and preservation verification.
- `artifacts/arena-repair-contract-comparison-01/`: frozen manifest, six challenges, 36-slot schedule, context schema, prompt, seals, payload audit, zero-request ledger template.
- `artifacts/arena-repair-contract-v2/`: before-state hashes and offline verification logs/results.
- This document. No pre-existing file was edited.
