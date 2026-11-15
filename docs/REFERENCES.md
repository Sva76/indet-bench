# References and attribution

All bibliographic entries are in [REFERENCES.bib](REFERENCES.bib). It covers:

- the published methods evaluated in IndetBench;
- the datasets they rely on;
- every work cited in [RELATED_WORK.md](RELATED_WORK.md) and [NOVELTY_AND_RELATED_WORK_2026.md](NOVELTY_AND_RELATED_WORK_2026.md);
- the technical reports of the models used in the experiments;
- the main software libraries.

Exact model revisions are not in the bibliography. They are pinned in [`research_originals/hf_revisions_verified.json`](../research_originals/hf_revisions_verified.json), in [`notebooks/Note_modelli_nuovi_v3.md`](../notebooks/Note_modelli_nuovi_v3.md) and in each `manifest.json` under `results/`. Licences are in [THIRD_PARTY.md](THIRD_PARTY.md).

## What to cite

If you use IndetBench, cite the software ([CITATION.cff](../CITATION.cff)). Also cite the methods, datasets and models behind the results you report:

| You report results on | Cite |
|---|---|
| LM-Polygraph estimators (Test M, method M1) | `fadeeva2023lmpolygraph`, `vashurin2025benchmarking`; for Semantic Entropy also `kuhn2023semantic`, `farquhar2024semanticentropy`; for p(True) also `kadavath2022know` |
| SIRIN answerability probe and judges (M2, M3) | `parchiev2026sirin` |
| Obeso et al. hallucination probes (M4) | `obeso2025realtime` |
| SQuAD 2.0-derived controls or natural cases | `rajpurkar2018squad` |
| Any model | the model's entry in the "Models" section of the `.bib` file |

## Code repositories of the evaluated methods

| Method | Repository | Commit used | Licence (read from the repository's LICENSE file, 15 Nov 2026) |
|---|---|---|---|
| LM-Polygraph | <https://github.com/IINemo/lm-polygraph> | package `lm-polygraph==0.7.0` (as pinned in the Step 2 protocols) | MIT |
| SIRIN | <https://github.com/sb-ai-lab/SIRIN> | `ef3bed143890dbee56b34755f8c27a218aef0aa2` | Apache-2.0 |
| Hallucination probes (Obeso et al.) | <https://github.com/obalcells/hallucination_probes> | code `295450e2c24db7ecac1229e21783d2ebd08f9582`; probe weights `obalcells/hallucination-probes` at Hub revision `db581ce2166d…` | Apache-2.0 |

Distinguish the original and modified probe configurations, and the linear and LoRA variants, as the protocols do.

## Verification log (15 November 2026)

Each entry was checked against the page in the "Source checked" column. Authors, title, venue, pages and DOI were compared field by field.

- When a page listed more authors than are written out in full, the `.bib` file ends the list with `and others`. This applies to Kadavath et al., the OLMo 2, Llama 3, Phi-4 and SmolLM2 reports.
- An entry with an arXiv identifier and no venue was found only as a preprint on the date of the check.
- These checks concern bibliographic data only. The summaries of findings in `RELATED_WORK.md` are the project's own reading of each paper (see the note at the top of that page). Readers should consult the original before quoting a number.

| Key | Source checked | Notes |
|---|---|---|
| `fadeeva2023lmpolygraph` | ACL Anthology 2023.emnlp-demo.41 | unchanged |
| `vashurin2025benchmarking` | ACL Anthology 2025.tacl-1.11 | Anthology URL added |
| `parchiev2026sirin` | arXiv 2608.00033 (PDF, first page) | **author order corrected**. The previous entry `belikova2026sirin` put Belikova first; the paper lists Parchiev, Filimonov, Polev, Belikova, Savchenko, Makarenko |
| `obeso2025realtime` | arXiv 2509.03531 | DOI added |
| `rajpurkar2018squad` | ACL Anthology P18-2124 | unchanged |
| `liu2023unknownbench` | arXiv 2311.09731 | added |
| `wen2024contextperturbations` | ACL Anthology 2024.findings-emnlp.197 | unchanged |
| `ming2025faitheval` | ICLR 2025 proceedings; arXiv 2410.03727 | added |
| `kirichenko2025abstentionbench` | NeurIPS 2025 proceedings page (DOI 10.52202/085713-5729) | unchanged |
| `fan2025missingpremise` | arXiv 2504.06514 | added |
| `tong2026askconditionabstain` | arXiv 2608.16554 | added |
| `zhang2026evidencesufficiency` | publisher page, Computers, Materials & Continua 89(1), article 69 | **journal, volume, issue and article number added** (previously missing) |
| `joren2025sufficientcontext` | ICLR 2025 proceedings; arXiv 2411.06037 | added |
| `warstadt2020blimp` | ACL Anthology 2020.tacl-1.25 | added |
| `gardner2020contrastsets` | ACL Anthology 2020.findings-emnlp.117 | added |
| `sanyal2022robustlr` | ACL Anthology 2022.emnlp-main.653 | added |
| `tafjord2021proofwriter` | ACL Anthology 2021.findings-acl.317 | added |
| `han2024folio` | ACL Anthology 2024.emnlp-main.1229 | added. Published at EMNLP 2024, not only as arXiv 2209.00840 |
| `ling2026promptartifact` | ACL Anthology 2026.emnlp-main.549 (PDF); arXiv 2507.16199 | **duplicate removed**. See note 1 below |
| `yan2026wrongprediction` | arXiv 2608.31068 | added. Reported in press as accepted to EMNLP 2026; update when the Anthology record exists |
| `kadavath2022know` | arXiv 2207.05221 | added. p(True) is one of the M1 estimators |
| `agnimo2026uncertaintyestimators` | arXiv 2605.27016 (abstract page) | added, with the title shown on arXiv on 15 Nov 2026 |
| `santilli2025lengthbias` | ACL Anthology 2025.acl-short.60 | added. Published at ACL 2025 |
| `tomov2025illusion` | arXiv 2511.04418 (v2) | added |
| `wagner2026twoaxes` | arXiv 2607.08456 | added |
| `orgad2025llmsknowmore` | ICLR 2025 proceedings; arXiv 2410.02707 | added. Published at ICLR 2025 |
| `azizian2025geometries` | arXiv 2506.08572; ICML 2025 workshop page | added. Workshop paper, non-archival |
| `slobodkin2023curious` | ACL Anthology 2023.emnlp-main.220 | added |
| `buerger2024truthuniversal` | NeurIPS 2024 poster page; arXiv 2407.12831 | added. Published at NeurIPS 2024 |
| `truong2023naysayers` | ACL Anthology 2023.starsem-1.10 | added. Published at *SEM 2023 |
| `kuhn2023semantic`, `farquhar2024semanticentropy` | ICLR 2023 page; Nature 630, 625–630 | **added; previously missing although Semantic Entropy is one of the M1 estimators** evaluated in Test M (`Protocollo_testM_metodi_v2.md`) |
| `yin2023selfaware` | ACL Anthology 2023.findings-acl.551 | added. SelfAware was previously cited only through Wagner (2026) |
| `wen2025knowyourlimits` | ACL Anthology 2025.tacl-1.26 | added as background (abstention survey) |
| `hewitt2019controltasks` | ACL Anthology D19-1275 | added as background (probe control tasks) |
| `azaria2023internalstate` | ACL Anthology 2023.findings-emnlp.68 | added as background (truthfulness probes) |
| `marks2024geometry` | arXiv 2310.06824 (COLM 2024 version) | added as background (truth directions) |
| `min2020ambigqa`, `zhang2021situatedqa` | ACL Anthology 2020.emnlp-main.466; 2021.emnlp-main.586 | added (§8). The dataset name is SituatedQA, not "SituationalQA" |
| `hu2023falseqa` | ACL Anthology 2023.acl-long.309 | added (§8). FalseQA is by Hu et al., not by Yin et al. (SelfAware) |
| `burns2023ccs` | ICLR 2023 poster page; arXiv 2212.03827 | added (§8) |
| `lin2022truthfulqa`, `li2023halueval`, `zhao2024wildhallucinations` | ACL Anthology 2022.acl-long.229; 2023.emnlp-main.397; arXiv 2407.17468 | added (§8) |
| `miller2024errorbars` | arXiv 2411.00640 | added (§8) |
| `geifman2017selective` | NeurIPS 2017 page; arXiv 1705.08500 | added (§8) |
| Models (`qwen3`, `qwen25`, `mistralnemo2024`, `olmo2`, `llama3`, `gemma2`, `phi4`, `yi2024`, `falcon3`, `smollm2`, `tinyllama`) | arXiv abstract pages, the Mistral AI announcement page, and the Falcon3 model card | added. Mistral NeMo and Falcon 3 have no technical report; the official announcement and the citation that the model card requests are cited instead |
| Software (`wolf2020transformers`, `paszke2019pytorch`, `harris2020numpy`) | ACL Anthology 2020.emnlp-demos.6; NeurIPS 2019 proceedings; Nature 585, 357–362 | added |

**Note 1, Ling et al.** arXiv 2507.16199 was first posted in July 2025 with the title *WakenLLM*. The current arXiv version and the EMNLP 2026 paper carry the title *LLM Abstention Can Be a Prompt Artifact, in Addition to Genuine Uncertainty*. Earlier versions of `RELATED_WORK.md` cited the two titles as two separate works. They are one work, and `RELATED_WORK.md` now cites it once.

The DOI `10.18653/2026.emnlp-main.549` has no `v1/` segment. This matches the pattern the ACL Anthology uses for 2026 proceedings, so it was kept as published.

## Still to do before a formal release

- Replace `yan2026wrongprediction` with its ACL Anthology record once it is listed.
- Add DOIs for the ICLR, NeurIPS 2024 and COLM entries if the publishers assign them.
- Re-run this check on the date of any paper submission. Preprints change titles and versions; one entry, Ling et al., already did.
