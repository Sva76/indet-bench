# Historical research sources — IndetBench

**Status: archive of recovered originals, 13 November 2026** (public since 14 November 2026).
These files preserve the original research provenance of **Step 1** (tests 4–7) and **Step 2** (U, U2, M-A, M-B and C) from the owner's earlier work. They are distinct from the separately generated **240-pair Hugging Face** study under `data/smol_stat_v01_frozen.jsonl`.

## Preserved files

- `step1/Riepilogo_Step1.md`: Step 1 summary, final version (v3, approved 8 November).
- `step2/Riepilogo_Step2.md`: original Step 2 summary.
- `step2/protocols/`: U, U2, M and C protocols and the M2 configuration note, in their approved final versions (Test C protocol v3 including the C-gen-4 and C-sel corrections).
- `step2/results/`: written reports for U, U2, M-A and M-B (owner-reviewed versions) and Test C (draft v2 of 13 November, still under owner review).
- `step2/test_c_controls/`: aggregate outputs of the post-run controls notebook (C-controlli-1a): HC0 of M1 with natural generation, truncation sensitivity, LOG analysis, classifier agreement result, and the owner's review of the notebook. Per-answer model outputs and reading sheets are not committed.
- `step2/test_c_selection/`: written closure of selection C-sel-8 at 199/200 DUE-nat pairs.
- `hf_revisions_verified.json`: every model and dataset revision used in Steps 1–2 and in the 13 November CPU studies, checked on the Hugging Face Hub on 13 November (metadata only).
- `step2/notebooks/`: original Test C C-sel-8 selection and full inference notebooks, valid unexecuted JSON.
- `step2/scripts/`: seven original Python scripts extracted from the `%%writefile` cells of the C-sel-8 notebook. All seven were independently compared *byte-for-byte* with the named scripts in the owner's original `testC_selezione.zip`; no changes were made.
- `step2/frozen/`: **five GZIP-compressed copies of unchanged frozen synthetic JSON files** (Test M 4,800 source rows; Test C synthetic definitive, technical test and deterministic reserves). These were copied from the original experiment ZIP members; decompression recovers the original JSON byte-for-byte.

## Document versions

The protocol and report files first added at commit `3e0e9fb` were earlier drafts (for example marked «bozza» or «da approvare»). They were replaced by the final versions kept in the owner's project archive; each file's SHA-256 is listed under `documents_final_versions` in the manifest. The drafts remain in git history.

## Original machine-readable statistical reports

The folder `step2/numeric_reports/` contains **eight original result/table reports**, GZIP-compressed without altering their source bytes: the M-A/M-B/Test C `esiti_*.json`, the Test C narrative report and A/B/C CSV tables (including the M-B per-family table). Decompress with `gzip -dc`; all original SHA-256 values are in the manifest. These are historical experiment outputs, NOT reanalyses.

## Validate source file integrity

```bash
gzip -dc research_originals/step2/frozen/M_Original_4800_righe.json.gz > /tmp/original_M_righe.json
sha256sum /tmp/original_M_righe.json
# Expected: 906c01bf2988607247b4b06f92b15d189bcb49278a6964ae2479b2236f96d459
```

All expected archive and file SHA-256 values are recorded in [manifest_originals.json](manifest_originals.json). The M-A and M-B experiments include **the same frozen original M dataset**, verified by comparing their archive members.

## Missing / not yet redistributed

This is **not** a claim that the full original Step 1/Step 2 research package is already in GitHub. Historical Step 1 frozen datasets and generator notebooks, the Test U output archive, the TriviaQA rows and third-party probe weights remain to be archived or linked to a durable restricted storage source; the output archives of Tests U2, M and C are published in `step2/outputs/` (see below). Refer to the original experiments, not their paraphrases, before asserting full replication.

The complete Test C selection `dati/righe_C.json` (2,478 rows including technical and natural cases) is in `step2/test_c_selection/righe_C.json.gz` (published 15 Nov 2026 by the owner's decision). Its natural rows are derived from SQuAD 2.0 and are distributed under CC BY-SA 4.0 with attribution; see [`step2/outputs/README.md`](step2/outputs/README.md#licences-and-attribution).

## What is not here

This is a substantial partial recovery, not the entire historical research archive. Since 15 November 2026 the complete output archives of Tests U2, M (notebooks A and B) and C are in [`step2/outputs/`](step2/outputs/README.md), with SHA-256 values and replay commands; from the notebook A archive only the TriviaQA rows were removed (licence not checked). Still not committed: the Test U output archive, several original Step 1 files, the TriviaQA rows, model and probe weights. The M-A and M-B original frozen inputs were checked to be identical.

## Rights and provenance

The root license (PolyForm Noncommercial 1.0.0, © Simona Vargiu) covers the owner's original material archived here; third-party content is excluded or keeps its own terms. **Do not change licensing without explicit owner approval and third-party rights review.**

These source records are historical. Later versions or observations must be separately versioned, not silently overwrite original protocols or results.
