# Original Step 2 output archives (Tests U2, M, C)

Published on 15 November 2026 by decision of the owner. These are the complete results archives exported from the original Colab runs. Three are byte-identical to the originals; one (Test M notebook A) has a single third-party file removed (see below).

| File | Test | SHA-256 | Original archive |
|---|---|---|---|
| `testU2_risultati.zip` | U2 (4 models, 4 formats, 38,400 rows) | `dbcd61faa7ba0b6bdade866fc8d130eb21d4a6d7c471e9e2c9a7b8537d999433` | identical |
| `testM_A_risultati_completo_senza_triviaqa.zip` | M, notebook A (M1, M3, M4, references) | `fa9577bea44135e06f4583dc80fb9400929dde240063c7a9e5918eb66016e033` | `testM_A_risultati_completo.zip`, `5f2922d73d3f8921600d082c92201975faea97cf3d078ab49e6ec51565661cbc`, minus `dati/triviaqa.json`; the other 51 members are copied byte for byte |
| `testM_B_risultati_completo.zip` | M, notebook B (M2, SIRIN probe) | `a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a` | identical |
| `completo_Drive_20261113.zip` | C (C-sel-8, notebook C-3; contains `testC_completo_risultati.zip`, `cc89298c…`) | `da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed` | identical |

The full Test C selection, `dati/righe_C.json` from `testC_selezione.zip` (2,478 rows, SHA-256 `4586e18f4e589505b63699ac91117a927d8bdfc965506a4e3d73920e2e6b0b42`), is in [`../test_c_selection/righe_C.json.gz`](../test_c_selection/righe_C.json.gz) (gzip of the unchanged bytes).

## Check them

```bash
python -m pip install -e '.[replay]'
python -m indetbench.replay research_originals/step2/outputs/completo_Drive_20261113.zip --kind C \
    --expected-sha256 da84d9bfb81df8ef15c39524b9e507ffa13eb1e563ce18715b432a1638b5bbed
python -m indetbench.replay research_originals/step2/outputs/testM_A_risultati_completo_senza_triviaqa.zip --kind M-A \
    --expected-sha256 fa9577bea44135e06f4583dc80fb9400929dde240063c7a9e5918eb66016e033
python -m indetbench.replay research_originals/step2/outputs/testM_B_risultati_completo.zip --kind M-B \
    --expected-sha256 a78cf5a02566d22de80acf8fff6caff0fa0049c697abbbf27667b807648cea3a
```

All three pass with 0 differences (C 508 values, M-A 498, M-B 176), also on the M-A archive without `triviaqa.json`. `tests/test_original_archives.py` runs these replays in CI, checks every SHA-256, and recomputes the Test U2 HI1 W on set PN for the four models from `punteggi.csv` (equal to the archived estimates). A full replay of Test U and of all U2 hypotheses is not implemented; HC4 (answer classification in Test C) is not revalidated.

## What was removed, and why

`dati/triviaqa.json` (400 TriviaQA questions with answer aliases, used for the M1 positive control HM0) was removed from the notebook A archive because the TriviaQA licence has not been checked ([THIRD_PARTY.md](../../../docs/THIRD_PARTY.md)). The HM0 results on TriviaQA remain in `esiti_A.json`, and the model answers to those questions remain in `uscite/M1_*.json` (identified by `row_id` only); recomputing HM0 needs the TriviaQA rows, which can be obtained from the source.

## Licences and attribution

These archives mix material under different terms:

- **IndetBench original material** (synthetic stories and prompts, scripts' configuration, reports, statistics, the owner's classification sample): PolyForm Noncommercial 1.0.0, © 2026 Simona Vargiu ([LICENSE](../../../LICENSE), [NOTICE](../../../NOTICE)).
- **Text derived from SQuAD 2.0** — passages, questions and answers of the natural Test C cases (natural rows in `dati/righe.json`, `risposte_C.csv`, `confronto_M1_riferimento.csv` and the M1 outputs of the Test C archive, and in `dati/righe.json`, `dati/righe_C_selezionate.json` and `dati/passaggi_selezionati.json` of the nested `testC_completo_risultati.zip`; natural rows of `righe_C.json`), the SQuAD probe-training and control rows of Test M (`dati/squad.json`, `dati/m2_dati.json`, `uscite/M2_dati-*/M2_dati.json`, the `squad` controls inside `uscite/M1_*.json`): **CC BY-SA 4.0**. Source: Rajpurkar, P., Jia, R. & Liang, P. (2018), *Know What You Don't Know: Unanswerable Questions for SQuAD*, ACL; dataset [SQuAD 2.0](https://rajpurkar.github.io/SQuAD-explorer/) (Hugging Face `rajpurkar/squad_v2`, revision `3ffb306f725f`), licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Changes were made: selection, shortening at word or sentence boundaries, construction of B/C variants with distractors, and embedding in prompts, as described in the Test M note (`../protocols/Nota_M2_configurazione_v2_2.md`) and the Test C protocol (`../protocols/Protocollo_testC_v3.md`, §3.3c). These adapted rows are distributed under CC BY-SA 4.0; the PolyForm licence does not apply to them.
- **Model outputs** (generated text, probabilities, probe scores): not original IndetBench material; use follows the terms of the model that produced them (Qwen3, Mistral-Nemo, OLMo-2: Apache 2.0; Llama-3.1-8B-Instruct: Llama 3.1 Community License and Acceptable Use Policy; Qwen3-4B judge: Apache 2.0). See [THIRD_PARTY.md](../../../docs/THIRD_PARTY.md).
- `uscite/M2_*/sonda*/` in the notebook B archive are SIRIN probes trained in this project (SIRIN code: Apache 2.0); the Obeso et al. probe weights are not included.
- Logs and environment listings contain Colab and Google Drive paths of the original runs and the package versions installed there.
