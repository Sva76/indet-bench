"""CPU replay of the frozen Test U2 analysis from the original results ZIP.

Re-implements, with NumPy only, the analysis cell of
``TestU2_istruzione_4_modelli_v2.ipynb`` (``with_scores``, ``wide_pairs``,
``condition_metrics``, ``contrast``, ``analyse``, ``export_total``) and
compares every recomputed statistic with ``esiti.json``. The input is the
archived per-row ``punteggi.csv``: no model is run and nothing is refitted.

Fields that depend on the GPU run itself (tokenizer lengths behind
``scarti_prompt``, the 24-value alignment with Test U, software versions)
cannot be recomputed from the scores and are reported as not replayed.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from io import TextIOWrapper
from math import isfinite
from zipfile import ZipFile

import numpy as np

from .archive_safety import check_zip_archive
from .replay import BOOT, SEED

CONDITIONS = ("PS", "PN", "SS", "SN")
HYPOTHESES = ("HI1", "HI2", "HI3")
LABELS = ("YES", "NO", "UNKNOWN")
# W of V2 in Test U, rounded as written in the notebook (alignment check of P+S).
W_V2_TEST_U = {"qwen": 0.91375, "mistral": 0.83375, "olmo": 0.73625, "llama": 0.83875}


def bootstrap_per_story(per_story, seed=SEED, n_boot=BOOT):
    """``per_story`` is a list of (story_id, value), already sorted by story."""
    x = np.asarray([v for _, v in per_story], float)
    n = len(x)
    if not n:
        return {"storie": 0, "stima": None, "ci95": None}
    ci = None
    if n > 1:
        rng = np.random.default_rng(seed)
        b = x[rng.integers(0, n, (n_boot, n))].mean(axis=1)
        ci = np.quantile(b, [.025, .975]).tolist()
    return {"storie": n, "stima": float(x.mean()), "ci95": ci}


def verdict(stat, null, minimum):
    if stat["ci95"] is None:
        return "NON VALUTABILE"
    lo, hi = stat["ci95"]
    if lo > null and stat["stima"] >= minimum:
        return "CONFERMATA"
    return "NON CONFERMATA" if hi <= null else "NON CONCLUSIVA"


def with_scores(rows):
    out = []
    for r in rows:
        probs = np.array([float(r["p_" + k]) for k in LABELS])
        norm = probs / max(probs.sum(), 1e-300)
        s = dict(r)
        for k in LABELS:
            s["p_" + k] = float(r["p_" + k])
        s["mass_total"] = float(r["mass_total"])
        s["meno_p_massima"] = float(-norm.max())
        s["entropia"] = float(-(norm * np.log(np.maximum(norm, 1e-300))).sum())
        s["is_unknown"] = r["parsed"] == "UNKNOWN"
        s["ok"] = r["parsed"] == r["condition"]
        out.append(s)
    return out


def wide_pairs(rows, score):
    """Pivot of B/C rows on (story_id, pair_key); incomplete or NaN pairs dropped."""
    wide = {}
    for r in rows:
        if r["kind"] not in ("B", "C"):
            continue
        cell = wide.setdefault((r["story_id"], r["pair_key"]), {})
        if r["kind"] in cell:
            raise ValueError("Duplicate pivot entry %r" % ((r["story_id"], r["pair_key"], r["kind"]),))
        cell[r["kind"]] = (r[score], r["is_unknown"])
    return {k: v for k, v in sorted(wide.items())
            if len(v) == 2 and all(isfinite(v[kind][0]) for kind in ("B", "C"))}


def pair_wins(wide, mask=None):
    return {k: float(v["C"][0] > v["B"][0]) + .5 * (v["C"][0] == v["B"][0])
            for k, v in wide.items() if mask is None or mask(v)}


def story_means(wins):
    groups = defaultdict(list)
    for (story, _), w in wins.items():
        groups[story].append(w)
    return [(s, float(np.mean(groups[s]))) for s in sorted(groups)]


def story_wins(wide, mask=None, **boot):
    wins = pair_wins(wide, mask)
    return dict(bootstrap_per_story(story_means(wins), **boot), coppie=len(wins))


def auroc(labels, values):
    """Mann-Whitney AUROC with average ranks for ties (equals sklearn's).

    Average ranks are half-integers, so the rank sum is exact and the
    result does not depend on how ties are ordered.
    """
    labels = np.asarray(labels, bool)
    values = np.asarray(values, float)
    n1, n0 = int(labels.sum()), int((~labels).sum())
    if not n1 or not n0:
        return None
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    ends = np.cumsum(counts)
    average = ends - (counts - 1) / 2
    ranks = average[inverse.ravel()]
    return float((ranks[labels].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def condition_metrics(rows, **boot):
    wide = wide_pairs(rows, "p_UNKNOWN")
    wins = pair_wins(wide)
    W = story_wins(wide, **boot)
    b_c = [r for r in rows if r["kind"] in ("B", "C")]
    au = auroc([r["kind"] == "C" for r in b_c], [r["p_UNKNOWN"] for r in b_c])
    equal = {
        "entrambi_UNKNOWN": story_wins(wide, lambda v: v["B"][1] and v["C"][1], **boot),
        "nessuno_UNKNOWN": story_wins(wide, lambda v: not v["B"][1] and not v["C"][1], **boot),
        "senza_UNKNOWN_su_C": story_wins(wide, lambda v: not v["C"][1], **boot),
    }
    alternative = {m: story_wins(wide_pairs(rows, m), **boot) for m in ("meno_p_massima", "entropia")}
    by_kind = defaultdict(list)
    by_pos = defaultdict(list)
    for r in rows:
        by_kind[r["kind"]].append(r)
        by_pos[(r["kind"], r["position"])].append(r)
    behavior = [{"kind": k, "n": len(g), "quota_unknown": float(np.mean([r["is_unknown"] for r in g])),
                 "acc": float(np.mean([r["ok"] for r in g])),
                 "quota_altro": float(np.mean([r["parsed"] == "ALTRO" for r in g])),
                 "p_UNKNOWN_mediana": float(np.median([r["p_UNKNOWN"] for r in g]))}
                for k, g in sorted(by_kind.items())]
    by_position = [{"kind": k, "position": p, "n": len(g),
                    "quota_unknown": float(np.mean([r["is_unknown"] for r in g]))}
                   for (k, p), g in sorted(by_pos.items())]
    return wins, {"W": W, "AUROC": au, "W_a_parita_di_risposta": equal, "alternative": alternative,
                  "comportamento": behavior, "comportamento_per_posizione": by_position}


def contrast(wins, signs, **boot):
    common = None
    for c in signs:
        common = set(wins[c]) if common is None else common & set(wins[c])
    diff = {k: sum(s * wins[c][k] for c, s in signs.items()) for k in common}
    out = bootstrap_per_story(story_means(diff), **boot)
    out["coppie"] = len(common)
    return out


def analyse(rows, **boot):
    t = with_scores(rows)
    wins, stats = {}, {}
    for cond in CONDITIONS:
        wins[cond], stats[cond] = condition_metrics([r for r in t if r["set"] == cond], **boot)
    d = lambda a, b: contrast(wins, {a: 1, b: -1}, **boot)  # noqa: E731
    hi1 = dict(stats["PN"]["W"], esito=verdict(stats["PN"]["W"], .5, .60))
    hi2 = d("PS", "PN")
    hi2["esito"] = verdict(hi2, 0, .05)
    hi3 = d("PN", "SN")
    hi3["esito"] = verdict(hi3, 0, .05)
    inter = contrast(wins, {"PS": 1, "PN": -1, "SS": -1, "SN": 1}, **boot)
    descr = {"interazione": inter, "PS_meno_SS": d("PS", "SS"), "SS_meno_SN": d("SS", "SN")}
    low_mass = float(np.mean([r["mass_total"] < .90 for r in t]))
    return {"condizioni": stats, "HI1": hi1, "HI2": hi2, "HI3": hi3, "descrittivi": descr,
            "quota_massa_bassa": low_mass, "cautela_massa": low_mass > .05}


def compare(expected, actual, path, errors, tolerance=1e-10):
    """Recursive comparison; returns the number of leaf values checked."""
    if isinstance(actual, dict):
        if not isinstance(expected, dict) or set(expected) != set(actual):
            errors.append({"field": path, "expected": sorted(expected) if isinstance(expected, dict) else expected,
                           "actual": sorted(actual)})
            return 1
        return sum(compare(expected[k], actual[k], f"{path}.{k}", errors, tolerance) for k in actual)
    if isinstance(actual, list):
        if not isinstance(expected, list) or len(expected) != len(actual):
            errors.append({"field": path, "expected": expected, "actual": actual})
            return 1
        return sum(compare(e, a, f"{path}[{i}]", errors, tolerance) for i, (e, a) in enumerate(zip(expected, actual)))
    numeric = (isinstance(actual, (int, float)) and not isinstance(actual, bool)
               and isinstance(expected, (int, float)) and not isinstance(expected, bool))
    if numeric:
        if not (isfinite(expected) and isfinite(actual)):
            # NaN or inf on either side: only an identical non-finite value matches
            same = (expected != expected and actual != actual) or expected == actual
            if not same:
                errors.append({"field": path, "expected": expected, "actual": actual})
        elif abs(expected - actual) > tolerance:
            errors.append({"field": path, "expected": expected, "actual": actual})
    elif expected != actual:
        errors.append({"field": path, "expected": expected, "actual": actual})
    return 1


def read_scores(z):
    with z.open("punteggi.csv") as f:
        rows = list(csv.DictReader(TextIOWrapper(f, encoding="utf-8", newline="")))
    by_model = defaultdict(list)
    for r in rows:
        by_model[r["modello"]].append(r)
    return by_model


def replay_u2(path, seed=SEED, n_boot=BOOT):
    errors, checked, models = [], 0, {}
    with ZipFile(path) as z:
        check_zip_archive(z)
        esiti = json.loads(z.read("esiti.json"))
        by_model = read_scores(z)
    if set(by_model) != {k for k, r in esiti["modelli"].items() if r["valutabile"]}:
        errors.append({"field": "modelli", "expected": sorted(esiti["modelli"]), "actual": sorted(by_model)})
    for key in sorted(by_model):
        original = esiti["modelli"][key]
        computed = analyse(by_model[key], seed=seed, n_boot=n_boot)
        w_ps = computed["condizioni"]["PS"]["W"]["stima"]
        computed["allineamento.W_P+S"] = {"stima": w_ps, "test_U": W_V2_TEST_U[key],
                                          "superato": abs(w_ps - W_V2_TEST_U[key]) <= .005}
        expected = {k: original[k] for k in computed if k != "allineamento.W_P+S"}
        expected["allineamento.W_P+S"] = original["allineamento"]["W_P+S"]
        n = compare(expected, computed, key, errors)
        checked += n
        models[key] = {"righe": len(by_model[key]), "valori_controllati": n,
                       **{h: computed[h]["esito"] for h in HYPOTHESES}}
    scorecard = {h: [k for k, r in esiti["modelli"].items() if r["valutabile"] and models.get(k, {}).get(h) == "CONFERMATA"]
                 for h in HYPOTHESES}
    # esiti.json was written with sort_keys, so the run order of the lists is not recoverable: compare as sets.
    checked += compare({h: sorted(v) for h, v in esiti["conferme"].items()},
                       {h: sorted(v) for h, v in scorecard.items()}, "conferme", errors)
    return {
        "test": "U2", "passed": not errors, "values_checked": checked, "errors": errors[:50],
        "n_errors": len(errors), "models": models, "seed": seed, "n_boot": n_boot,
        "not_replayed": ["scarti_prompt (needs the tokenizers)", "allineamento.valori (24 GPU re-runs)",
                         "software and GPU metadata"],
        "scope": "Test U2 analysis from the archived per-row scores; models are not re-run",
    }
