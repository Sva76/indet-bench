# Third-party components, licences and distribution boundaries

*Checked 15 November 2026. Model licences were checked against each model's Hugging Face model card. Library licences were checked against the package metadata or the repository's LICENSE file. Bibliographic references for every component are in [REFERENCES.bib](REFERENCES.bib).*

The PolyForm Noncommercial License 1.0.0 in [`LICENSE`](../LICENSE) and [`NOTICE`](../NOTICE) covers **original IndetBench material only**. It does not relicense, and cannot relicense, any third-party model, tokenizer, probe, dataset, library or publication. Each of those remains under its own terms, listed below.

This page records the terms declared by each provider. It is not legal advice.

## What this repository does and does not contain

**Not distributed:**

- model weights, tokenizers, adapters or probe weights;
- TriviaQA, LongFact or other third-party dataset rows (the TriviaQA rows were removed from the Test M notebook A archive; their licence is not checked here).

SQuAD 2.0 passages and questions **are** distributed since 15 November 2026, under CC BY-SA 4.0 (see below).

All models are downloaded at run time, by whoever runs the code, from the provider's official Hugging Face repository at a pinned revision, with `trust_remote_code=False`. Whoever runs the code accepts the model's licence and use policy; for gated models such as Gemma this happens on the model page before download.

**Distributed:**

- Numeric scores computed from model outputs (probabilities, W, intervals) in `results/` and `research_originals/`.
- Short generated answers, at most 8 generated tokens (for example "YES", "NO" or "UNKNOWN", sometimes followed by the start of an explanation), in the `generated` column of the `punteggi.csv` files under `results/`. These are model outputs, not original IndetBench material. See [Model outputs](#model-outputs) below.
- The original output archives of Tests U2, M and C in [`research_originals/step2/outputs/`](../research_originals/step2/outputs/README.md) (owner's decision, 15 November 2026): per-row scores, generated answers (including LM-Polygraph samples and natural-passage answers, longer than 8 tokens), logs, environment listings and the SIRIN probes trained in this project.
- Text derived from SQuAD 2.0, under **CC BY-SA 4.0** with attribution and a description of the changes: in those archives and in [`research_originals/step2/test_c_selection/righe_C.json.gz`](../research_originals/step2/test_c_selection/righe_C.json.gz). Exact list of files: [`research_originals/step2/outputs/README.md`](../research_originals/step2/outputs/README.md#licences-and-attribution).
- SQuAD 2.0 question IDs and Wikipedia article titles, also in one selection record, [`research_originals/step2/test_c_selection/Chiusura_selezione_DUE-nat_199_C-sel-8.md`](../research_originals/step2/test_c_selection/Chiusura_selezione_DUE-nat_199_C-sel-8.md). Attribution is given in the dataset table below.

## Models

| Model (Hugging Face ID) | Used for | Pinned revision | Licence declared on the model card | Gated |
|---|---|---|---|---|
| `Qwen/Qwen3-8B` | generator, Tests U/U2/M/C; positive control, 14 Nov run | `b968826d9c46` | Apache-2.0 | no |
| `Qwen/Qwen3-4B` | zero-shot judge (SIRIN M3) | `1cfa9a720891` | Apache-2.0 | no |
| `mistralai/Mistral-Nemo-Instruct-2407` | generator, Tests U/U2/M/C | `04d8a90549d2` | Apache-2.0 | no |
| `allenai/OLMo-2-1124-7B-Instruct` | generator, Tests U/U2/M/C | `470b1fba1ae0` | Apache-2.0 | no |
| `meta-llama/Llama-3.1-8B-Instruct` | generator, Tests U/U2/M/C; base model of the Obeso et al. probes | `0e9e39f249a1` | Llama 3.1 Community License and Acceptable Use Policy | yes (manual approval) |
| `google/gemma-2-9b-it` | new-model run, 14 Nov 2026 | `11c9b309abf7` | Gemma Terms of Use and Gemma Prohibited Use Policy | yes |
| `01-ai/Yi-1.5-9B-Chat` | new-model run, 14 Nov 2026 | `1a0fc698cf88` | Apache-2.0 (with a NOTICE file from 01.AI) | no |
| `tiiuae/Falcon3-7B-Instruct` | new-model run, 14 Nov 2026 | `1e57a0ecd176` | TII Falcon-LLM License 2.0 (`falcon-llm-license`) | no |
| `microsoft/phi-4` | new-model run, 14 Nov 2026 | `2db69c1c3e91` | MIT | no |
| `HuggingFaceTB/SmolLM2-360M-Instruct` | CPU smoke test and 240-pair study | `c15f933c7343` | Apache-2.0 | no |
| `HuggingFaceTB/SmolLM2-1.7B-Instruct` | 240-pair study (CPU) | `31b70e2e869a` | Apache-2.0 | no |
| `Qwen/Qwen2.5-0.5B-Instruct` | 240-pair study (CPU) | `7ae557604adf` | Apache-2.0 | no |
| `Qwen/Qwen2.5-1.5B-Instruct` | 240-pair study (CPU) | `989aa7980e4c` | Apache-2.0 | no |
| `allenai/OLMo-2-0425-1B-Instruct` | 240-pair study (CPU) | `48d788eca847` | Apache-2.0 | no |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 240-pair study (CPU) | `fe8a4ea1ffed` | Apache-2.0 | no |

The full 40-character revisions are in the sources named in [REFERENCES.md](REFERENCES.md#references-and-attribution). Revision checks for the models of the original experiments are logged in [`research_originals/hf_revisions_verified.json`](../research_originals/hf_revisions_verified.json).

### Notes on specific terms

- **Llama 3.1.** The licence's attribution and naming requirements apply when Llama Materials, or products or models that contain them, are distributed. This repository distributes neither. Anyone running the code must accept the licence and comply with the Acceptable Use Policy.
- **Gemma 2.** The Gemma Terms of Use impose notice and use-restriction obligations on distributions of Gemma or of Model Derivatives. This repository distributes neither. The Gemma Prohibited Use Policy applies to anyone who runs the model through this code.
- **Falcon 3.** The TII Falcon-LLM License 2.0 and its acceptable use policy apply to anyone who downloads and runs the model: <https://falconllm.tii.ae/falcon-terms-and-conditions.html>.
- **Yi-1.5.** The NOTICE file in the model repository asks for attribution in derivative works of the model. IndetBench does not distribute a derivative model. It acknowledges anyway that the results labelled Yi-1.5-9B-Chat were obtained with Yi-1.5-9B-Chat by 01.AI, used under the Apache License 2.0.
- **Apache-2.0 and MIT models.** No weights are redistributed, so no licence copy is required. The models are acknowledged in this table and cited in [REFERENCES.bib](REFERENCES.bib).

## Model outputs

Some files under `results/` contain text generated by the models above: the `generated` column of `punteggi.csv`, and the `parsed` column derived from it. The archives in `research_originals/step2/outputs/` contain more model outputs (generated answers, samples, judge and probe scores) from Qwen3-8B, Mistral-Nemo, OLMo-2, Llama-3.1-8B and Qwen3-4B.

- These outputs are **not original IndetBench material**, and the PolyForm licence does not apply to them.
- They are published only as part of the research record, so that the reported scores can be audited.
- Any use of them must follow the terms and use policies of the model that produced them, listed above.

## Methods and probes

| Component | Use | Licence (checked in the repository) | Redistributed |
|---|---|---|---|
| LM-Polygraph (`lm-polygraph==0.7.0`) | uncertainty estimators, Test M | MIT (Copyright © 2023 MBZUAI) | no, installed from PyPI |
| SIRIN (commit `ef3bed1`) | answerability probe and judges | Apache-2.0 | no, installed from GitHub |
| Hallucination probes, Obeso et al. (code `295450e`, weights `obalcells/hallucination-probes` at `db581ce2166d`) | linear and LoRA probes on Llama-3.1-8B | Apache-2.0 | no, downloaded at run time |

If any of these is ever vendored, its LICENSE and NOTICE files must be copied with it.

## Datasets

| Dataset | Use | Licence | Redistributed |
|---|---|---|---|
| SQuAD 2.0 (`rajpurkar/squad_v2`, revision `3ffb306f725f`) | probe training/positive control (Test M B); natural cases of Test C | CC BY-SA 4.0 | **Yes, since 15 Nov 2026**, adapted rows under CC BY-SA 4.0: the natural Test C cases (including the full selection `righe_C.json`) and the Test M SQuAD rows, inside `research_originals/step2/`. Source: Rajpurkar, Jia & Liang (2018), [SQuAD 2.0](https://rajpurkar.github.io/SQuAD-explorer/), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); changes and file list in [`research_originals/step2/outputs/README.md`](../research_originals/step2/outputs/README.md#licences-and-attribution) |
| TriviaQA, loaded through LM-Polygraph | M1 positive control | not checked here | no |
| `obalcells/longfact-annotations` (revision `949fd2f71b3e`) | M4 positive control | not declared in the dataset card | no |
| `obalcells/triviaqa-balanced` (revision `620117a4967f`) | M4 reserve control | not declared in the dataset card | no |

All benchmark items that the repository does publish were written for IndetBench:

- [`data/smol_stat_v01_frozen.jsonl`](../data/smol_stat_v01_frozen.jsonl);
- the frozen Test M and Test C synthetic sets in `research_originals/step2/frozen/`;
- the examples in `examples/`.

They are covered by the root licence.

The Test C generator ([`gen_testC.py`](../research_originals/step2/scripts/gen_testC.py)) uses three packages: `geonamescache` (MIT; data from [GeoNames](https://www.geonames.org/), CC BY 4.0), `faker` (MIT) and `english-words` (MIT; word lists *web2* and *GCIDE*). They serve **only to build an exclusion list**, so that the invented entity names never coincide with a real place, person or English word. No entry from these lists appears in the published data.

## Software libraries

| Library | Licence (package metadata) |
|---|---|
| PyTorch (`torch`) | BSD-3-Clause |
| Transformers | Apache-2.0 |
| Accelerate | Apache-2.0 |
| Tokenizers | Apache-2.0 |
| huggingface_hub | Apache-2.0 |
| Datasets | Apache-2.0 |
| NumPy | BSD-3-Clause (with bundled components under 0BSD, MIT, Zlib, CC0-1.0) |
| pandas | BSD-3-Clause |
| loguru | MIT |
| Bandit (CI security scan only) | Apache-2.0 |

All are installed from PyPI and none is vendored. All of these licences permit use alongside the PolyForm Noncommercial licence of the original code.

## Patents and legal review

The PolyForm Noncommercial licence includes a patent licence for the original IndetBench material only. It grants nothing for third-party components. Before any commercial use, or any distribution beyond this repository, have the third-party terms above reviewed by a lawyer.
