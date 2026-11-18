# IndetBench v2: generator specification (DRAFT)

*Status: draft for owner review, 18 November 2026. Not frozen, not preregistered, no model has been run on v2 data.*

**Author and owner:** Simona Vargiu (principal investigator). The research question, the B/C determinability design and the decision to build a graded v2 set are hers; she approved the outline of this specification on 18 November 2026. The text and the code were drafted with AI assistance (Claude Opus 5.5) at her request, as recorded in [AI_USAGE.md](AI_USAGE.md). Every point in §8 is an open decision that belongs to her.

**Licence:** original IndetBench material, © 2026 Simona Vargiu, under the [PolyForm Noncommercial License 1.0.0](../LICENSE) with the [required notice](../NOTICE). Code: [`src/indetbench/gen_v2.py`](../src/indetbench/gen_v2.py). Tests: [`tests/test_gen_v2.py`](../tests/test_gen_v2.py).

The v1 benchmark is not changed by any of this. The 800 frozen pairs, their SHA-256, the results and the archives stay as they are; v2 is a separate set.

## 1. Purpose

v2 asks **up to what logical complexity a model recognises that the answer is not determined, and how often it actually abstains.** v1 answers this for one level of difficulty, and that level is already saturated at 8B parameters (W of p(UNKNOWN): Qwen3-8B 0.975, Qwen3-32B 0.975, reasoning models up to 1.000).

v2 addresses two limits of v1:

- **Narrow task.** v1 has one question, three logical templates and two variables. B's answer depends only on the family (AND always NO, OR and IMPLIES always YES), and counting "It is true" separates B from C perfectly within every family × variant cell (W = 1.0 or 0.0); the overall 0.5 comes only from counterbalancing.
- **Frontier models excluded.** p(UNKNOWN) needs token probabilities, which frontier APIs do not return ([Protocol §2](PROTOCOL.md#2-reference-score-punknown)).

## 2. What stays the same (invariants)

1. **Minimal pairs.** B and C differ in exactly one word, the truth value (`true` / `false`) of one stated fact. Same number of words, same uncertain lines, same rules, same order of facts. Checked by `audit()` and by `test_minimal_pairs`.
2. **Gold labels from a solver.** B is determined (YES or NO) for every value of the uncertain facts; C is not (UNKNOWN). No label comes from a person or a model.
3. **Prompt format.** A single-word answer, YES, NO or UNKNOWN, on the first line, as in v1. The instruction says "rules" instead of "policy" because v2 has several rules.
4. **Metric and statistics.** W as in [Protocol §4](PROTOCOL.md#4-the-metric-w): ties count one half, averaged within stories, story-level bootstrap. A story is one rule set, so it is the bootstrap block.
5. **Same runner.** The pair file is JSON Lines with `row_id`, `pair_id`, `block_id`, `side` and `prompt`, so `indetbench.hf_runner` reads it unchanged.

## 3. Difficulty and variety

**Difficulty knobs.** Each level fixes four knobs:

| Level | Rule variables | Chain depth (rules) | Uncertain facts | Distractor facts |
|---|---|---|---|---|
| 1 | 2 | 1 | 1 | 1 |
| 2 | 3 | 1 | 1 | 2 |
| 3 | 3 | 2 | 1 | 3 |
| 4 | 4 | 2 | 2 | 4 |
| 5 | 5 | 3 | 2 | 6 |

Level 1 is the v1 configuration, with the new variety below. In a chain, each rule defines an intermediate condition (for example "the permit is valid") that the next rule uses; intermediate conditions are never stated as facts.

**Variety at every level:**

- **Operators:** "both … and …" / "all of these hold", "at least one of these holds", "exactly one of these holds", "not all of these hold", and, for two items, "either both or neither of these hold".
- **Literal polarity:** each variable appears in a rule as "the X is P" or "the X is not P" at random. The surface word `true` is therefore not tied to the value a rule needs. This removes v1's per-cell shortcut.
- **Outcome polarity:** a rule defines either the positive outcome ("Approval is given if and only if …") or the negative one ("Approval is withheld if and only if …"), and the question always asks the positive one. The same operator can then give a YES or a NO answer for B. Without this, the first draft gave B the answer YES in 87% of pairs, and the operator alone decided the answer.
- **Domains:** approval, access (a gate), shipping, payment and operation (a production line), each with its own question.
- **Uncertainty markers:** "It may be true or false that …" (the v1 wording), "It is not known whether …", "The records do not say whether …" and "Nobody has checked whether …". One marker per story, shared by B and C.

**B answer balance.** Each story is assigned a target answer for B, alternating YES and NO and crossed with the four markers. The story is resampled until a pair with that target exists. Up to two pairs are kept per story; level 1 rules admit only one.

**D control (new).** Each story also has one D row. In D every rule fact is stated, and the same number of uncertain lines fall on distractors that no rule uses, so the answer is determined. An UNKNOWN on D is a **false abstention**, the case "I see uncertainty, so I answer UNKNOWN". D rows go to a separate file because they are not B/C pairs.

## 4. Labels and their verification

- `gold_label()` enumerates every value of the uncertain facts. The answer is YES or NO if all values agree, UNKNOWN otherwise.
- **Independent check on the text.** `tests/test_gen_v2.py` has its own parser, which rebuilds the rules and facts from the prompt text alone and solves them by brute force. On the draft set (seed 20261118) it agrees with the stored gold on **all 4,238 rows** (3,238 B/C rows and 1,000 D rows). A rendering error or a solver error would make this test fail.
- A second test compares the evaluator with the operator definitions on 300 random rule sets and every assignment.
- **Human review, still to do:** the labels follow from the logic, so the human review checks wording, not the labels of individual pairs. Two independent annotators should read a stratified sample of rule renderings across domains, operators, markers and outcome polarities, and judge whether each sentence is unambiguous English. The sample size is decision 5 in §8.

## 5. Shortcut controls (binding before any model run)

v1 showed that synthetic logic data carries surface statistics a model can use instead of reasoning, as found for other synthetic reasoning sets (`zhang2023paradox`) and for NLI (`gururangan2018artifacts`, `mccoy2019right`). `python -m indetbench.gen_v2 audit --input pairs.jsonl` reports:

- minimal-pair violations, which must be 0;
- W of the "It is true" count, overall and per level × root operator;
- B's share of YES, overall and per level × root operator;
- W of a bag-of-words naive Bayes classifier (unigrams and bigrams) trained on four domains and tested on the held-out fifth;
- B's share of YES per level × root operator × outcome polarity. This association is shared by B and C, because they share their rules, so it cannot move W; it does affect accuracy and abstention measures, which must therefore be read per cell.

**Draft check, seed 20261118, 40 stories per level × domain cell (1,000 stories, 1,619 pairs):**

| Check | Result | Draft threshold |
|---|---|---|
| Minimal-pair violations | 0 | 0 |
| B share of YES, overall | 0.507 | 0.45–0.55 |
| B share of YES, per level × root operator | 0.32–0.64 | to be decided |
| W of "It is true" count, overall | 0.494 | 0.45–0.55 |
| W of "It is true" count, per cell (20–114 pairs) | 0.38–0.61 | to be decided |
| W of bag-of-words classifier, held-out domain | 0.47–0.55 | 0.40–0.60 |

**Known remaining association.** At levels 1 and 2, the root operator together with the outcome polarity still fixes B's answer completely (a positive AND rule with one uncertain fact can only give NO). This follows from the logic and cannot be removed by sampling (`zhang2023paradox` shows that such features cannot all be removed jointly). It is reported by the audit, not hidden.

The overall and held-out thresholds are tested in CI as draft values; the binding values are decision 3 in §8.

## 6. Measures

**Track A, open-weight models (white box).** p(UNKNOWN) and W per level, exactly as in the v1 protocol, with `hf_runner` and the per-tokenizer length exclusion. `true` and `false` can differ in token count for some tokenizers, so the exclusion rule matters here.

**Track B, any model, API included (black box).** These measures use only the generated answer:

- abstention on C: share of UNKNOWN answers on C;
- false abstention: share of UNKNOWN answers on B and on D;
- accuracy on B and on D;
- optionally, k samples per prompt at temperature above 0, with the share of UNKNOWN answers as a score (consistency-based confidence, `xiong2024confidence`). A model's verbalised confidence is reported separately.

**Main output:** curves by level, not one number. For each model, the level at which W stops separating B from C (track A), and the level at which abstention on C falls (track B). The two together show the gap between ranking and abstention, which v1 observed at one level (Qwen3-32B: W 0.975, UNKNOWN on 24.4% of C cases). Track B results are reported in a separate table and not ranked against track A, as in [Protocol §3](PROTOCOL.md#3-other-methods).

D rows are not B/C pairs. Running them needs a generation-only runner, which is planned and not part of this draft.

## 7. Size and cost

With the defaults (40 stories per level × domain cell), one run is 1,000 stories: 1,619 B/C pairs (3,238 prompts; per level 200, 400, 296, 344 and 379 pairs) plus 1,000 D prompts, so 4,238 prompts per model. Generation takes under a second on a CPU.

API costs depend on the provider's price list on the day of the run and on the length of reasoning outputs. They must be checked then; no figure is given here.

## 8. Open decisions for the owner

1. Levels: are the five presets in §3 the right ones, and are five enough to reach the frontier models?
2. Size: stories per cell (default 40), and pairs per story (default 2).
3. Binding shortcut thresholds, overall and per cell (draft values in §5).
4. Readability: keep "either both or neither" and the double negations ("not all of these hold: the X is not P"), or restrict them to the higher levels?
5. Human review of the wording: number of renderings per stratum, annotators and agreement statistic (as in the v1 plan: two annotators blind to the gold, Krippendorff's alpha).
6. Models: which open-weight models for a pilot of the curve, and which API models for track B.
7. Primary outcome for the preprint, to be preregistered: for example, the highest level at which the lower bound of W stays above 0.5, and the abstention-on-C rate at that level.
8. Freezing: seed, release of the generated files with SHA-256 and a git tag **before** any model run (the rule in [Protocol §7](PROTOCOL.md#7-preregistration-and-its-limits)).

## 9. Limits

- Templated English with invented vocabulary; no natural documents. A small, human-written natural subset is possible later and would need its own protocol.
- Higher levels are hard to read for people too, partly because of double negations. A model failing there may be failing at reading, not at recognising that the answer is not determined. Accuracy on B and on D separates these two cases in part.
- The generator is reproducible for a given seed on the Python versions in CI. The frozen release will be the files with their SHA-256, not the act of regenerating them.
- The code was generated by AI tools and has not yet been reviewed line by line by a human, like the rest of the repository ([AI_USAGE.md](AI_USAGE.md)).

## 10. Related work

v2 belongs with benchmarks of logical reasoning over natural-language rules: synthetic rule bases with controlled chaining depth (RuleTaker, `clark2020ruletaker`; ProofWriter, `tafjord2021proofwriter`, whose open-world setting has an Unknown answer), the expert-written FOLIO with True/False/Unknown labels (`han2024folio`), LogicBench's inference patterns (`parmar2024logicbench`) and RobustLR's logical edits (`sanyal2022robustlr`). Its contribution is not the logic. It is the **minimal-pair construction** (`warstadt2020blimp`, `gardner2020contrastsets`), which isolates determinability while holding the text constant, the D control for false abstention, and the measurement of **ranking against abstention** across difficulty (`kirichenko2025abstentionbench`, `joren2025sufficientcontext`, `wagner2026twoaxes`, `kadavath2022know`, `geifman2017selective`). It does not claim to be the first graded logic benchmark or the first abstention benchmark.

All keys are in [REFERENCES.bib](REFERENCES.bib); the entries added for v2 are listed, with the pages they were checked against, in [REFERENCES.md](REFERENCES.md#verification-log-v2-generator-18-november-2026).
