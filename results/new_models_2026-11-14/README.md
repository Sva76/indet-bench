# New-model run, 14 November 2026 (exploratory)

Archived output of `notebooks/IndetBench_modelli_nuovi_v3.ipynb` (N-notebook-3), mode *completo*, on the frozen prose benchmark (set PN, 800 B/C pairs). Report: [`docs/NEW_MODELS_RESULTS_2026-11-14.md`](../../docs/NEW_MODELS_RESULTS_2026-11-14.md); owner-approved Italian original: [`Risultati_modelli_nuovi_v1.md`](Risultati_modelli_nuovi_v1.md).

- One folder per model (`<key>-<fingerprint>/`): `punteggi.csv` (per-row scores: p_yes, p_no, p_unknown, label mass, generated and parsed answer), `esito.json` (full report, including `report_indetbench`), `manifest.json` (model, revision, GPU, package versions, commit), `anomalie.csv`, `scarti_lunghezza.csv`.
- `riepilogo.csv/json`, `rapporto.txt`: summary as produced by the notebook (Italian). `controllo_cpu_testU2.json`: CPU check of the four Test U2 values.
- `ricalcolo_completo_originale.py`: the independent pandas recomputation used for the approved report, kept as run (paths refer to the project workspace, not to this repository).
- The notebook's `esito` field says CONFIRMED for Yi-1.5-9B-Chat; **the owner classified Yi as NOT EVALUABLE for a technical reason** (label mass ≈ 2·10⁻⁶ at the first token). The file is kept unchanged.
- Not included: per-shard checkpoints and the nested ZIPs (same content). Source archive `indetbench_modelli_nuovi_completo_20261114.zip`, SHA-256 `65d44bb53bdbb2c6e6d8ecc6cb82b9250cae405f82f2127b0f04bfd05dc9260c` (held by the owner).
- Integrity: `SHA256SUMS`; `tests/test_new_models_results.py` recomputes W, intervals, gate and verdict from `punteggi.csv`.
- Model licences: Gemma Terms of Use (Gemma-2-9B-it), Apache 2.0 (Yi-1.5-9B-Chat, Qwen3-8B), TII Falcon-LLM License 2.0 (Falcon3-7B-Instruct), MIT (Phi-4). Only scores and short generated answers are stored here, no weights; the generated text is not covered by the repository licence (see [`docs/THIRD_PARTY.md`](../../docs/THIRD_PARTY.md#model-outputs)).

## Timeline (what can be checked)
- 2026-11-14 07:19:48 UTC, commit `0e31a81`: competence gate (B accuracy ≥ 0.50) added; 07:30:16 UTC, commit `c086e65`: per-label parts added.
- Every `manifest.json` of this run records `repo_commit` `c086e65…`, so the run used the code with the complete gate already fixed. The notebook version `N-notebook-3` was committed in `617b5b5` (14:41:01 UTC).
- The manifests carry no run timestamp, and the file times inside the Drive archive have no time zone, so the exact run time is not stated here. The report was approved by the owner on 14 November 2026 and archived in commit `18b141d` (21:17 UTC).
