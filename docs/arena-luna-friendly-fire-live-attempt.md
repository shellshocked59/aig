# Luna Fireball A/B: first authorized attempt

Date: 2026-09-14. The user authorized the prepared A/B after reviewing its scope.

The old-prompt arm (`arena-turn-prompt-v1`) was started with the frozen plan and
stopped on the first fixture, `empty_blast`, trial 1. The runner reported
`connection_failure` after 0.6346 seconds, with one recorded request attempt,
zero repairs, zero accepted plans, zero executed actions, and no token usage.
The new-prompt arm was not started. No full matches or Ollama calls occurred.

Evidence remains in `.local/arena-luna-fireball-v1-old/manifest.json` and
`.local/arena-luna-fireball-v1-old/summary.json`. Zero-valued tactical aggregates
are not behavior results: there was no model decision to evaluate. A recorded
attempt does not establish that OpenAI received an inference request.

Two TCP-only connectivity checks to the configured OpenAI host (`api.openai.com`,
port 443) isolated a sandbox restriction. The default execution environment raised
`PermissionError`, errno 13, WinError 10013. The same check with tool escalation
connected successfully. Neither connectivity check sent an inference request.
This supports a sandbox network restriction as the cause; it does not establish
API authentication or model availability.

The frozen stop policy requires separate authorization for a retry after connection
failure. No retry or second arm has been run. Source, prompts, fixtures, profile,
settings and the frozen preparation artifact remain unchanged.

Proposed retry, requiring the same escalated execution permissions and a fresh
output directory:

```powershell
.venv/Scripts/python.exe -m aig.arena.friendly_fire_experiment --live --plan artifacts/arena-luna-friendly-fire/plan-v1.json --prompt arena-turn-prompt-v1 --output .local/arena-luna-fireball-v1-old-retry-01
```

If the retry completes, the existing prepared new-prompt command remains:

```powershell
.venv/Scripts/python.exe -m aig.arena.friendly_fire_experiment --live --plan artifacts/arena-luna-friendly-fire/plan-v1.json --prompt arena-turn-prompt-v3 --output .local/arena-luna-fireball-v1-new
```

A full retry plus the new arm would allow 48 decisions and up to 96 additional
request attempts (including bounded repairs), or up to 97 recorded attempts
including the failed attempt. This revised ceiling must be explicit in retry
authorization. Stop again on the existing failure conditions; preserve all evidence.

## Authorized retry result

The user subsequently authorized the retry. The old-prompt command above was run
with elevated network permissions in `.local/arena-luna-fireball-v1-old-retry-01`.
It reached OpenAI successfully and stopped after two decisions because the second
plan contained an illegal action. The new-prompt arm was not started.

| Fixture / trial | Selected plan | Execution result |
| --- | --- | --- |
| empty_blast / 1 | Mage Attack enemy three times | All three attacks executed; Blue won |
| friendly_only / 1 | Mage Attack enemy; ally Attack enemy; Mage Attack enemy | First attack executed; ally attack rejected as outside range; remaining plan truncated and turn ended |

The ally Knight at (2,0) cannot attack the enemy at (4,2). The preceding Mage
attack did not change these positions. This was an action-legality failure, not
a transport failure or a Fireball failure. Both responses passed the existing
structural validation on their first attempt, but only one plan completed without
execution illegality. No repair request was made: execution errors are not repaired
under the frozen control policy.

Retry totals: 2 provider requests, 2 accepted structured plans, 0 repairs,
4,995 input tokens, 132 output tokens, 0 cached input tokens, 0 reasoning tokens,
and 4.6192 seconds summed request latency. No Fireball was selected or executed;
there were no enemy/friendly Fireball hits, damage or downs. These two observations
cannot establish the effectiveness of the tuned prompt, which was not evaluated.

Both saved command traces replayed exactly to their saved final snapshots.
The prepared source manifest still matches. Verification is saved in
`.local/arena-luna-fireball-v1-old-retry-01/offline-verification.json`; original
manifest and summary evidence remain alongside it. The first failed sandbox run
is preserved separately. Total recorded attempts across both runs: 3, of which
the two retry requests returned successful OpenAI responses.

The authorized retry has stopped under the agreed execution-illegality condition.
No remaining request budget was consumed, no defaults or frozen policies changed,
and no further retry, tuned arm, or full match was run. Completing a comparison
requires a separately reviewed continuation or revised evaluation policy; the
existing failure must remain in the evidence rather than being silently discarded.
