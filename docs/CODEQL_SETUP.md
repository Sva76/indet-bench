# CodeQL eligibility and activation plan

**Current status (2026-11-13): NOT ENABLED.**

IndetBench is a **private repository owned by a personal GitHub account**. GitHub's current Code Security documentation requires a **public repository**, or an eligible **organization-owned private repository** with GitHub Code Security enabled, for GitHub CodeQL code scanning and Copilot Autofix. **Do not make IndetBench public or purchase a subscription merely to enable scanning.**

Official sources:
- https://docs.github.com/en/code-security/reference/code-scanning/troubleshoot-analysis-errors/private-repository-enablement
- https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning/configure-code-scanning
- https://github.com/github/codeql-action

If Code Security later becomes available for this repository, the owner can enable **CodeQL default setup** in GitHub `Settings → Advanced Security → Code Security → CodeQL analysis`; select Python and an appropriate query suite. Default setup requires no committed CodeQL workflow. If a custom advanced setup is needed, use the official `github/codeql-action@v4` `init` and `analyze` actions with `contents: read` and `security-events: write` permissions and check CodeQL feature eligibility first. Do not run incompatible default and advanced setups simultaneously.

Copilot Autofix may suggest patches for some code-scanning findings but is **not** a formal correctness proof. Always review generated modifications and rerun tests.

In the meantime `.github/workflows/security.yml` runs Bandit medium-and-higher severity/confidence checks in CI. The runner uses a narrowly documented Bandit B615 suppression on `from_pretrained` calls **only after** runtime validation of an exact 40-hex commit SHA; older Bandit versions cannot statically infer that a variable is pinned (https://github.com/PyCQA/bandit/issues/1345). The validation is unit tested; `.github/workflows/ci.yml` runs the unit tests. Neither replaces a thorough review of model-loading, archive parsing, prompt injection or dependency vulnerabilities.
