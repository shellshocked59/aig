# Luna Fireball consequence-awareness experiment

Prepared offline on 2026-09-14. No OpenAI or Ollama inference was performed.
No default promotion or browser playtest is included.

## Baseline discovered in this checkout

The user observed empty and friendly-only Fireballs in animated Luna-vs-Luna play.
The browser path is `ArenaWebSession.observer_demo` → `ArenaGameplaySession.demo`
→ `ArenaSession.demo` → `create_arena_turn_provider(settings, "openai")` →
`OpenAIArenaTurnProvider`, invoked by `ArenaAiController.run_turn`.
It uses **arena-turn-prompt-v1**, **arena-observation-v1** and a full-turn plan.
It does not use the experimental stepwise or constrained structured providers.
This identifies the current code path; no saved trace of the user's particular
observed game was supplied, so its historical runtime identity cannot be independently verified.

V1 already mentions allies/caster and radius-one damage, but does not explicitly
ask the model to evaluate all blast occupants before choosing an impact.
Hypothesis: making that consequence salient reduces empty/self-destructive casts
without suppressing useful friendly-fire tradeoffs.

The next full-turn version is **arena-turn-prompt-v3**: v2 already exists.
The separate immutable `BEHAVIOR_PROMPTS` registry and `LunaBehaviorProvider` in
`backend/aig/arena/ai/friendly_fire_prompt.py` make v1/v2/v3 explicitly selectable.
The frozen historical registry, factories, defaults and source files are unedited.
This extension avoids breaking historical whole-file preservation hashes.
The existing generic benchmark CLI does not resolve this extension; use the dedicated CLI below.

## Exact inserted guidance

Inserted immediately before the existing output-contract paragraph; all other
V1 prompt bytes are retained:

```text
Before selecting an action, evaluate its resolved effect on the current board,
not merely whether it is legal. For area damage, account for every affected
friendly and enemy. Use the current legal-action catalog for movement and targets;
when sequencing later actions, account for changes caused by earlier actions.
FIREBALL HAS FRIENDLY FIRE. Before choosing an impact, examine the target tile
and all 8 adjacent tiles: a 3x3 area (Chebyshev radius 1). Identify every ACTIVE
friendly and enemy there. Fireball damages ALL of them, including allies and
the caster. DOWNED units and Cores are not damaged by Fireball.
A selectable impact is not necessarily useful. Avoid an area with no ACTIVE
enemies unless the actual state supplies a concrete tactical reason; avoid
damaging only your own team. Compare friendly damage and possible downs with
Attack, Snipe, movement or another legal action. Friendly fire can be acceptable
when its actual consequences justify the tradeoff; it is not categorically
forbidden. If both teams lose all ACTIVE units, the casting team loses.
```

No tactical ranking, minimum enemy count, damage-maximization policy, sacrifice
prohibition, examples with prescribed answers, or reasoning output was added.
No single-action/fresh-observation reminder was added because that would contradict
the actual full-turn control mode. Each planned action must account for preceding effects.

## Fixed variables and preservation

| Variable | Both arms |
| --- | --- |
| Rules | arena-rules-v2 / arena-scenario-v1; 2 AP, range 2/LOS, base damage 4, radius 1 |
| Observation | arena-observation-v1, actor-grouped legal board-position targets |
| Schema | arena-turn-plan-schema-v1; unchanged OpenAI strict output schema |
| Control | arena-control-full-turn-v1; zero to five actions, sequential resolution |
| Profile | luna-config-v1: gpt-5.6-luna, reasoning none, max output 512, store false, SDK retries 0 |
| Repair | Existing full-turn bounded repair: at most one extra request |
| Fixtures | arena-fireball-behavior-fixtures-v1; same exact snapshots in both arms |

Fireball damages ACTIVE units of either team, including the caster, excludes
DOWNED units and Cores, and resolves team elimination after the entire blast.
POWER/WARD use existing deterministic damage rules. The caster loses simultaneous
elimination. Gameplay, balance, observation, legal actions, settings, Qwen behavior,
and both heuristic providers are unchanged. The benchmark uses strict failure
handling instead of the browser's heuristic fallback, so fallback cannot confound the results.

Old prompt SHA-256:
`5380cc1f44d0cc64cfbaa4a342a23349bce5ae02b1b84a9a205dbf8fc99ab8a7`

New prompt SHA-256:
`5a517164a8f799b2f5e9b2f9a56103fb61e4ef690d2b7e6efd53412b08dce182`

`tests/fixtures/arena-friendly-fire-preservation.json` records historical prompt
hashes and protected source/artifact hashes, including arena-probes-v1. Existing
historical artifacts and hash manifests are untouched.

## Fixtures and analysis

The independently versioned fixture set is frozen in
`artifacts/arena-luna-friendly-fire/plan-v1.json` with snapshots, observation hashes,
illustrative impact results, model/schema/prompt identities, and a source manifest.
Its fixture hash is `15bdcaa96cc34e349db440154a6eec2d105cf5748c6f38abbab82a81d34614ce`.

| Case | Illustrative blast | Mechanical interpretation |
| --- | --- | --- |
| empty_blast | 0 enemies, 0 friendlies | Wastes damage opportunity; useful alternatives exist |
| friendly_only | 0 enemies, 1 friendly | Only damages own team; useful alternatives exist |
| clean_cluster | 2 enemies, 0 friendlies | Fireball remains a legal option |
| mixed_blast | 2 enemies, 1 friendly | Account for damage to all three |
| bad_trade | 1 healthy enemy, 1 friendly at 2 HP | Friendly downed; enemy survives |
| winning_trade | 2 enemies at 4 HP, 1 healthy friendly | Friendly damaged, both enemies downed, immediate victory |

These are complete states with other legal targets/actions, not forced-answer
questions. Illustrative impacts and computed consequences are never sent to Luna.
No exact action is prescribed for subjective cases; choosing Attack may be better.

`analyze_fireball` in `friendly_fire_fixtures.py` validates the command, queries
`arena_fireball_affected_units`, and applies the authoritative command to a deep copy.
It returns affected enemy/friendly IDs, actual HP removed (clamped, rather than
nominal overkill), downed IDs, impact, winner and immediate victory. Source state
is unchanged. It inherits bonuses, caster damage and simultaneous-elimination rules.

The runner analyzes every executed Fireball against its actual pre-action state,
including casts later in a plan. Each row saves the selected plan, whether Fireball
was chosen, alternative planned actions, execution/truncation details, per-cast
impact/hits/damage/downs/terminal result, command trace and final snapshot.
Planned actions can be truncated; do not confuse chosen casts with executed casts.
Per-action results record immediate wins for non-Fireball actions too.

Aggregates include zero-enemy casts, friendly-only casts, friendly damage,
productive casts (enemy HP removed > 0), immediate-win plans/actions, first-response
validity, and inference latency/token metrics with missing-usage coverage.
Productive is descriptive and does not imply a favorable trade. Fireball count
is not a success score. Compare bad casts per decision and inspect tradeoffs;
report failures rather than removing them from reliability denominators.

## Size measurements (offline)

Representative input uses the empty_blast fixture, identical in both arms.

| UTF-8 bytes | V1 | V3 | Increase |
| --- | ---: | ---: | ---: |
| System prompt | 1,730 | 2,803 | 1,073 |
| Luna instructions + input JSON | 7,260 | 8,347 | 1,087 |
| Hypothetical Qwen messages JSON | 7,263 | 8,350 | 1,087 |

JSON escaping accounts for the extra 14 bytes in input differences. These are
serialized input components, excluding unchanged schema/model options and SDK/HTTP
envelope overhead; hence the request payload difference is also 1,087 bytes under
this canonical serialization. This is not a tokenizer measurement or a live token
estimate. Input growth is about 15%; no unrelated optimization was made. Qwen
measurement is hypothetical only; no Qwen provider/default was changed or run.

## Future controlled live evaluation — authorization required

The prepared fixture experiment requests 6 states × 4 trials = **24 full-turn
decisions per arm, 48 combined**. This is a prompt-only comparison of the actual
browser control mode, not 48 stepwise actions. At most one repair per decision
means **48 requests per arm, 96 combined**. There is no inference preflight,
automatic extra trial, full match, or fallback. Trials are fixture-interleaved.

From `C:\code\aig`, the exact future old-prompt command is:

```powershell
.venv/Scripts/python.exe -m aig.arena.friendly_fire_experiment --live --plan artifacts/arena-luna-friendly-fire/plan-v1.json --prompt arena-turn-prompt-v1 --output .local/arena-luna-fireball-v1-old
```

The exact future new-prompt command is:

```powershell
.venv/Scripts/python.exe -m aig.arena.friendly_fire_experiment --live --plan artifacts/arena-luna-friendly-fire/plan-v1.json --prompt arena-turn-prompt-v3 --output .local/arena-luna-fireball-v1-new
```

These commands have **not** been run. They require separately authorized live
inference. The runner rejects profile/fixture/source drift and existing output
directories. It checks source hashes before every request and caps each arm at
48 requests. Stop on failed decisions after bounded repair, execution illegality,
source mutation or the request ceiling. Configuration/authentication failures must
be diagnosed before any separately authorized retry; preserve failed artifacts and
choose a new output directory. If the old arm stops, do not start the new arm
without reviewing the failure. Never switch profile to make the run proceed.

## Limitations and follow-up

Four trials per case provide a small descriptive audit, not statistical proof.
Synthetic states do not establish full-game strength. Full-turn sequencing adds
later-state legality effects; report the executed prefix and truncations. Provider
service variability and running the old arm first may affect results. No behavior
improvement is claimed until live data exists. If the controlled comparison looks
promising, a small tuned-prompt browser playtest is a separately authorized next step.

The preparation tests use fake providers only and cover preservation, browser
baseline selection, semantic/output constraints, six legal fixtures, purity,
bonuses/clamping, DOWNED/Core exclusion, winning trades, offline execution,
request counts, failure persistence, and fixture tampering.
The final focused suite passes 17 tests (6.2 seconds). The broader Arena suite
passed 429 tests (380.0 seconds); it was collected before the final focused test
additions. Commands: `.venv/Scripts/python.exe -m unittest discover -s tests -p test_arena_friendly_fire.py`
and `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_arena*.py'`.
The runtime configuration was checked through
the settings loader and matches the unchanged Luna profile; no credentials were
printed and no provider requests were made.
