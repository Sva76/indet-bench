# Third-party terms and distribution boundaries

The original IndetBench material is **all rights reserved** (root `LICENSE`; no license granted for now). That notice covers original IndetBench material only and does not relicense any external dataset, model, tokenizer, adapter, library, copyrighted prompt, or publication.

| Component | Reported license | Publishing rule |
|---|---|---|
| LM-Polygraph | MIT | External optional integration; preserve license/notice if vendored |
| SIRIN, Obeso hallucination-probes | Apache-2.0 | External optional integration; preserve license/notice if vendored |
| Qwen3, Mistral Nemo | Apache-2.0 (model cards) | Download from model provider; pin model revisions |
| HuggingFaceTB/SmolLM2-360M-Instruct | Apache-2.0 (official model card) | Used only in opt-in CPU smoke at pinned SHA; no weights redistributed |
| OLMo-2 | Apache-2.0 declaration plus model-card considerations | Check exact card and training-output notes |
| Llama 3.1 | Meta Llama 3.1 Community License and Acceptable Use Policy | No weights redistributed; review output terms separately |
| SQuAD 2.0 | CC BY-SA 4.0 | No derived passage data shipped in initial source |
| TriviaQA, LongFact, additional checkpoints | Model/artifact-specific | Do not redistribute before exact license review |

All model runners should be opt-in and download from official sources under their own terms. If a noncommercial license (e.g. PolyForm) is adopted later, its patent clauses and third-party licensing merit legal review before publishing components touching proprietary patents.
