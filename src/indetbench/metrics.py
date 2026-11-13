"""CPU-only B/C paired-score metrics.

Development implementation. Exact parity with frozen Test M and Test C
analyses is an upcoming acceptance test, not a current claim.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import isfinite
from random import Random
from typing import Iterable, Sequence


@dataclass(frozen=True)
class PairScore:
    """Higher score means greater predicted indeterminacy."""
    pair_id: str
    block_id: str
    side: str
    score: float


@dataclass(frozen=True)
class Estimate:
    value: float
    ci_lower: float | None
    ci_upper: float | None
    n_pairs: int
    n_blocks: int


@dataclass(frozen=True)
class PairedComparison:
    method: Estimate
    reference: Estimate
    delta_w: Estimate
    headroom: float


def _pair_table(rows: Iterable[PairScore]) -> dict[str, tuple[str, float, float]]:
    pending: dict[str, dict[str, float]] = {}
    blocks: dict[str, str] = {}
    for row in rows:
        if not row.pair_id or not row.block_id:
            raise ValueError("pair_id and block_id must be nonempty")
        side = row.side.upper()
        if side not in {"B", "C"}:
            raise ValueError(f"Unknown side {row.side!r} for {row.pair_id}")
        value = float(row.score)
        if not isfinite(value):
            raise ValueError(f"Non-finite score in {row.pair_id}")
        if row.pair_id in blocks and blocks[row.pair_id] != row.block_id:
            raise ValueError(f"Inconsistent block for {row.pair_id}")
        blocks[row.pair_id] = row.block_id
        sides = pending.setdefault(row.pair_id, {})
        if side in sides:
            raise ValueError(f"Duplicate side {side} for {row.pair_id}")
        sides[side] = value
    if not pending:
        raise ValueError("No observations")
    pairs = {}
    for pair_id, sides in pending.items():
        if set(sides) != {"B", "C"}:
            raise ValueError(f"Incomplete B/C pair {pair_id}")
        pairs[pair_id] = (blocks[pair_id], sides["B"], sides["C"])
    return pairs


def _win(b: float, c: float) -> float:
    return 1.0 if c > b else (0.5 if c == b else 0.0)


def _block_values(table: dict[str, tuple[str, float, float]]) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for block_id, b, c in table.values():
        grouped[block_id].append(_win(b, c))
    return {key: sum(values) / len(values) for key, values in grouped.items()}


def _quantile(sorted_values: Sequence[float], p: float) -> float:
    index = (len(sorted_values) - 1) * p
    low, high = int(index), min(int(index) + 1, len(sorted_values) - 1)
    return sorted_values[low] + (index - low) * (sorted_values[high] - sorted_values[low])


def _interval(values: list[float], n_bootstrap: int, seed: int) -> tuple[float | None, float | None]:
    if n_bootstrap < 0:
        raise ValueError("n_bootstrap must be non-negative")
    if n_bootstrap == 0:
        return None, None
    rng = Random(seed)
    n = len(values)
    samples = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(n_bootstrap))
    return _quantile(samples, 0.025), _quantile(samples, 0.975)


def w_score(rows: Iterable[PairScore], *, n_bootstrap: int = 2000, seed: int = 20261108) -> Estimate:
    """Block-averaged W(C>B), with ties worth half a point."""
    table = _pair_table(rows)
    values = list(_block_values(table).values())
    low, high = _interval(values, n_bootstrap, seed)
    return Estimate(sum(values) / len(values), low, high, len(table), len(values))


def compare_to_reference(
    method_rows: Iterable[PairScore],
    reference_rows: Iterable[PairScore],
    *,
    n_bootstrap: int = 2000,
    seed: int = 20261108,
) -> PairedComparison:
    """Paired delta-W on common complete pairs, resampling matched blocks."""
    method = _pair_table(method_rows)
    reference = _pair_table(reference_rows)
    ids = set(method) & set(reference)
    if not ids:
        raise ValueError("No common complete pairs")
    method_common = {}
    reference_common = {}
    for pair_id in sorted(ids):
        if method[pair_id][0] != reference[pair_id][0]:
            raise ValueError(f"Mismatched blocks for common pair {pair_id}")
        method_common[pair_id] = method[pair_id]
        reference_common[pair_id] = reference[pair_id]
    mvals = _block_values(method_common)
    rvals = _block_values(reference_common)
    block_ids = sorted(mvals)
    mv = [mvals[k] for k in block_ids]
    rv = [rvals[k] for k in block_ids]
    dv = [mvals[k] - rvals[k] for k in block_ids]
    ml, mh = _interval(mv, n_bootstrap, seed)
    rl, rh = _interval(rv, n_bootstrap, seed)
    dl, dh = _interval(dv, n_bootstrap, seed)
    n = len(block_ids)
    n_pairs = len(ids)
    ref_w = sum(rv) / n
    return PairedComparison(
        Estimate(sum(mv) / n, ml, mh, n_pairs, n),
        Estimate(ref_w, rl, rh, n_pairs, n),
        Estimate(sum(dv) / n, dl, dh, n_pairs, n),
        1.0 - ref_w,
    )


def auroc(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Binary ROC AUC, with half credit for ties."""
    if len(labels) != len(scores) or not labels:
        raise ValueError("labels/scores must have equal nonzero lengths")
    if any(x not in (0, 1) for x in labels):
        raise ValueError("labels must be 0/1")
    values = [float(s) for s in scores]
    if any(not isfinite(s) for s in values):
        raise ValueError("scores must be finite")
    n_positive = sum(labels)
    n_negative = len(labels) - n_positive
    if not n_positive or not n_negative:
        raise ValueError("AUROC requires both classes")
    ordered = sorted(zip(values, labels))
    rank_positive = 0.0
    start = 0
    while start < len(ordered):
        stop = start + 1
        while stop < len(ordered) and ordered[stop][0] == ordered[start][0]:
            stop += 1
        average_rank = ((start + 1) + stop) / 2.0
        rank_positive += sum(y for _, y in ordered[start:stop]) * average_rank
        start = stop
    return (rank_positive - n_positive * (n_positive + 1) / 2.0) / (n_positive * n_negative)
