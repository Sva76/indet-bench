# IndetBench v2: generator specification (DRAFT)

*Status: draft for owner review, revised 18 November 2026 after the owner's review of PR #24. Not frozen, not preregistered, no model has been run on v2 data.*

**Author and owner:** Simona Vargiu (principal investigator). The research question, the B/C determinability design and the decision to build a graded v2 set are hers; she approved the outline of this specification and the constraints of this revision (§5.2, §5.3, §6) on 18 November 2026. The text and the code were drafted with AI assistance (Claude Opus 5.5) at her request, as recorded in [AI_USAGE.md](AI_USAGE.md). Every point in §8 is an open decision that belongs to her.

**Licence:** original IndetBench material, © 2026 Simona Vargiu, under the [PolyForm Noncommercial License 1.0.0](../LICENSE) with the [required notice](../NOTICE). Code: [`src/indetbench/gen_v2.py`](../src/indetbench/gen_v2.py). Tests: [`tests/test_gen_v2.py`](../tests/test_gen_v2.py). Audits: [`results/v2_draft_audit_2026-11-18/`](../results/v2_draft_audit_2026-11-18/README.md).

The v1 benchmark is not changed by any of this. The 800 frozen pairs, their SHA-256, the results and the archives stay as they are; v2 is a separate set. The human reviews required for the v1 alpha are not affected.

**Correction to the first draft (PR #24).** The first draft said that v2 "removes v1's per-cell shortcut" and reported a shortcut audit close to chance. That audit grouped pairs too coarsely and did not check its input. Finer grouping showed that at levels 1 and 2, operator × outcome polarity × sign of the changed literal × its truth word separated B from C in every pair. §5 replaces those results.

**Second correction (CodeRabbit, PR #25).** A first version of this revision claimed that `--flip-location intermediate` makes every pair at levels 3–5 depend on following the chain, and that the default reproduces the first draft's prompts. Neither is true. A reader of Rule 1 alone separates B from C at levels 3 and 4 under `intermediate` (§5.2), and the satisfaction target changes which stories the default draws.

## 1. Purpose

v2 asks **up to what logical complexity a model recognises that the answer is not determined, and how often it actually abstains.** v1 answers this for one level of difficulty, and that level is already saturated at 8B parameters (W of p(UNKNOWN): Qwen3-8B 0.975, Qwen3-32B 0.975, reasoning models up to 1.000).

v2 addresses two limits of v1:

- **Narrow task.** v1 has one question, three logical templates and two variables. B's answer depends only on the family (AND always NO, OR and IMPLIES always YES), and counting "It is true" separates B from C perfectly within every family × variant cell.
- **Frontier models excluded.** p(UNKNOWN) needs token probabilities, which frontier APIs do not return ([Protocol §2](PROTOCOL.md#2-reference-score-punknown)).

What v2 does **not** address: whether p(UNKNOWN) carries information specific to indeterminacy rather than generic answer uncertainty (§9). v2 is a test bed on which that question can later be asked; it does not answer it.

## 2. What stays the same (invariants)

1. **Minimal pairs.** B and C differ in exactly one word, the truth value (`true` / `false`) of one stated fact. Same number of words, same uncertain lines, same rules, same order of facts.
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

Level 1 is the v1 configuration, with the new variety below. In a chain, each rule defines an intermediate condition (for example "the permit is valid") that the next rule uses; intermediate conditions are never stated as facts. Several knobs change together from one level to the next, so a drop in performance cannot be attributed to one of them (§9, decision 9).

**Variety at every level:**

- **Operators:** "both … and …" / "all of these hold", "at least one of these holds", "exactly one of these holds", "not all of these hold", and, for two items, "either both or neither of these hold".
- **Literal polarity:** each variable appears in a rule as "the X is P" or "the X is not P" at random.
- **Outcome polarity:** a rule defines either the positive outcome ("Approval is given if and only if …") or the negative one ("Approval is withheld if and only if …"); the question always asks the positive one, so the same operator can give a YES or a NO answer for B.
- **Domains:** approval, access (a gate), shipping, payment and operation (a production line), each with its own question.
- **Uncertainty markers:** "It may be true or false that …" (the v1 wording), "It is not known whether …", "The records do not say whether …" and "Nobody has checked whether …". One marker per story, shared by B and C.

**Balanced design.** In each level × domain cell, story number n = 8q + r gets marker r mod 4, B target YES or NO by r div 4, and a target for whether the changed literal is satisfied in C, (marker + target + q) mod 2. Every block of 8 stories therefore has each marker twice and each target 4 times. A story is resampled as a whole, with unchanged templates, until it has a valid pair meeting its targets (§5.3). Up to two pairs are kept per story; level 1 rules admit only one.

**Option `flip_location`** (`--flip-location any | root | intermediate`, default `any`). For levels with a chain, it restricts the rule that holds the changed fact; the default allows either. It constrains only where the changed literal sits, not which prompts need which rules (§5.2). Because of the satisfaction target, the default draws different stories from the first draft (PR #24) for the same seed.

**Story ids** start with a dataset tag (generator version, seed, `flip_location`, stories per cell, pairs per story, and a digest of the ordered levels and domains, because one random stream runs across cells), for example `v2g0.1.0-draft-s20261119-any-c40-p2-e4ddd14d-L1-approval-0000`. A score file made on another seed or setting therefore cannot match the generated file in the report.

**D control.** Each story also has one D row. In D every rule fact is stated, and as many uncertain lines as B has fall on distractors that no rule uses, so the answer is determined. An UNKNOWN on D is a **false abstention**. D rows go to a separate file because they are not B/C pairs.

## 4. Labels and their verification

- `gold_label()` enumerates every value of the uncertain facts: YES or NO if all values agree, UNKNOWN otherwise.
- **Independent check on the text.** `tests/test_gen_v2.py` has its own parser, which rebuilds the rules and facts from the prompt text alone and solves them by brute force. It agrees with the stored gold on every B, C and D row of the test set. The same parser re-derives each row's metadata: the rule, sign and location of the changed fact, its satisfaction in C, and the shallow counts of §5.2.
- A second test compares the evaluator with the operator definitions on 300 random rule sets and every assignment.
- A third test rebuilds the four confirmation files (seed 20261119; pairs and controls; `any` and `intermediate`) and checks their SHA-256 in the `cpu-tests` CI job (Python 3.10 and 3.12), so CI detects any change in generation.
- `minimal_pair_ok()` checks that the one changed word is the truth value of the same stated fact, in the Facts block; a change anywhere else is a violation.
- **Human review, still to do:** the labels follow from the logic, so the human review checks wording, not the labels of individual pairs (decision 5).

## 5. Shortcut controls (binding before any model run)

Synthetic logic data carries surface statistics that a model can use instead of reasoning (`zhang2023paradox`; for NLI, `gururangan2018artifacts`, `mccoy2019right`). Not every such statistic is a defect. Reading an operator, the sign of a literal and its truth value **is** one-step reasoning. The audit therefore reports each statistic with its cell size and states which reading applies.

### 5.1 Integrity

`audit()` and `report()` refuse a record that is not a JSON object, a missing or blank field, a side other than B/C (D in its own file, also checked for duplicates), a duplicate `row_id`, a duplicate side in a pair, a pair split across stories or an incomplete pair. Before this revision, incomplete pairs were dropped and duplicates overwritten silently.

### 5.2 Baselines evaluated on unseen stories and unseen structures

Each baseline scores **one prompt at a time**, as a model would, and is evaluated only on stories, domains or logical structures that it did not see during fitting (5 story folds; leave-one-domain-out; 5 folds of logical structure = level × operator sequence × outcome polarity). W is given per level with a 95% story-bootstrap interval.

- **Bag of words:** naive Bayes on unigrams and bigrams. On minimal pairs it reduces to the direction of the one changed word, so it is a weak test.
- **Shallow reading with the operator:** a lookup on level, outcome polarity, root operator and, for the root rule only, how many literals the stated facts satisfy, falsify or leave uncertain. This reads one rule and does not follow the chain.
- **Shallow reading without the operator:** a lookup on level and the same counts summed over all rules. A high score on unseen structures would be a **spurious** cue, because it would work without knowing what the rule says.
- **Single-rule readers:** for each rule position k (Rule 1, Rule 2, …), a lookup on level, outcome polarity, **root operator**, and the operator and literal counts of rule k only. They read the root operator but not the root's literal counts. Reported by level and by level × root operator.

These baselines measure how well a reader that looks at one rule **ranks** C above B. W = 0.50 shows no net ranking advantage; it does not by itself mean that pairs tie. Any single-rule reader gives B and C identical features, and so tied scores, when the changed fact is not in the rule it reads (for example the root-rule reader on pairs whose changed fact is in an intermediate rule, or the Rule 1 reader when the changed fact is in the root). Neither W = 0.50 nor a high W shows which rules a prompt's label depends on.

**Confirmation seed 20261119, 40 stories per level × domain cell, default settings (1,000 stories, 1,560 pairs).** W [95% interval]:

| Baseline | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|
| Bag of words, unseen domain | 0.52 [0.44, 0.59] | 0.50 [0.45, 0.55] | 0.50 [0.44, 0.57] | 0.53 [0.47, 0.60] | 0.53 [0.47, 0.59] |
| Shallow with operator, unseen stories | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.66 [0.63, 0.69] | 0.76 [0.72, 0.79] | 0.64 [0.61, 0.67] |
|   changed fact in the final rule | 1.00 | 1.00 | 1.00 | 0.99 | 0.95 |
|   changed fact in an intermediate rule | – | – | 0.50 | 0.50 | 0.50 |
| Shallow without operator, unseen stories | 0.46 [0.39, 0.53] | **0.78 [0.72, 0.84]** | 0.52 [0.46, 0.59] | 0.50 [0.44, 0.56] | 0.47 [0.41, 0.53] |
| Shallow without operator, unseen structures | 0.12 [0.08, 0.17] | **0.78 [0.72, 0.84]** | 0.36 [0.30, 0.43] | 0.33 [0.27, 0.40] | 0.49 [0.43, 0.54] |
| Rule 1 only, unseen stories | 1.00 | 1.00 | 0.79 [0.76, 0.82] | 0.70 [0.67, 0.73] | 0.57 [0.55, 0.60] |
| Rule 2 only, unseen stories | – | – | 0.66 (root) | 0.76 (root) | 0.57 [0.54, 0.60] |
| Rule 3 only, unseen stories | – | – | – | – | 0.64 [0.61, 0.67] (root) |

**Same seed, `--flip-location intermediate` (1,479 pairs):**

| Baseline | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|
| Shallow with operator (root rule) | 1.00 | 1.00 | 0.50 | 0.50 | 0.50 |
| Rule 1 only | 1.00 | 1.00 | **0.95 [0.93, 0.97]** | **0.92 [0.90, 0.95]** | 0.57 [0.54, 0.61] |
| Rule 2 only | – | – | 0.50 (root) | 0.50 (root) | 0.60 [0.57, 0.64] |
| Shallow without operator, unseen stories | 0.46 | **0.78** | 0.54 | 0.41 | 0.45 |
| Shallow without operator, unseen structures | 0.145 | **0.78** | 0.42 | 0.345 | 0.44 |
| Bag of words | 0.41–0.54 at every level | | | | |

How to read these results:

1. **Levels 1–2, shallow reading with the operator = 1.00.** One rule and one step: reading the operator, the sign and the value solves the item. This is legitimate reasoning, and it is the v1 level of difficulty.
2. **Levels 3–5, default settings: the root-rule reader reaches 0.64–0.76, from pairs whose changed fact is in the final rule** (34–56% of pairs at these levels on the confirmation seed; 0.95–1.00 on them, exactly 0.50 on the others). On those pairs the final rule alone ranks C above B. That does not mean C can be answered from the final rule alone: C's indeterminacy can still depend on an intermediate rule.
3. **`--flip-location intermediate` does not stop a one-rule reader at levels 3–4.** At depth 2 the changed fact is then always in Rule 1, and the Rule 1 reader (Rule 1's operator and counts, plus the root operator and outcome polarity) ranks C above B with W 0.95 and 0.92. With a root rule such as "exactly one" or "either both or neither", whose other literal is known, the root is determined exactly when Rule 1 is, so for those root operators Rule 1 decides the pair (W 0.97–1.00). With other root operators some labels still depend on the root: for `Rule 1 = a AND b`, `root = Rule 1 AND c`, `a` uncertain, changing `b` from false to true gives UNKNOWN only if `c` is true. The single-rule reader ranks many of these pairs correctly; it does not show that Rule 1 alone determines every label. **At level 5, every single-rule reader's level-wide estimate stays below 0.65** (best 0.60 with `intermediate`, 0.64 with the default), but some root-operator subgroups exceed it (for example Rule 2 with an "exactly one" root under `intermediate`, 0.73; Rule 3 with an OR root under the default, 0.73). The audit lists every subgroup (decision 10).
4. **Level 2, shallow reading without the operator = 0.78 on unseen structures. This is a real residual shortcut.** With three literals and one uncertain, C is the prompt where the two known facts point the same way ("unanimity") for AND, OR and "not all of these hold". The rule fails only for "exactly one of these holds". It has not been removed; it is declared here and measured (decision 11).
5. **Values well below 0.5 on unseen structures (L1 0.12; L3–L4 0.33–0.36)** mean that a count rule learned on other structures reverses on a new one. Counting without the operator does not transfer across structures.

The development seed (20261118) gives the same pattern; all four audits are in [`results/v2_draft_audit_2026-11-18/`](../results/v2_draft_audit_2026-11-18/README.md).

### 5.3 Satisfaction of the changed literal in C

In the first draft, the changed literal was satisfied in C in 53–68% of pairs. A reader that sees which fact differs could use this. Balancing **inside a story** is mostly not feasible. In single-rule stories (levels 1–2) the operator fixes the kind: AND and "not all" give satisfied in C, OR and "exactly one" unsatisfied, and no story has both kinds. In chains the kind is not fixed by the operator (for example, with `R1 = a OR b` and `root = R1 AND u`, `a` false and `u` uncertain, changing `b` from false to true makes the answer UNKNOWN and satisfies an OR literal), but it is still strongly associated with it. At levels 3–5, 12–37% (default) and 13–38% (`intermediate`) of pairs come from stories where both kinds were available within the run's location constraint, mostly where the rule holding the literal is "either both or neither" or "exactly one" (confirmation seed; `balance_feasibility_within_story` in the audit). Balancing is therefore done **across stories** with the targets of §3, without changing any rule template. Result (confirmation seed, default): 0.50, 0.50, 0.49, 0.49, 0.50 by level. Per operator the share stays near 0 or 1, as the logic requires; the audit reports it per level × operator with cell sizes.

### 5.4 Other audit tables

- Minimal-pair violations: 0 on both seeds and both settings.
- B share of YES: 0.501 overall (default) and 0.498 (`intermediate`); per level × root operator, and per level × operator × outcome polarity, with cell sizes. At levels 1–2 the operator together with the outcome polarity still fixes B's answer, which matters for accuracy and abstention measures (read per cell), not for W.
- W of the "It is true" count: 0.516 overall (default), and per fine subcell (level × operator of the rule holding the changed fact × outcome polarity × sign × location), with sizes. The share of pairs in subcells of at least 10 pairs where the count separates B and C perfectly is, by level, 0.97 / 1.00 / 0.23 / 0.47 / 0.19 (default) and 0.97 / 1.00 / 0.00 / 0.19 / 0.00 (`intermediate`); At levels 3–5, 34–42% of pairs (default) and 8–13% (`intermediate`) are in subcells too small to judge, which the audit reports separately. These are pair-level diagnostics: a model sees one prompt and does not know which fact differs, so the per-prompt baselines of §5.2 are the relevant test.

**Draft thresholds tested in CI** (the binding values are decision 3): 0 violations; B share of YES 0.45–0.55; W of the count 0.45–0.55 overall; satisfaction in C 0.45–0.55 per level.

## 6. Measures and the report

`indet-bench-v2 report --pairs pairs.jsonl --scores scores.csv [--controls controls.jsonl --control-answers answers.csv]` gives, **for each level**, with a 95% story-bootstrap interval:

- **Ranking:** W of p(UNKNOWN), excluding pairs whose B and C prompts differ in token count (with a sensitivity value that includes them), and W of the generated answer (UNKNOWN = 1);
- **Solving determined questions:** accuracy on B, overall and separately for gold YES and gold NO, and accuracy on D;
- **Abstention:** share of UNKNOWN on C (abstention when needed), on B and on D (false abstention);
- the same W (probability and answer), abstention on C and false abstention on B, split **by the operator** of the rule that holds the changed fact and **by its location**; the median label mass and the share of unreadable answers.

**Populations.** Accuracy and abstention use every scored row of the side concerned, even when the other side of its pair is missing. W of the generated answer uses complete pairs. W of p(UNKNOWN), the primary measure, uses complete pairs whose B and C prompts have the same token count, with all complete pairs as a sensitivity value, in the splits too. The coverage that sets DESCRIPTIVE is that of the primary population (complete pairs for an answer-only file), compared on counts before any rounding. A probability file without `prompt_tokens` cannot pass the length check, so it receives DESCRIPTIVE with that reason, never a verdict.

**Input checks.** B/C score files must have `row_id`, `pair_id`, `block_id`, `side` and `parsed`. `score`, `mass_total`, `prompt_tokens` and the model columns are optional, but a column present in one row must be present in all. Ids must exist in the generated file, with the same pair, story and side, and no duplicates. Only one model is allowed, and the D answers must come from the same model when they name one. D controls must belong to the stories of the B/C file, with the same rules. B and C of a pair must agree on their story and pair metadata, and the fields the report reads must be present with the right type. Each story may have at most one D control, whose level, gold and rules must match the story. `prompt_tokens` must be a positive integer and is compared as a number. Labels must be YES, NO, UNKNOWN or ALTRO, and numbers must be finite. Otherwise the report stops. D answers need only `row_id,parsed`.

**Statuses**, in this order, are reported per level and are never merged with a negative result: NOT MEASURABLE (median label mass < 0.5, true median), NOT EVALUABLE (accuracy on B < 0.5 overall, on gold YES or on gold NO), DESCRIPTIVE (coverage of the primary population < 95% of pairs), ANSWERS ONLY (no probability scores: answer measures, no verdict), DESCRIPTIVE (probability scores without `prompt_tokens`), and only then a verdict with the v1 thresholds (CONFIRMED if W ≥ 0.60 and the lower bound > 0.5; NOT CONFIRMED if the upper bound ≤ 0.5; otherwise NOT CONCLUSIVE). The v1 thresholds are applied provisionally (decision 3).

**Two tracks.** Track A (open-weight models) uses p(UNKNOWN) from `hf_runner`. Track B (any model, API included) uses only the generated answer: the report computes W of the answer, accuracy and abstention from the `parsed` column of any runner. Consistency over k samples (`xiong2024confidence`) and verbalised confidence are planned, not implemented. Track B results are reported in a separate table and not ranked against track A ([Protocol §3](PROTOCOL.md#3-other-methods)).

**Still missing:** a generation-only runner for D rows and for API models (`hf_runner` reads B/C pairs only). The report accepts D answers from any runner as a CSV `row_id,parsed`.

## 7. Size and cost

With the defaults (40 stories per level × domain cell), one run is 1,000 stories: 1,560 B/C pairs on the confirmation seed (3,120 prompts) plus 1,000 D prompts, about 4,100 prompts per model. With `--flip-location intermediate`, 1,479 pairs. Generation takes under a second on a CPU; the audit with baselines takes a few seconds.

API costs depend on the provider's price list on the day of the run and on the length of reasoning outputs. They must be checked then; no figure is given here.

## 8. Open decisions for the owner

1. Levels: are the five presets in §3 the right ones?
2. Size: stories per cell (default 40) and pairs per story (default 2). Fine subcells at levels 3–5 are often below 10 pairs at this size.
3. Binding thresholds for the audit (draft values in §5.4) and for the v2 verdict (the v1 thresholds are used provisionally).
4. Readability: keep "either both or neither" and the double negations, or restrict them to the higher levels?
5. Human review of the wording: renderings per stratum, annotators and agreement statistic (as in the v1 plan: two annotators blind to the gold, Krippendorff's alpha).
6. Models: which open-weight models for the pilot (decision 9) and which API models for track B.
7. Primary outcome for the preprint, to be preregistered: for example, the highest level at which the lower bound of W stays above 0.5, and abstention on C at that level.
8. Freezing: seed, release of the generated files with SHA-256 and a git tag **before** any model run ([Protocol §7](PROTOCOL.md#7-preregistration-and-its-limits)).
9. **Pilot of difficulty**, on a seed kept apart from the final data: do the levels actually get harder for models, large ones especially? For causal attribution, a design in which one knob changes at a time (depth, variables, uncertain facts, distractors), which needs a small extension of the generator.
10. **Real depth of levels 3–4.** Under either setting of `flip_location`, a reader of one rule (that rule's operator and counts, plus the root operator and outcome polarity) ranks most pairs at levels 3–4 correctly (§5.2, point 3), although some labels still depend on the root. Options: accept that levels 3–4 test mostly one-rule determinacy and report the single-rule readers beside the models; change the generator so that, at those levels, no single rule settles the item (for example, uncertain facts in two different rules); or keep only level 5 as the "chain" level.
11. **The level-2 unanimity shortcut (§5.2, point 3):** accept it as declared, change the level-2 operator mix, or drop level 2 from the primary analysis.

## 9. Limits

- **Specificity is not tested.** v2 measures how recognition of indeterminacy changes with complexity. It does not contain a preregistered comparison of hard B items with easy C items that controls for generic uncertainty, so it cannot show that p(UNKNOWN) detects something different from entropy. That needs its own protocol.
- **Levels confound knobs** (§3, decision 9).
- **Residual shortcuts:** the level-2 unanimity cue; at levels 3–4 the best single-rule reader ranks C above B with W 0.76–0.95, depending on the setting; only at level 5 are all single-rule readers below 0.65 level-wide, with some subgroups above it (§5.2).
- Templated English with invented vocabulary; no natural documents. Higher levels are hard to read for people too, partly because of double negations: a model failing there may be failing at reading. Accuracy on B and on D separates these two cases in part.
- The generator is reproducible for a given seed and the CI checks a SHA-256 on the supported Python versions. The frozen release will be the files with their SHA-256, not the act of regenerating them.
- The development seed was used to correct the generator; the confirmation seed was first generated after the prompt-generating code was committed (`b605ac2`). The audit code was revised afterwards (CodeRabbit, PR #25) and re-run on both seeds, with the prompts of the confirmation seed unchanged ([audit README](../results/v2_draft_audit_2026-11-18/README.md)). Neither seed is the final data set; the pilot of decision 9 needs a further seed that nothing has been tuned on.
- The code was generated by AI tools and has not yet been reviewed line by line by a human, like the rest of the repository ([AI_USAGE.md](AI_USAGE.md)). Passing CI checks is not a scientific review.

## 10. Related work

v2 belongs with benchmarks of logical reasoning over natural-language rules: synthetic rule bases with controlled chaining depth (RuleTaker, `clark2020ruletaker`; ProofWriter, `tafjord2021proofwriter`, whose open-world setting has an Unknown answer), the expert-written FOLIO with True/False/Unknown labels (`han2024folio`), LogicBench's inference patterns (`parmar2024logicbench`) and RobustLR's logical edits (`sanyal2022robustlr`). Its contribution is not the logic. It is the **minimal-pair construction** (`warstadt2020blimp`, `gardner2020contrastsets`), which isolates determinability while holding the text constant, the D control for false abstention, and the measurement of **ranking against abstention** across difficulty (`kirichenko2025abstentionbench`, `joren2025sufficientcontext`, `wagner2026twoaxes`, `kadavath2022know`, `geifman2017selective`). It does not claim to be the first graded logic benchmark or the first abstention benchmark.

All keys are in [REFERENCES.bib](REFERENCES.bib); the entries added for v2 are listed, with the pages they were checked against, in [REFERENCES.md](REFERENCES.md#verification-log-v2-generator-18-november-2026).
