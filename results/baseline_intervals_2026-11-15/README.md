# Intervals for the output baselines (15 November 2026, post hoc)

**This analysis was added after the results were known. It was not preregistered and changes no verdict.** The new-model and larger-model reports gave the generic baselines as point estimates only. This table adds 95% intervals to them, plus the paired difference from p(UNKNOWN).

- Input: the published `punteggi.csv` of [`results/new_models_2026-11-14/`](../new_models_2026-11-14/) and [`results/larger_models_2026-11-15/`](../larger_models_2026-11-15/). No new inference.
- Baselines, as defined in the notebooks: entropy and minus the maximum of (p_yes, p_no, p_unknown) renormalised to sum 1; `unknown01` = 1 if the generated answer is UNKNOWN.
- W with a 95% story bootstrap; `dW_punknown_minus_baseline` = W(p(UNKNOWN)) − W(baseline), with the 200 stories resampled jointly. Positive favours p(UNKNOWN). 2000 resamples, seed 20261108, bootstrap of `indetbench.metrics`. The notebooks used a numpy bootstrap, so intervals can differ by a few thousandths; the point estimates are identical, and a unit test checks them against `riepilogo.csv`.
- No correction for multiple comparisons (11 model rows × 3 baselines).
- Yi-1.5-9B-Chat is listed for completeness but is NOT EVALUABLE (technical; owner decision of 14 November 2026). The Qwen3-8B positive control appears once per run.

Reproduce: `python results/baseline_intervals_2026-11-15/compute.py` (writes `baseline_intervals.csv`); `tests/test_baseline_intervals.py` recomputes the whole table.

## Reading (descriptive)

Difference from the best of entropy and −p max, with its 95% interval:

| Model | ΔW p(UNKNOWN) − baseline [95% CI] | Interval |
|---|---|---|
| Qwen3-32B | +0.085 [+0.062, +0.107] | above 0 |
| Gemma-2-27B-it | +0.051 [+0.026, +0.077] | above 0 |
| Falcon3-7B-Instruct | +0.031 [+0.005, +0.058] | above 0 |
| Qwen3-8B (control) | +0.026 [+0.011, +0.041] | above 0 |
| Phi-4 | −0.000 [−0.018, +0.019] | includes 0 (inconclusive) |
| OLMo-2-0325-32B-Instruct | −0.034 [−0.051, −0.018] | below 0 |
| Gemma-2-9B-it | −0.074 [−0.100, −0.049] | below 0 |
| Llama-3.3-70B-Instruct (nf4) | −0.080 [−0.099, −0.061] | below 0 |

The split already described in the reports holds with intervals: p(UNKNOWN) ranks C above B better than generic answer uncertainty in four models, worse in three, and with an inconclusive difference in one (Phi-4: the interval includes 0, which does not show equality). These data therefore do not show that p(UNKNOWN) carries information specific to indeterminacy. Against the generated answer (`unknown01`), p(UNKNOWN) is higher in every model, because many C cases get a YES or NO answer: the generated answer is UNKNOWN on 19–55% of the C cases in the evaluable models (see [`docs/PROTOCOL.md`](../../docs/PROTOCOL.md#6-what-w-does-not-measure)).
