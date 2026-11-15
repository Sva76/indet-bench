# Original Step 2 output archives (Tests U, U2, M, C)

Published on 15 November 2026 by decision of the owner. These are the complete results archives exported from the original Colab runs. Four are byte-identical to the originals; one (Test M notebook A) has a single third-party file removed (see below).

| File | Test | SHA-256 | Original archive |
|---|---|---|---|
| `testU_risultati.zip` | U (4 models, sets ADD/V1/V2/V3, screening SCR, lexical "or" control O; 36,480 rows) | `f47231eb89d129b1488d1c23e421c3b4a4492ad122fbbbe5057ef457d9230b39` | identical |
| `testU2_risultati.zip` | U2 (4 models, 4 formats, 38,400 rows) | `dbcd61faa7ba0b6bdade866fc8d130eb21d4a6d7c471e9e2c9a7b8537d999433` | identical |
| `testM_A_risultati_completo_senza_triviaqa.zip` | M, notebook A (M1, M3, M4, references) | `fa9577bea44135e06f4583dc80fb9400929dde240063c7a9e5918eb66016e033` | `testM_A_risultati_completo.zip`, `5f2922d73d3f8921600d082c92201975faea97cf3d078ab49e6ec51565661cbc`, minus `dati/triviaqa.json`; the other 51 members are copied byte for byte |
| `testM_B_risultati_completo.zip` | M, notebook B (M2, SIRIN probe) | `a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a` | identical |
| `completo_Drive_20261113.zip` | C (C-sel-8, notebook C-3; contains `testC_completo_risultati.zip`, `cc89298c…`) | `da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed` | identical |

The full Test C selection, `dati/righe_C.json` from `testC_selezione.zip` (2,478 rows, SHA-256 `4586e18f4e589505b63699ac91117a927d8bdfc965506a4e3d73920e2e6b0b42`), is in [`../test_c_selection/righe_C.json.gz`](../test_c_selection/righe_C.json.gz) (gzip of the unchanged bytes).

## Check them

```bash
python -m pip install -e '.[replay]'
python -m indetbench.replay research_originals/step2/outputs/testU_risultati.zip --kind U \
    --expected-sha256 f47231eb89d129b1488d1c23e421c3b4a4492ad122fbbbe5057ef457d9230b39
python -m indetbench.replay research_originals/step2/outputs/testU2_risultati.zip --kind U2 \
    --expected-sha256 dbcd61faa7ba0b6bdade866fc8d130eb21d4a6d7c471e9e2c9a7b8537d999433
python -m indetbench.replay research_originals/step2/outputs/completo_Drive_20261113.zip --kind C \
    --expected-sha256 da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed
python -m indetbench.replay research_originals/step2/outputs/completo_Drive_20261113.zip --kind C-HC4 \
    --expected-sha256 da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed
python -m indetbench.replay research_originals/step2/outputs/testM_A_risultati_completo_senza_triviaqa.zip --kind M-A \
    --expected-sha256 fa9577bea44135e06f4583dc80fb9400929dde240063c7a9e5918eb66016e033
python -m indetbench.replay research_originals/step2/outputs/testM_B_risultati_completo.zip --kind M-B \
    --expected-sha256 a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a
```

All pass with 0 differences: U 8,517 values, U2 1,319, C 508, C-HC4 44,969, M-A 498 (also on the archive without `triviaqa.json`), M-B 176. `tests/test_original_archives.py` runs these replays in CI and checks every SHA-256.

What each replay covers:

- **U** (`indetbench/replay_u.py`, re-implementation of the analysis of [`TestU_astensione_4_modelli_v3.ipynb`](../notebooks/TestU_astensione_4_modelli_v3.ipynb)): for the four models, every value of `benchmark` (HU1 with W, intervals, permutation p, AUROC, behaviour tables), `soglia` (HU2 with the joint bootstrap of the threshold), `soglie_descrittive`, `controllo_or` (HO1, HO2 and descriptive comparisons, from the archived SQuAD-detector scores), `or_generazione`, `screening` and the polarity decision, `quota_massa_bassa`, every row of each `celle.csv`, and `sintesi`. Not recomputable from the scores: the fit and AUROC of the SQuAD detector, the tokenizer lengths behind `scarti_prompt` (all 0), software metadata. The polarity hold-out did not run in the original (no candidate reached 0.90).
- **U2** (`indetbench/replay_u2.py`, analysis of [`TestU2_istruzione_4_modelli_v2.ipynb`](../notebooks/TestU2_istruzione_4_modelli_v2.ipynb)): for the four models, the four conditions (W, AUROC, W at equal answer, alternative measures, behaviour), HI1, HI2, HI3, the descriptive contrasts, the P+S alignment with Test U, the low-mass share, and `conferme`. Not recomputable: the 24 GPU re-runs of the alignment check, `scarti_prompt`.
- **C-HC4** (`indetbench/replay_c_hc4.py`): the frozen answer classifier of the run (`tc_classifica.py`, rules C-classifica-2, vendored byte for byte as `indetbench/tc_classifica_frozen.py`, checked against the copy in the archive) is re-run on all 21,582 archived answers (M1 reference and LM-Polygraph answers of four models, M4 answers of Llama): labels and details equal `risposte_C.csv`, category counts and B accuracies equal `esiti_C.json`. From these labels and the archived scores, the five HC4 sets of all 38 method/model results (AUROC, passage-bootstrap interval, counts, verdict) are recomputed. This shows that HC4 follows from the archived answers, rules and scores; it does not show that the rules label the answers correctly. The classifier agreed with the owner's blind classification of 100 answers in 0.680 of cases (Cohen's kappa 0.619, protocol threshold 0.90; 0.770 on the supported / unsupported / excluded class used by HC4); The owner's 100 labels (categories only, without her notes) are published in [`../test_c_controls/etichette_Simona_campione_C.csv`](../test_c_controls/etichette_Simona_campione_C.csv) (owner's decision, 15 November 2026); `--annotations` on that file recomputes this agreement (unit test). HC4 within C is also confounded with passage family (independent review of 13 November).

## What was removed, and why

`dati/triviaqa.json` (400 TriviaQA questions with answer aliases, used for the M1 positive control HM0) was removed from the notebook A archive because TriviaQA declares no licence: on 15 November 2026 neither the official page ([nlp.cs.washington.edu/triviaqa](https://nlp.cs.washington.edu/triviaqa/)) nor the Hugging Face card of `mandarjoshi/trivia_qa` names one (card licence field: unknown), and the page states that the University of Washington does not own the copyright of the questions and documents ([THIRD_PARTY.md](../../../docs/THIRD_PARTY.md)). The HM0 results on TriviaQA remain in `esiti_A.json`, and the model answers to those questions remain in `uscite/M1_*.json` (identified by `row_id` only); recomputing HM0 needs the TriviaQA rows, which can be obtained from the source: `mandarjoshi/trivia_qa`, config `rc.nocontext`, split `validation`, 400 indices drawn with `np.sort(np.random.default_rng(20261110).choice(len(split), 400, replace=False))`, as in `TestM_A_metodi_v8.ipynb`. The dataset revision was not pinned in that notebook, so a later copy of the source could differ; the `TQ|question_id` identifiers kept in `uscite/M1_*.json` allow the selection to be checked.

## Licences and attribution

These archives mix material under different terms:

- **IndetBench original material** (synthetic stories and prompts, scripts' configuration, reports, statistics, the owner's classification sample; the Test U and U2 archives contain only this and model outputs): PolyForm Noncommercial 1.0.0, © 2026 Simona Vargiu ([LICENSE](../../../LICENSE), [NOTICE](../../../NOTICE)).
- **Text derived from SQuAD 2.0** — passages, questions and answers of the natural Test C cases (natural rows in `dati/righe.json`, `risposte_C.csv`, `confronto_M1_riferimento.csv` and the M1 outputs of the Test C archive, and in `dati/righe.json`, `dati/righe_C_selezionate.json` and `dati/passaggi_selezionati.json` of the nested `testC_completo_risultati.zip`; natural rows of `righe_C.json`), the SQuAD probe-training and control rows of Test M (`dati/squad.json`, `dati/m2_dati.json`, `uscite/M2_dati-*/M2_dati.json`, the `squad` controls inside `uscite/M1_*.json`): **CC BY-SA 4.0**. Source: Rajpurkar, P., Jia, R. & Liang, P. (2018), *Know What You Don't Know: Unanswerable Questions for SQuAD*, ACL; dataset [SQuAD 2.0](https://rajpurkar.github.io/SQuAD-explorer/) (Hugging Face `rajpurkar/squad_v2`, revision `3ffb306f725f`), licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Changes were made: selection, shortening at word or sentence boundaries, construction of B/C variants with distractors, and embedding in prompts, as described in the Test M note (`../protocols/Nota_M2_configurazione_v2_2.md`) and the Test C protocol (`../protocols/Protocollo_testC_v3.md`, §3.3c). These adapted rows are distributed under CC BY-SA 4.0; the PolyForm licence does not apply to them.
- **Model outputs** (generated text, probabilities, probe scores): not original IndetBench material; use follows the terms of the model that produced them (Qwen3, Mistral-Nemo, OLMo-2: Apache 2.0; Llama-3.1-8B-Instruct: Llama 3.1 Community License and Acceptable Use Policy; Qwen3-4B judge: Apache 2.0). See [THIRD_PARTY.md](../../../docs/THIRD_PARTY.md).
- `uscite/M2_*/sonda*/` in the notebook B archive are SIRIN probes trained in this project (SIRIN code: Apache 2.0); the Obeso et al. probe weights are not included.
- Logs and environment listings contain Colab and Google Drive paths of the original runs and the package versions installed there.
