# Workspace instructions

## GitHub account

For this workspace (`C:\code\aig`), use only the GitHub account `shellshocked59`.

Before any GitHub CLI repository operation, verify the effective authenticated account with `gh api --hostname github.com user --jq .login` in the same execution environment that will run the operation. This identity check is allowed solely to enforce this rule.

If the check fails or the login is anything other than `shellshocked59`, stop the GitHub operation and report an explicit account-verification error. In particular, never proceed as `ewashburn88` or `ewashburn88-tca`, even for read-only repository operations or when those accounts have repository access.

Do not run the intended operation after a failed check, silently switch accounts, substitute credentials, or use another GitHub tool to bypass this restriction. Resume only after the intended account is authenticated and verified. Repository ownership, remote URLs, and Git commit identity do not establish the authenticated GitHub CLI account.
