"""Strict CSV ingestion for paired-score experiments."""
from __future__ import annotations

import csv
from pathlib import Path

from .metrics import PairScore


def load_pair_scores_csv(path: str | Path) -> list[PairScore]:
    """Load normalized long-form pair_id,block_id,side,score data."""
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"pair_id", "block_id", "side", "score"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV missing required columns: {sorted(required - set(reader.fieldnames or []))}")
        return [
            PairScore(
                pair_id=(row["pair_id"] or "").strip(),
                block_id=(row["block_id"] or "").strip(),
                side=(row["side"] or "").strip(),
                score=float(row["score"]),
            )
            for row in reader
        ]
