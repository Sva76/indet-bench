# Security Policy

## Development status

IndetBench is currently private, in pre-alpha. Code dealing with externally supplied B/C datasets, ZIP archives and Hugging Face models has not yet undergone a formal independent security audit.

## Reporting a vulnerability

Please report vulnerabilities **privately to the repository owner** rather than creating a public issue or publishing a proof of concept. When GitHub private vulnerability reporting / security advisories are available for this repository, use the corresponding GitHub Security interface.

Please include affected version or commit, impact, minimal reproduction and proposed mitigation, without disclosing personal data or authentication tokens.

## Supported versions

Only the latest reviewed development branch is maintained; there is no production release or security support commitment yet.

## Important boundaries

- Installing or downloading external model files is **opt-in**. IndetBench's Hugging Face runner requires a 40-hex commit SHA and `safetensors` rather than mutable branches or pickle weights. Always review the model provider's terms and source before loading weights or tokenizers.
- Do not commit `HF_TOKEN`, cloud credentials, model-gated tokens or confidential dataset files.
- Treat JSONL/CSV and compressed experiment archives supplied by strangers as **untrusted input**. Run them with ordinary user privileges, in an isolated environment.
- No CodeQL or Copilot Autofix claim is made while this private personal-account repository is ineligible for GitHub Code Security.
- The separate GitHub Actions Bandit workflow is **static security linting**, not formal verification or a security guarantee.
