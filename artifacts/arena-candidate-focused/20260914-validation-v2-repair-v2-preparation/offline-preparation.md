# Fresh candidate validation preparation

24 turns, identical eight frozen snapshots and strict/bounded/stepwise order to validation V1. AP cohort: 1,3,5,2,2,3,1,2 (sum 19). Hard ceiling: strict 8x2=16; bounded 8x4=32; stepwise 2x19=38; total 86. No preflight inference, transport retry, fallback, or post-run trial is authorized. Prior use was 37/86; repair-only success was 17/18, but neither justifies reducing a structural ceiling for fresh nondeterministic outputs.

Live command (after passing offline checks):
`.venv/Scripts/python.exe scripts/arena-candidate-focused-repair-v2.py run --live --output artifacts/arena-candidate-focused/20260914-validation-v2-repair-v2`

Luna: gpt-5.6-luna / luna-config-v1, reasoning none, max output 512, store false, SDK retries zero. Explicit NEW binding for every provider instance, inherited by strict initial, bounded initial and replacement, and stepwise. Each actual outgoing repair payload must equal the frozen V2 message builder output; all request messages, policy instructions, and schema are durably persisted before transport. OLD remains available and defaults unchanged.

Final preparation is preparation-final.json. preparation.json is a superseded offline draft retained for provenance; its runner hash predates moving the large full preservation scan to the before/after boundaries. An initial fake-run test was interrupted for that overhead; it made no live request. Current source/binding checks and live artifact checks remain on every request boundary. No old source inventory is bypassed: prior source hashes must match, exactly the two previously authorized additive repair modules are present, and all current source hashes are frozen.

17 existing repair tests passed, including fake controller coverage of all four repair paths, malformed/repeated errors, OLD compatibility, EndTurn escapes, one-repair limit, and no future-state simulation. The new runner tests deny network and test global/per-trial ceiling denial, ledger corruption, complete 24-turn fake persistence/replay, no overwrite, and evidence-corruption rejection. See runner-tests.log for final outcome.

Preservation inventory contains 16,304 existing files, including prior validation, repair-only comparison, V1/V4/V5 literacy, prompts, repair V2, rules, controls, defaults, and Empire. Full hash verification is required before and after live inference. .env credentials are never copied or printed; effective nonsecret model configuration is checked.

No causal paired claim, model judge, full match, prompt tuning, or 300-match design is authorized by this run.
