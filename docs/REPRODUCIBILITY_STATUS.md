# Archived-results reproducibility — Step 3 progress

**Status:** CPU replay implemented for Test C and Test M notebook B. These are *not* new model experiments. Source archives are NOT redistributed.

## Evidence from local replay against original archives

The first local implementation recalculated individual B/C pair wins (ties = 0.5), aggregated by story/passage, and then computed paired ΔW using common valid pairs. Bootstrap confidence intervals used the frozen seed 20261108, 2,000 resamples and NumPy PCG64-style generator. Comparisons used the original exported per-row scores and the archived analysis results as the fixed expected values.

| Original archive | SHA-256 (external) | Methods × models | Pair universe | Numeric checks | Differences |
|---|---|---:|---|---:|---:|
| `completo-20261113T082301Z-1-001.zip` (Test C, C-sel-8) | `da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed` | 38 | 800 synthetic + 399 natural | **508** | **0** |
| `testM_B_risultati_completo.zip` (Test M notebook B) | `a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a` | 8 | 800 P−S and 800 S−S | **176** | **0** |

The 684 checks span W, paired ΔW, per-family W/ΔW, source-specific p(UNKNOWN) baselines, 95% CIs, and Test C's RIM difference; the natural dataset comparisons are descriptive with no CI, per the original protocol.

**Important distinction:** the stored numeric tables were *verification targets*, **not** substitutes for source scores. This does not show out-of-domain generalization or the quality of model-generated answers.

## Run the proposed replay code

```bash
python -m pip install -e '.[replay]'
python -m indetbench.replay /path/to/completo-20261113T082301Z-1-001.zip --kind C --expected-sha256 da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed --json-out testC_parity.json
python -m indetbench.replay /path/to/testM_B_risultati_completo.zip --kind M-B --expected-sha256 a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a --json-out testM_B_parity.json
```

The replay command returns nonzero when a statistic differs from its archived target; an incorrect SHA-256 fails before analysis. It deliberately does not fetch/download any third-party model, dataset or probe.

## Boundaries and remaining work

1. Test M **notebook A**: archived ZIP has been identified, but raw-byte access is not yet available to this development session; full M parity is not yet claimed.
2. Test U and Test U2: numeric replay is not part of the current implementation.
3. Test C **HC4**: response labels and classifier agreement require separate analysis. No HC4 revalidation is implied by W and ΔW parity.
4. Classification sample and natural-language semantic review were partly AI assisted; do not describe them as independently double-blind.
5. Installation and execution on completely new language models, including an optional first-token p(UNKNOWN) runner, is a future deliverable; CSV-import and archival replay do not yet provide that functionality.
6. A fresh run of the code committed to GitHub and CI validation should be captured before a v0.1 release; this table records local parity checks from the development process.

## Safeguards

- Frozen archive provenance must be checked by SHA-256.
- Different reference environments are not silently interchanged: M1 uses its own reference, M2/M3 use env_sirin, M4 uses its recorded reference.
- Missing B/C scores are never silently replaced by zero.
- No model weights, raw SQuAD passages, original per-row research outputs, or third-party implementations are committed.
