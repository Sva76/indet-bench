# v2 draft: shortcut audits (18 November 2026)

Audits of the **v2 generator text only**. No model was run. Reading of the results: [V2_GENERATOR_SPEC.md §5](../../docs/V2_GENERATOR_SPEC.md#5-shortcut-controls-binding-before-any-model-run).

| File | Seed | `--flip-location` | Role |
|---|---|---|---|
| `audit_dev_seed20261118_any.json` | 20261118 | any (default) | development: the seed used while correcting the generator |
| `audit_dev_seed20261118_intermediate.json` | 20261118 | intermediate | development |
| `audit_confirm_seed20261119_any.json` | 20261119 | any (default) | confirmation |
| `audit_confirm_seed20261119_intermediate.json` | 20261119 | intermediate | confirmation |

## What "confirmation" means here

- The prompt-generating code was committed in `b605ac2` before seed 20261119 was generated for the first time.
- After CodeRabbit's review of PR #25, story ids were made dataset-specific, metadata fields were added and the audit gained the single-rule readers and a location-scoped feasibility table. The **prompts and gold labels of seed 20261119 did not change**: they were compared row by row, both settings, B/C and D files.
- The audits above were then **re-run on both seeds with the revised audit code**. Later revisions in the same pull request changed only ids, validation, the added `exact` (unrounded) fields and the marking of single-rule readers for rules that do not exist at a level as "not applicable" (previously reported as constant W 0.50); every other value was checked to be identical. The single-rule readers were therefore first computed on the confirmation seed after the generator had been fixed, but the audit code itself was revised after the first confirmation run. Neither seed is the final data set.

## How to reproduce

```bash
python -m pip install -e .
indet-bench-v2 generate --seed 20261119 --flip-location any --output pairs.jsonl --controls controls.jsonl
indet-bench-v2 audit --input pairs.jsonl > audit.json
```

The generated files are not committed: they are rebuilt from the seed. Their SHA-256 (Python 3.13). `test_confirmation_files_checksum` in `tests/test_gen_v2.py` rebuilds the four seed-20261119 files and checks these values in the `cpu-tests` job of `.github/workflows/ci.yml` (Python 3.10 and 3.12; pushes to `main` and every pull request). The seed-20261118 files are not checked in CI.

| Seed | Flip location | `pairs.jsonl` | `controls.jsonl` |
|---|---|---|---|
| 20261118 | any | `71d2c1046f6376e8e4cf43c9eef6f6cd7a47f92be93b363028e509cd81b698c5` | `6eae6227d2bed747e79a1a062b148dccfc16fbbc49d2ec78ebc14ec463b51159` |
| 20261118 | intermediate | `9f64516c9c87e0e3f7d15cd2be070024222107b7f17587f5cdd9254155a0163d` | `bb4229880f5163c6bea4477b16e24f6eadeac21d3a386ad9e7f75541057c081a` |
| 20261119 | any | `9c1358c8a978ab0750f8fb877b6cd26c7b8cd54d59d64b0c7f05bc4728a0e6ba` | `ceeb73f42adf844951bc2c88dea6973252e85e08c2898b756c627f01684550f7` |
| 20261119 | intermediate | `f8da8b118bcd944551910bf2dacd949d50357caf8ed91cc102e8876a53d989e1` | `2e8c19f21e112807a71d21a285c4b65fd52167697fe3f99c2294d5cc717f6294` |

Audit files (`sha256sum *.json`):

```
b0a556b1d42620b4c2707fac01689e2b075b27aeea35a6c88e9ed034cafa42a1  audit_confirm_seed20261119_any.json
20c4222fe6cd88e80c92cc0f7048d34b70c9fa7b0a10557408aa3da83d66e208  audit_confirm_seed20261119_intermediate.json
5db9c1db599e85604e9e3075fa23422555ef1401955c2cef5f6e2c57b2c9860e  audit_dev_seed20261118_any.json
77ed4925a2b614cb2c62485ed50c5dbed49f2358e6c2d6ca92b25fb692dcab25  audit_dev_seed20261118_intermediate.json
```

Original IndetBench material, © 2026 Simona Vargiu, PolyForm Noncommercial License 1.0.0.
