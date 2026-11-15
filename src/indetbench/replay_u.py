"""CPU replay of the frozen Test U analysis from the original results ZIP.

Re-implements, with NumPy only, the analysis functions of
``TestU_astensione_4_modelli_v3.ipynb`` (``benchmark_metrics`` with its
per-cell detail, ``permutation_w``, ``fit_threshold``,
``transferred_threshold`` with the joint bootstrap, ``lexical_metrics``,
``accuracy_by_label``, ``pick_candidate``, ``export_total``) and compares
every recomputed value with ``esiti.json`` and with each model's
``celle.csv``. The input is the archived per-row ``punteggi.csv``, which
includes the SQuAD-detector score of the lexical "or" rows: no model is
run, and the SQuAD detector is not refitted.

Not recomputable from the scores: the SQuAD detector fit and its AUROC
(``rilevatore_squad``), the tokenizer lengths behind ``scarti_prompt``,
the tokenizer audit and software metadata. The polarity hold-out was not
run in the original (no candidate reached 0.90), so only the screening
that decided this is replayed.
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
from .replay_u2 import LABELS, auroc, bootstrap_per_story, compare, story_means, verdict

CANDIDATES = ("N1", "N2", "N3")
MODELS = ("qwen", "mistral", "olmo", "llama")


def with_scores(rows):
    out = []
    for r in rows:
        s = dict(r)
        probs = np.array([float(r["p_" + k]) for k in LABELS])
        for k in LABELS:
            s["p_" + k] = float(r["p_" + k])
        norm = probs / max(probs.sum(), 1e-300)
        s["mass_total"] = float(r["mass_total"])
        s["meno_p_massima"] = float(-norm.max())
        s["entropia"] = float(-(norm * np.log(np.maximum(norm, 1e-300))).sum())
        s["is_c"] = r["kind"] == "C"
        s["is_unknown"] = r["parsed"] == "UNKNOWN"
        s["ok"] = r["parsed"] == r["condition"]
        s["altro"] = r["parsed"] == "ALTRO"
        s["prompt_tokens"] = int(r["prompt_tokens"])
        s["score_squad"] = float(r["score_squad"]) if r.get("score_squad") not in (None, "") else float("nan")
        out.append(s)
    return out


def pair_table(rows, score, key):
    """pivot(index=[story_id, pair_key], columns=key, values=score); refuses duplicates like pandas."""
    wide = {}
    for r in rows:
        cell = wide.setdefault((r["story_id"], r["pair_key"]), {})
        if r[key] in cell:
            raise ValueError("Duplicate pivot entry %r" % ((r["story_id"], r["pair_key"], r[key]),))
        cell[r[key]] = r[score]
    return wide


def pair_wins(rows, score, left, right, key):
    wins = {}
    for k, cell in sorted(pair_table(rows, score, key).items()):
        a, b = cell.get(left, float("nan")), cell.get(right, float("nan"))
        if isfinite(a) and isfinite(b):
            wins[k] = float(a > b) + .5 * (a == b)
    return wins


def compare_pairs(rows, score, left, right, key, **boot):
    wins = pair_wins(rows, score, left, right, key)
    return dict(bootstrap_per_story(story_means(wins), **boot), coppie=len(wins))


def permutation_w(wins, seed=SEED):
    if not wins:
        return None
    x = np.asarray([v for _, v in story_means(wins)]) - .5
    rng = np.random.default_rng(seed)
    shuffled = (rng.choice([-1, 1], size=(2000, len(x))) * x).mean(axis=1)
    return float((1 + np.count_nonzero(shuffled >= x.mean() - 1e-12)) / (1 + len(shuffled)))


def groups(rows, *keys):
    out = defaultdict(list)
    for r in rows:
        out[tuple(r[k] for k in keys)].append(r)
    return sorted(out.items())


def benchmark_metrics(rows, **boot):
    stats, detail = [], []
    for (scope, polarity), group in groups(rows, "set", "polarity"):
        for (family, variant, position), cell in groups(group, "family", "variant", "position"):
            for measure in ("p_UNKNOWN", "meno_p_massima", "entropia"):
                detail.append(dict(set=scope, polarity=polarity, family=family, variant=variant, position=position,
                                   misura=measure, **compare_pairs(cell, measure, "C", "B", "kind", **boot)))
        b_c = [r for r in group if r["kind"] in ("B", "C")]
        wins = pair_wins(b_c, "p_UNKNOWN", "C", "B", "kind")
        w = dict(bootstrap_per_story(story_means(wins), **boot), coppie=len(wins))
        unanswered = {r["pair_key"] for r in group if r["kind"] == "C" and not r["is_unknown"]}
        strict_w = compare_pairs([r for r in group if r["pair_key"] in unanswered], "p_UNKNOWN", "C", "B", "kind", **boot)
        complete = {pk for _, pk in wins}
        bc_full = [r for r in b_c if r["pair_key"] in complete]
        au = auroc([r["is_c"] for r in bc_full], [r["p_UNKNOWN"] for r in bc_full]) if bc_full else None
        behavior = [dict(kind=kind, n=len(k), acc=float(np.mean([r["ok"] for r in k])),
                         quota_unknown=float(np.mean([r["is_unknown"] for r in k])),
                         n_unknown=sum(r["is_unknown"] for r in k), n_altro=sum(r["altro"] for r in k),
                         n_yes=sum(r["parsed"] == "YES" for r in k), n_no=sum(r["parsed"] == "NO" for r in k))
                    for (kind,), k in groups(group, "kind")]
        by_position = [dict(kind=kind, position=position, n=len(k),
                            quota_unknown=float(np.mean([r["is_unknown"] for r in k])),
                            p_UNKNOWN_mediana=float(np.median([r["p_UNKNOWN"] for r in k])))
                       for (kind, position), k in groups(group, "kind", "position")]
        alternative = {m: compare_pairs(group, m, "C", "B", "kind", **boot) for m in ("meno_p_massima", "entropia")}
        stats.append(dict(set=scope, polarity=polarity, W=w, AUROC=au, comportamento=behavior,
                          comportamento_per_posizione=by_position, W_senza_UNKNOWN_generato=strict_w,
                          alternative=alternative, p_perm=permutation_w(wins, boot.get("seed", SEED)),
                          esito="DESCRITTIVA" if scope == "V3" or (scope == "POL" and polarity == "granted")
                          else verdict(w, .5, .60)))
    return stats, detail


def fit_threshold(scores, is_c, weights=None):
    values, inverse = np.unique(scores, return_inverse=True)
    w = np.ones(len(scores)) if weights is None else weights
    size = np.bincount(inverse, weights=w, minlength=len(values))[::-1]
    positive = np.bincount(inverse, weights=w * is_c, minlength=len(values))[::-1]
    keep = size > 0
    values, size, positive = values[::-1][keep], size[keep], positive[keep]
    negative = size - positive
    assert positive.sum() > 0 and negative.sum() > 0
    tpr = np.r_[0, positive.cumsum()] / positive.sum()
    fpr = np.r_[0, negative.cumsum()] / negative.sum()
    tau = np.r_[values.astype(float), np.nextafter(float(values[-1]), -np.inf)]
    ba = .5 * (tpr + 1 - fpr)
    best = int(np.argmax(np.round(ba, 12)))
    return float(tau[best]), float(ba[best])


def transferred_threshold(rows, score="p_UNKNOWN", seed=SEED, n_boot=BOOT):
    add = [r for r in rows if r["set"] == "ADD"]
    sc_add = np.asarray([r[score] for r in add], float)
    c_add = np.asarray([r["is_c"] for r in add], float)
    tau, ba_add = fit_threshold(sc_add, c_add)
    by_story = defaultdict(list)
    for i, r in enumerate(add):
        by_story[r["story_id"]].append(i)
    rows_by_story = [np.asarray(by_story[s]) for s in sorted(by_story)]
    rng_add = np.random.default_rng(seed + 1)
    taus = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng_add.integers(0, len(rows_by_story), len(rows_by_story))
        counts = np.bincount(np.concatenate([rows_by_story[i] for i in pick]), minlength=len(add)).astype(float)
        taus[b] = fit_threshold(sc_add, c_add, counts)[0]
    out = []
    for name in ("V1", "V2", "V3"):
        t = [r for r in rows if r["set"] == name]
        stories = sorted({r["story_id"] for r in t})
        pos = {s: i for i, s in enumerate(stories)}
        n = np.zeros((len(stories), 2))
        hit_rule = np.zeros((len(stories), 2))
        hit_model = np.zeros((len(stories), 2))
        for r in t:
            i, c = pos[r["story_id"]], int(r["is_c"])
            n[i, c] += 1
            hit_rule[i, c] += (r[score] > tau) == r["is_c"]
            hit_model[i, c] += r["is_unknown"] == r["is_c"]
        present = {int(r["is_c"]) for r in t}
        if not t or present != {0, 1}:
            result = dict(storie=len(stories), stima=None, ci95=None)
            ba_rule = ba_model = None
        else:
            ba_rule = float((hit_rule.sum(axis=0) / n.sum(axis=0)).mean())
            ba_model = float((hit_model.sum(axis=0) / n.sum(axis=0)).mean())
            ci = ci_cond = None
            if len(n) > 1:
                rng = np.random.default_rng(seed)
                indices = rng.integers(0, len(n), (n_boot, len(n)))
                denom = n[indices].sum(axis=1)
                good = (denom > 0).all(axis=1)
                delta = ((hit_rule - hit_model)[indices].sum(axis=1)[good] / denom[good]).mean(axis=1)
                if len(delta):
                    ci_cond = np.quantile(delta, [.025, .975]).tolist()
                srow = np.asarray([pos[r["story_id"]] for r in t])
                cls = np.asarray([int(r["is_c"]) for r in t])
                sc_ = np.asarray([r[score] for r in t], float)
                cell = srow * 2 + cls
                deltas = []
                for b in range(n_boot):
                    if not good[b]:
                        continue
                    hr = np.bincount(cell, weights=((sc_ > taus[b]) == cls.astype(bool)),
                                     minlength=2 * len(stories)).reshape(-1, 2)
                    num = (hr - hit_model)[indices[b]].sum(axis=0)
                    deltas.append((num / denom[b]).mean())
                if deltas:
                    ci = np.quantile(deltas, [.025, .975]).tolist()
            result = dict(storie=len(n), stima=ba_rule - ba_model, ci95=ci, ci95_condizionato=ci_cond)
        out.append(dict(set=name, tau=tau, BA_ADD_in_sample=ba_add, BA_soglia=ba_rule, BA_modello=ba_model,
                        tau_bootstrap_ci95=np.quantile(taus, [.025, .975]).tolist(), **result,
                        esito="DESCRITTIVA" if name == "V3" or score != "p_UNKNOWN" else verdict(result, 0, .05)))
    return out


def lexical_metrics(rows, **boot):
    out = []
    scopes = [("tutte", rows), ("OR", [r for r in rows if r["family"] == "OR"]),
              ("senza_OR", [r for r in rows if r["family"] != "OR"])]
    for name, group in scopes:
        lengths = pair_table(group, "prompt_tokens", "lex_case")
        for hyp, a, b in (("HO1", "A_or", "A_and"), ("HO2", "B_or", "B_set"),
                          ("due_valori", "B_set", "A_and"), ("C_vs_B_set", "C_set", "B_set"),
                          ("C_vs_B_or", "C_or", "B_or")):
            diff = {k: v[a] - v[b] for k, v in sorted(lengths.items()) if a in v and b in v}
            for score in ("score_squad", "p_UNKNOWN"):
                comparison = group
                if hyp.startswith("C_vs_B"):
                    same = {pk for (_, pk), d in diff.items() if d == 0}
                    comparison = [r for r in group if r["pair_key"] in same]
                stat = compare_pairs(comparison, score, a, b, "lex_case", **boot)
                decisive = hyp in ("HO1", "HO2") and score == "score_squad" and name == "tutte"
                out.append(dict(scope=name, ipotesi=hyp, misura=score, confronto=f"{a} > {b}",
                                delta_token_medio=float(np.mean(list(diff.values()))) if diff else None,
                                **stat, esito=verdict(stat, .5, .60) if decisive else "DESCRITTIVA"))
    gen = [dict(lex_case=case, n=len(g), quota_UNKNOWN=float(np.mean([r["parsed"] == "UNKNOWN" for r in g])))
           for (case,), g in groups([r for r in rows if r["lex_case"] in ("C_or", "C_set")], "lex_case")]
    return out, gen


def accuracy_by_label(rows):
    order = list(dict.fromkeys(r["polarity"] for r in rows))  # pandas unique(): order of appearance
    output = []
    for p in order:
        acc = {}
        for label in ("YES", "NO"):
            g = [r["parsed"] == r["condition"] for r in rows if r["polarity"] == p and r["condition"] == label]
            acc[label] = (float(np.mean(g)), len(g))
        output.append(dict(polarity=p, acc_yes=acc["YES"][0], n_yes=acc["YES"][1], acc_no=acc["NO"][0],
                           n_no=acc["NO"][1], minimo=float(min(acc["YES"][0], acc["NO"][0]))))
    return output


def pick_candidate(screen):
    by_candidate = {r["polarity"]: r["minimo"] for r in screen}
    best = max(CANDIDATES, key=by_candidate.__getitem__)
    return best if by_candidate[best] >= .90 else None


def read_csv_member(z, name):
    with z.open(name) as f:
        return list(csv.DictReader(TextIOWrapper(f, encoding="utf-8", newline="")))


def cells_as_archived(z, key):
    rows = []
    for r in read_csv_member(z, f"{key}/celle.csv"):
        rows.append(dict(r, storie=int(r["storie"]), stima=None if r["stima"] == "" else float(r["stima"]),
                         ci95=None if r["ci95"] == "" else json.loads(r["ci95"]), coppie=int(r["coppie"])))
    return rows


def analyse_model(rows, seed=SEED, n_boot=BOOT):
    t = with_scores(rows)
    main = [r for r in t if r["set"] in ("ADD", "V1", "V2", "V3")]
    screen_raw = [r for r in t if r["set"] == "SCR"]
    lex_raw = [r for r in t if r["set"] == "O"]
    boot = dict(seed=seed, n_boot=n_boot)
    benchmark, by_cell = benchmark_metrics(main, **boot)
    threshold = transferred_threshold(main, seed=seed, n_boot=n_boot)
    threshold_alt = {s: transferred_threshold(main, s, seed=seed, n_boot=n_boot) for s in ("meno_p_massima", "entropia")}
    screen = accuracy_by_label(screen_raw)
    chosen = pick_candidate(screen)
    lex, lex_gen = lexical_metrics(lex_raw, **boot)
    low_mass = float(np.mean([r["mass_total"] < .90 for r in t]))
    result = dict(benchmark=benchmark, soglia=threshold, soglie_descrittive=threshold_alt, controllo_or=lex,
                  or_generazione=lex_gen, screening=screen, quota_massa_bassa=low_mass, cautela_massa=low_mass > .05)
    if chosen is None:
        result["polarita"] = dict(candidato=None, esito="NON VALUTABILE", coerenza_AB=None)
        result["polarita_benchmark"] = []
    return result, by_cell, chosen


def replay_u(path, seed=SEED, n_boot=BOOT):
    errors, checked, models = [], 0, {}
    with ZipFile(path) as z:
        check_zip_archive(z)
        esiti = json.loads(z.read("esiti.json"))
        by_model = defaultdict(list)
        for r in read_csv_member(z, "punteggi.csv"):
            by_model[r["modello"]].append(r)
        archived_cells = {k: cells_as_archived(z, k) for k in by_model}
    if set(by_model) != set(esiti["modelli"]):
        errors.append({"field": "modelli", "expected": sorted(esiti["modelli"]), "actual": sorted(by_model)})
    for key in sorted(by_model):
        original = esiti["modelli"][key]
        computed, cells, chosen = analyse_model(by_model[key], seed, n_boot)
        if chosen is not None:
            errors.append({"field": key + ".polarita", "note": "candidate chosen: hold-out not archived", "actual": chosen})
        n = compare({k: original[k] for k in computed}, computed, key, errors)
        n += compare(archived_cells[key], cells, key + "/celle.csv", errors)
        checked += n
        models[key] = {"righe": len(by_model[key]), "valori_controllati": n,
                       "HU1": {b["set"]: b["esito"] for b in computed["benchmark"]},
                       "HU2": {s["set"]: s["esito"] for s in computed["soglia"]},
                       "HO": {c["ipotesi"]: c["esito"] for c in computed["controllo_or"]
                              if c["scope"] == "tutte" and c["misura"] == "score_squad" and c["ipotesi"] in ("HO1", "HO2")},
                       "polarita": computed.get("polarita", {}).get("esito")}
    for row in esiti["sintesi"]:
        section = "HU1" if row["ipotesi"] == "HU1" else "HU2"
        confirmed = sorted(k for k, m in models.items() if m[section].get(row["insieme"]) == "CONFERMATA")
        actual = dict(row, confermati=confirmed, criterio_3_su_4=len(confirmed) >= 3,
                      n_modelli_completati=len(models), denominatore=4)
        # esiti.json lists models in run order: compare the confirmed models as a set.
        checked += compare(dict(row, confermati=sorted(row["confermati"])), actual,
                           f"sintesi.{row['ipotesi']}.{row['insieme']}", errors)
    return {
        "test": "U", "passed": not errors, "values_checked": checked, "errors": errors[:50],
        "n_errors": len(errors), "models": models, "seed": seed, "n_boot": n_boot,
        "not_replayed": ["rilevatore_squad (SQuAD detector fit and AUROC: needs the model and SQuAD)",
                         "scarti_prompt (needs the tokenizers)", "audit_tokenizzazione and software metadata",
                         "polarity hold-out (not run in the original: no candidate reached 0.90)"],
        "scope": "Test U analysis from the archived per-row scores; models are not re-run",
    }
