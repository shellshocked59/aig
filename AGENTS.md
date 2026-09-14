# Workspace instructions

## GitHub account

For this workspace (`C:\code\aig`), use only the GitHub account `shellshocked59`.

Before any GitHub CLI repository operation, verify the effective authenticated account with `gh api --hostname github.com user --jq .login` in the same execution environment that will run the operation. This identity check is allowed solely to enforce this rule.

If the check fails or the login is anything other than `shellshocked59`, stop the GitHub operation and report an explicit account-verification error. In particular, never proceed as `ewashburn88` or `ewashburn88-tca`, even for read-only repository operations or when those accounts have repository access.

Do not run the intended operation after a failed check, silently switch accounts, substitute credentials, or use another GitHub tool to bypass this restriction. Resume only after the intended account is authenticated and verified. Repository ownership, remote URLs, and Git commit identity do not establish the authenticated GitHub CLI account.

## Ollama connectivity and live Arena benchmarks

On 2026-09-13, Arena Qwen probe preflights repeatedly failed in about 0.026 seconds with `provider_exception`, zero accepted plans, and zero trials started. A read-only `GET /api/version` to the configured Ollama endpoint (`10.0.0.250:11434` at diagnosis time) exposed `URLError` wrapping `PermissionError [WinError 10013]` (socket access forbidden). The same version check with `sandbox_permissions: "require_escalated"` succeeded with HTTP 200 and Ollama version `0.34.0`. This was a sandbox connectivity restriction, not evidence of poor Qwen tactical ability or a stuck model.

Before retrying a similarly fast failure, check `/api/version` using the current `Settings().ollama.base_url`, without making an inference request. If sandbox socket permissions block it, use the tool's escalation mechanism for the read-only check. If that succeeds, authorized live provider commands need the same execution permissions. Do not bypass an approval rejection or assume every future failure has this cause.

The current Arena benchmark error allowlist omits the Ollama adapter's `transport_failure` category and reports it as `provider_exception`; persisted diagnostics may therefore hide the underlying transport cause. A recorded request attempt does not prove that Ollama received a request. Diagnose connectivity before recommending model restarts, tuning, or abandonment.

Keep live-run authorization and frozen benchmark policies intact: connectivity diagnosis does not authorize extra inference calls, retries, full matches, source changes, or model/profile changes. Preserve failed-run artifacts and use a new output directory for any authorized retry.
