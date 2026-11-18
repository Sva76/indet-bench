# v2 draft: shortcut audits (18 November 2026)

Audits of the **v2 generator text only**. No model was run. Generator code at commit `b605ac2` (branch `claude/v2-audit-report`), committed **before** the confirmation seed was generated.

| File | Seed | `--flip-location` | Role |
|---|---|---|---|
| `audit_dev_seed20261118_any.json` | 20261118 | any (default) | development: the seed used while correcting the generator |
| `audit_dev_seed20261118_intermediate.json` | 20261118 | intermediate | development |
| `audit_confirm_seed20261119_any.json` | 20261119 | any (default) | confirmation: generated once, after the code was committed |
| `audit_confirm_seed20261119_intermediate.json` | 20261119 | intermediate | confirmation |

Reading of the results: [V2_GENERATOR_SPEC.md §5](../../docs/V2_GENERATOR_SPEC.md#5-shortcut-controls-binding-before-any-model-run).

## How to reproduce

```bash
python -m pip install -e .
indet-bench-v2 generate --seed 20261119 --flip-location any --output pairs.jsonl --controls controls.jsonl
indet-bench-v2 audit --input pairs.jsonl > audit.json
```

The generated files are not committed: they are rebuilt from the seed. Their SHA-256 (Python 3.13; `tests/test_gen_v2.py` checks the confirmation pair file on every CI run):

| Seed | Flip location | `pairs.jsonl` | `controls.jsonl` |
|---|---|---|---|
| 20261118 | any | `1bcfb69a4feae40a56598b4ffbcd1387ce56733ea17fda30d22dfcba28b5eed9` | `136f02fdf8d15eb9d607b5d33c50158a642d290979496fc988f29b255af41550` |
| 20261118 | intermediate | `655dbae764a07a7bef647df00e8484742ef9ccfe44fdd6a4e00195cb2573536b` | `9f72a86bed0331d21313ae46213efe2a5b0ea37889648937211bcdc86c57a9e5` |
| 20261119 | any | `074057c43b56dbcbe24db4dd1f3538e8f46eeda227982918e7e07bd9dd044ae1` | `604431de615ea95cb0c4fedb89ee596f0ee299be8fbd2f3ad5a64605ce696732` |
| 20261119 | intermediate | `3f83818814632c71af26ce31c500b396fffae4966c24149ecd4cf65ba2a3f1d6` | `8de24e0098263a368ec1e0e00561b9835f5687b7232f2e8915dac84ba461c16a` |

Audit files (`sha256sum *.json`):

```
a2fa4fef8534f8f9e4a400741030df63132c0e25f90be60bfaa6dd9749a11622  audit_confirm_seed20261119_any.json
f0b627dbfbee56288748cef243cad4d3a18d302622f4bbfe2548bfd62590eefc  audit_confirm_seed20261119_intermediate.json
cb526f5ff88e4029b7e224bf43cc70cb2e99e76c1dcc8996c9d7040f35975632  audit_dev_seed20261118_any.json
45bcc62bbd6106d18db9d797a6792054230cc2ab18731367ddef38f528a27fce  audit_dev_seed20261118_intermediate.json
```

Original IndetBench material, © 2026 Simona Vargiu, PolyForm Noncommercial License 1.0.0.
