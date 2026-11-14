# Security checkpoint — pre-alpha

**Scope:** Python source under `src/indetbench/` on the review branch, not a full penetration test or formal verification.

## Measures implemented

| Input boundary | Control | Evidence |
|---|---|---|
| Hugging Face model loading | Exact 40-character immutable Git commit SHA **required**; mutable `main` and tags rejected | `hf_runner.validate_revision`; unit tests |
| Model file format | `trust_remote_code=False`, `use_safetensors=True` | `hf_runner.load_hf` |
| Tokens/secrets | `HF_TOKEN` read from environment only; never embedded in examples | `hf_runner.main`, `.gitignore` |
| User JSONL B/C cases | Required fields, unique row IDs, complete pairs, consistent group IDs; inputs not silently truncated | `hf_runner.load_pairs`; unit tests |
| ZIP results archives | Before reading: reject path traversal, encrypted entries, excessive file counts, uncompressed member/total bytes and suspicious compression ratios | `archive_safety.check_zip_archive`; unit tests |
| Local results | Optional exact SHA-256 verification of frozen archives | `replay.py`, `docs/REPRODUCIBILITY_STATUS.md` |
| Python code | Bandit static scanner on push/PR, medium+ severity and confidence | `.github/workflows/security.yml` |
| Correctness | Python unit tests in multiple versions | `.github/workflows/ci.yml` |

## Security scan finding and remediation

The initial Bandit CI run raised **two B615 (CWE-494)** findings on `AutoTokenizer.from_pretrained` and `AutoModelForCausalLM.from_pretrained`: revision pinning was optional. The runner now rejects missing/branch/tag/short revisions before any download; only a 40-hex commit is accepted. Bandit 1.8.6 cannot reliably prove that a runtime-validated variable is immutable (https://github.com/PyCQA/bandit/issues/1345), so the two call sites have **narrow, documented B615 suppressions** with a separate validation unit test. We have **not** disabled B615 for the package.

## CodeQL / Copilot Autofix availability

At the time of this checkpoint the repository was private on a personal account and therefore not eligible for CodeQL. Since 14 November 2026 it is public and eligible. No CodeQL analysis, SARIF upload or Copilot Autofix has been performed yet; see `docs/CODEQL_SETUP.md` to enable it.

## Remaining risks

- Hugging Face dependencies and any model/repository content remain a third-party supply-chain boundary despite pinning; verify packages and providers separately.
- Model inference can still consume substantial CPU, GPU memory or disk space; run untrusted model files in a constrained environment.
- The ZIP bounds are guardrails, not malware scanning and not a substitute for source integrity.
- AI-assisted code and automated suggested patches still require human security review.
- The exact main-branch state is not updated until this draft pull request is merged by the owner.

**Result:** static lint and unit tests are protective measures, **not proof of vulnerability-free code**.
