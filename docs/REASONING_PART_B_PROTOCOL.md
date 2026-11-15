# Part B protocol: p(UNKNOWN) in reasoning models (v1)

English version of `notebooks/Protocollo_parteB_reasoning_v1.md` (Italian). **Approved by Simona Vargiu on 15 Nov 2026, 14:11, with the 5 recommended choices of §7, before any part B data were collected.** Implementation notes: `notebooks/Note_reasoning_v1.md`. Notebook: `notebooks/IndetBench_reasoning_v1.ipynb` (R-notebook-1).

## 1. Question and status
**Question.** When the model reasons before answering, does p(UNKNOWN) still separate the C cases from the B cases on the 800 frozen prose pairs (set PN)? And does reasoning change the separation compared with the same model without reasoning?

**Status.** Results are **exploratory**, like the earlier parts: not an independent validation. A higher W with reasoning does not show that the method works better, and a lower one does not refute it. Every anomaly is classified into the four categories (model behaviour, technical problem, protocol limit, scientific evidence), saying whether the category is supported by the data or remains open.

## 2. The measurement problem
Without reasoning, p(UNKNOWN) is the probability of the first answer token. In a reasoning model the first token starts the reasoning, so that definition no longer makes sense. The answer comes after the reasoning is closed (`</think>`) and depends on what the model wrote before.

**Definition.** p(UNKNOWN) is the summed probability of the 6 UNKNOWN variants (same variants and same `token_label_ids` as before, no renormalisation) **at the first answer token after `</think>`**: the first token generated after `</think>` that is not only whitespace or newline. p(YES) and p(NO) are measured at the same point. The measure is **conditional on the sampled reasoning**; repeatability is therefore measured (§5.4).

## 3. Models
| Key | Model | Revision | Params | Licence | Comparison | Role |
|---|---|---|---|---|---|---|
| qwen3_8b | Qwen/Qwen3-8B, `enable_thinking=True` | b968826d9c46dd6066d109eabc6255188de91218 | 8B | Apache-2.0 | **same weights** without reasoning | **primary** |
| qwen3_32b | Qwen/Qwen3-32B, `enable_thinking=True` | 9216db5781bf21249d130ec9da846c4624c16137 | 33B | Apache-2.0 | **same weights** without reasoning (part A: W 0.975) | secondary |
| phi4_reasoning | microsoft/Phi-4-reasoning | 1de18ec97600877ce63dbf60c73b998da99f0195 | 14.7B | MIT | Phi-4 (14 Nov: W 0.944), same base, different training | descriptive |
| r1_llama_8b (optional) | deepseek-ai/DeepSeek-R1-Distill-Llama-8B | 6a6f4aa4197940add57724a7707d069478df56b1 | 8B | MIT; derived from Llama-3.1-8B-Base, so the Llama 3.1 Community License also applies | no fixed-model comparison | descriptive |

- Qwen3 is primary because reasoning on/off uses **the same weights**: the difference measures reasoning and nothing else. Known limit stated before the data: Qwen3 without reasoning already has W 0.975, so the comparison can show a decrease better than an increase.
- Phi-4-reasoning's template **always inserts a Microsoft system message** asking for a reasoning section and a "Solution" section. It is used as is and declared. Stated risk: the Solution may not start with YES/NO/UNKNOWN, and then the mass rule (§5.2) would make it NOT MEASURABLE.
- Excluded: QwQ-32B and DeepSeek-R1-Distill-Qwen-32B (same Qwen family, no extra fixed-weight comparison); reasoning models above 32B (do not fit an A100 in bf16).

## 4. Generation
| Item | Choice | Reason |
|---|---|---|
| Prompt | the frozen prompts, user message only (plus Phi-4-reasoning's fixed template system message) | identity with earlier parts |
| Decoding | **sampling with the authors' parameters**: Qwen3 temperature 0.6, top-p 0.95, top-k 20, min-p 0; Phi-4-reasoning 0.8, 0.95, 50; R1 0.6, 0.95 | Qwen explicitly advises against greedy decoding in thinking mode (degradation, endless repetition); Phi-4-reasoning requires sampling |
| Seed | fixed, 20261108, recorded with the batch composition | reproducibility in the same session and environment |
| Reasoning budget | **4096 tokens** | stories are short; the recommended full budget (32 768) would make the full run too long |
| Reasoning that does not close | the notebook appends `\n</think>\n\n` and measures the next token; the row is flagged `troncata` | the measure stays defined; truncation is recorded and analysed separately |
| Answer after reasoning | up to 16 tokens after `</think>`, read with the same `parse_label` | same answer reading as before |
| Precision | bfloat16 for all | as in part A |
| Batch and attention | **batch 16, left padding, sdpa attention** | with batch 1 and eager, thousands of tokens per row do not fit a session |
| No-reasoning condition | for Qwen3-8B and 32B, re-measured **in the same pipeline** (same batch and attention, `enable_thinking=False`, greedy, 8 tokens as in Test U2) | the on/off comparison uses the same technical settings |
| Saved texts | full reasoning and answer for every row | for checking anomalies; not used in the measures |

## 5. Rules fixed before the data
### 5.1 Technical checks
1. Revision, template and labels checked as in part A; the template must not insert the date.
2. **Batch pipeline check.** With reasoning off, the batch-16 + sdpa pipeline must reproduce the 24 archived Qwen3-8B values of Test U2: max difference ≤ 0.01 and 24/24 equal answers (looser than part A's 1e-3 because batch and attention change rounding). If it fails, the full run does not start.
3. The CPU check of the 4 Test U2 W values remains mandatory before the full run.

### 5.2 Measurability
- **Mass rule (from v4):** if the median YES+NO+UNKNOWN mass at the first answer token is < 0.5, the model is **NOT MEASURABLE (technical reason)**; checked first on the 24 control rows, then on the full set.
- **Truncations:** a pair is "closed" if both B and C closed their reasoning by themselves within the budget. With at least 760 closed pairs, the main analysis uses all 800 pairs and the sensitivity analysis only closed pairs. With fewer than 760, the model's result is **descriptive only**, with the distribution of truncations by family, variant and position.

### 5.3 Hypotheses and criteria
- **HR1 (each model):** same HU1/HI1 rule with reasoning on (W ≥ 0.60 and lower 95% bound > 0.5). The binding competence gate applies (B accuracy ≥ 0.50, overall and per gold label, from the answer after reasoning).
- **HR2 (Qwen3-8B primary, Qwen3-32B secondary):** ΔW = W on − W off, paired by story, 95% bootstrap interval (2000 story resamples, seed 20261108). "Reasoning changes W" only if the interval excludes 0. No improvement threshold: it is not a superiority test.
- **Descriptive:** Phi-4-reasoning (vs Phi-4 of 14 Nov) and R1-Distill (no comparison); answers changed between on and off on B and C; B accuracy by gold label.

### 5.4 Baselines and repeatability
- Baselines from the same outputs (descriptive): normalised entropy, minus normalised max probability, UNKNOWN answer 0/1, normalised p(UNKNOWN) (with the 14 Nov note), **reasoning length in tokens** (new) and truncated reasoning 0/1. The "a baseline equals or beats p(UNKNOWN)" flag uses the independent baselines, reasoning length included.
- **Repeatability:** on the first 20 stories (80 pairs) inference is repeated with two more seeds; W per seed and the share of equal answers are reported (descriptive).

### 5.5 Not measured
p(UNKNOWN) during the reasoning is not measured: there is no single definition of where to measure, and choosing one after seeing the texts would be a data-driven choice. The texts are saved; an analysis of the reasoning would be a separate test with its own protocol.

## 6. Test run and full run
- **Test run:** 10 stories (40 pairs, 80 rows) for Qwen3-8B with reasoning on and off; measures real times, mean reasoning length, truncation share and the pipeline check (§5.1).
- **Estimated times (not measured):** with ~1000 reasoning tokens on average, Qwen3-8B 1–2 h, Phi-4-reasoning 2–3 h, Qwen3-32B 4–6 h, plus the off condition and repeatability.
- **Environment:** A100-SXM4-80GB, HF_TOKEN and GH_TOKEN as Colab secrets, outputs in Drive with checkpoint resume.

## 7. Owner's decisions (15 Nov, 14:11: all 5 as recommended)
1. **Models:** Qwen3-8B (primary), Qwen3-32B and Phi-4-reasoning; R1-Distill-Llama-8B optional.
2. **Decoding:** sampling with the authors' parameters plus repeatability on 20 stories (greedy would be deterministic but against Qwen's and Microsoft's instructions).
3. **Budget:** 4096 tokens with recorded forced closure.
4. **Pipeline:** batch 16 + sdpa, with the 0.01 check and the off condition re-measured in the same pipeline.
5. **Phi-4-reasoning:** if the mass rule makes it NOT MEASURABLE because the Solution does not start with a label, the result stays NOT MEASURABLE; no alternative measure is defined for one model.
