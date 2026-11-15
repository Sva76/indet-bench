# Archived-results reproducibility — Step 3 progress

**Status:** CPU replay implemented for Tests U, U2, C (including HC4) and Test M notebooks A/B. These are *not* new model experiments. Since 15 November 2026 the source archives of Tests U, U2, M and C are published in [`research_originals/step2/outputs/`](../research_originals/step2/outputs/README.md); the notebook A archive without its TriviaQA rows (SHA-256 `fa9577be…6e033`; the replay passes on it with the same 498 values). `tests/test_original_archives.py` runs all six replays in CI.

## Evidence from local replay against original archives

The first local implementation recalculated individual B/C pair wins (ties = 0.5), aggregated by story/passage, and then computed paired ΔW using common valid pairs. Bootstrap confidence intervals used the frozen seed 20261108, 2,000 resamples and NumPy PCG64-style generator. Comparisons used the original exported per-row scores and the archived analysis results as the fixed expected values.

| Original archive | SHA-256 (external) | Methods × models | Pair universe | Numeric checks | Differences |
|---|---|---:|---|---:|---:|
| `completo-20261113T082301Z-1-001.zip` (Test C, C-sel-8) | `da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed` | 38 | 800 synthetic + 399 natural | **508** | **0** |
| `testM_A_risultati_completo.zip` (Test M notebook A) | `5f2922d73d3f8921600d082c92201975faea97cf3d078ab49e6ec51565661cbc` | 23 | 800 P−S and 800 S−S | **400 scalar comparisons** | **0** |
| `testM_B_risultati_completo.zip` (Test M notebook B) | `a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a` | 8 | 800 P−S and 800 S−S | **176** | **0** |

The 684 previously checked statistic groups (Test C + Test M notebook B) span W, paired ΔW, per-family W/ΔW, source-specific p(UNKNOWN) baselines, 95% CIs, and Test C's RIM difference; the natural dataset comparisons are descriptive with no CI, per the original protocol.

**Test M notebook A:** 400 individual scalar fields, including point estimates and the two bounds of each 95% CI, match an independent local replay from the uploaded original ZIP. The archived scores cover 23 method/model combinations and nine reference environments. The committed CLI `--kind M-A` adds coverage and identity checks; it was run on the real archive on 14 November 2026 (below). These scalar comparisons are not directly additive to the earlier *metric-group* counts.

**Important distinction:** the stored numeric tables were *verification targets*, **not** substitutes for source scores. This does not show out-of-domain generalization or the quality of model-generated answers.

## Committed CLI run against the original archives (2026-11-14)

The committed replayer (`python -m indetbench.replay`, this branch) was executed directly on the original ZIP files, CPU only, Python 3.13, NumPy 2.5.3. Every run exited with code 0 (`passed: true`), i.e. zero differences from the archived targets.

| Archive | SHA-256 | `--kind` | Values checked | Differences |
|---|---|---|---:|---:|
| `completo_Drive_20261113.zip` (Test C, C-sel-8) | `da84d9bf…bbed` | C | 508 | 0 |
| `testC_completo_risultati.zip` (Test C, same results, other export) | `cc89298c…e1a3` | C | 508 | 0 |
| `testM_A_risultati_completo.zip` | `5f2922d7…1cbc` | M-A | 498 numeric values (116 metric groups) | 0 |
| `testM_B_risultati_completo.zip` | `a78cf5a0…bbea3a` | M-B | 176 | 0 |

The 498 values of the CLI (M-A) and the 400 scalar fields of the earlier independent check are two different counts of the same archive; both match. Boundary 1 below is therefore closed. Boundaries 2 (Tests U and U2) and 3 (HC4 reproducibility) were closed on 15 November 2026; see the table below. What remains open for HC4 is the correctness of the labels, not their reproducibility.

## Replays added on 2026-11-15 (published archives, CI)

Run with `python -m indetbench.replay <archive> --kind <kind>` on the archives in `research_originals/step2/outputs/`; `tests/test_original_archives.py` runs them on every change. Python 3.11, NumPy 2.x locally; CI on Python 3.10 and 3.12.

| Archive | SHA-256 | `--kind` | Values checked | Differences |
|---|---|---|---:|---:|
| `testU_risultati.zip` | `f47231eb…9b30` | U | 8,517 (`esiti.json` of 4 models and 4 `celle.csv`) | 0 |
| `testU2_risultati.zip` | `dbcd61fa…9433` | U2 | 1,319 (`esiti.json` of 4 models, `conferme`) | 0 |
| `completo_Drive_20261113.zip` | `da84d9bf…bbed` | C-HC4 | 44,969 (21,582 answer labels and details, category counts, HC4 of 38 results) | 0 |

The U and U2 replays are NumPy re-implementations of the analysis cells of the two notebooks, now in `research_originals/step2/notebooks/`. The bootstrap uses the same seed (20261108) and the same calls, so the intervals match to 1e-10, not only the point estimates; with another seed the replay reports differences (unit test). They do not re-run models: the SQuAD-detector fit of Test U, the tokenizer lengths and the 24-value GPU alignment of U2 cannot be recomputed from the scores.

## Run the proposed replay code

```bash
python -m pip install -e '.[replay]'
python -m indetbench.replay /path/to/completo-20261113T082301Z-1-001.zip --kind C --expected-sha256 da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed --json-out testC_parity.json
python -m indetbench.replay /path/to/testM_A_risultati_completo.zip --kind M-A --expected-sha256 5f2922d73d3f8921600d082c92201975faea97cf3d078ab49e6ec51565661cbc --json-out testM_A_parity.json
python -m indetbench.replay /path/to/testM_B_risultati_completo.zip --kind M-B --expected-sha256 a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a --json-out testM_B_parity.json
```

The replay command returns nonzero when a statistic differs from its archived target; an incorrect SHA-256 fails before analysis. It deliberately does not fetch/download any third-party model, dataset or probe.

## Boundaries and remaining work

1. Test M **notebook A**: closed on 2026-11-14 — the committed replayer was run directly on the original file (498 values, 0 differences; see table above).
2. Test U and Test U2: closed on 2026-11-15 (table above).
3. Test C **HC4**: reproducibility closed on 2026-11-15 — the frozen classifier gives the archived label for all 21,582 answers and the HC4 statistics follow (table above). Still open: whether the labels are right. The classifier agreed with the owner's blind classification of 100 answers in 0.680 of cases (threshold 0.90, kappa 0.619), so HC4 carries the protocol's warning; a second, independent human annotation has not been done. HC4 within C is also confounded with passage family.
4. Classification sample and natural-language semantic review were partly AI assisted; do not describe them as independently double-blind.
5. An optional first-token p(UNKNOWN) Hugging Face runner has been implemented and unit tested; a real-model inference smoke test with an immutable model SHA is still required.
6. A fresh run of the code committed to GitHub and CI validation should be captured before a v0.1 release; this table records local parity checks from the development process.

## Safeguards

- Frozen archive provenance must be checked by SHA-256.
- Different reference environments are not silently interchanged: M1 uses its own reference, M2/M3 use env_sirin, M4 uses its recorded reference.
- Missing B/C scores are never silently replaced by zero.
- No model weights or third-party implementations are committed. Since 15 November 2026 the original per-row outputs of Tests U, U2, M and C, including SQuAD 2.0-derived passages under CC BY-SA 4.0, are committed in `research_originals/step2/outputs/`; see [`THIRD_PARTY.md`](THIRD_PARTY.md).
