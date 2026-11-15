"""CPU replay of Test C HC4 (answer support) from the original results ZIP.

Two checks, both from archived material only:

1. Answer labels. The frozen rule-based classifier of the original run
   (``tc_classifica.py``, rules ``C-classifica-2``, vendored unchanged as
   ``tc_classifica_frozen.py``; its bytes are checked against the copy in
   the archive) is re-run on every archived answer: the reference
   generations and the LM-Polygraph greedy answers of M1 for the four
   models, and the M4 generations of Llama. The labels and details must
   equal ``risposte_C.csv``, and the category counts and B accuracies
   must equal ``esiti_C.json``.
2. HC4 statistics. For each of the 38 method/model results, the five
   AUROC sets of HC4 (within C, within B and three descriptive ones),
   with passage-bootstrap intervals and verdicts, are recomputed from
   those labels and the archived scores, and compared with ``esiti_C.json``.

Scope: this shows that HC4 follows from the archived answers, the frozen
rules and the archived scores. It does not show that the rules label the
answers correctly: that needs human annotation. ``annotation_agreement``
recomputes the agreement of the classifier with a human-labelled sample
(the original 100-answer sample gave 0.680, protocol threshold 0.90).
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from io import TextIOWrapper
from math import isfinite

import numpy as np

from . import tc_classifica_frozen as K
from .replay import BOOT, SEED, c_archive, c_sources, read_json
from .replay_u2 import auroc, compare

FAM_MAIN = ("DUE", "CONF", "LOG")
MIN_ANSWERS = 30     # MIN_RISPOSTE_HC4 in configurazione_notebook.json
MIN_PASSAGES = 15    # MIN_PASSAGGI_HC4
M1_ESTIMATORS = ("MSP", "Perplexity", "MeanTokenEntropy", "SemanticEntropy", "PTrue")
MODELS = ("qwen", "mistral", "olmo", "llama")


def finite(x):
    return x is not None and isinstance(x, (int, float)) and isfinite(x)


def classify(rows, passages, answers):
    cat, det = {}, {}
    for r in rows:
        if r["row_id"] not in answers:
            continue
        if r["insieme"].startswith("sintetico"):
            info = K.info_sintetico(passages[r["passaggio_id"]], r["famiglia"], r["kind"])
            c, d = K.classifica_sintetico(answers[r["row_id"]], info)
        else:
            c, d = K.classifica_naturale(answers[r["row_id"]], r)
        cat[r["row_id"]], det[r["row_id"]] = c, d
    return cat, det


def category_counts(rows, categories):
    out = defaultdict(Counter)
    for r in rows:
        out[f"{r['insieme']}|{r['famiglia']}|{r['kind']}"][categories.get(r["row_id"], "mancante")] += 1
    return {k: dict(v) for k, v in sorted(out.items())}


def accuracy_B(rows, categories):
    per = defaultdict(lambda: [0, 0])
    for r in rows:
        if r["kind"] != "B":
            continue
        for k in (r["famiglia"], "tutte"):
            per[k][1] += 1
            per[k][0] += categories.get(r["row_id"]) == "corretta"
    return {k: dict(corrette=a, totale=n, accuratezza=(a / n if n else None)) for k, (a, n) in sorted(per.items())}


def auroc_by_passage(pos, neg, seed, n_boot):
    pos = [(p, s) for p, s in pos if finite(s)]
    neg = [(p, s) for p, s in neg if finite(s)]
    n_pos_p, n_neg_p = len({p for p, _ in pos}), len({p for p, _ in neg})
    stima = auroc([1] * len(pos) + [0] * len(neg), [s for _, s in pos] + [s for _, s in neg]) if pos and neg else None
    out = dict(n_pos=len(pos), n_neg=len(neg), passaggi_pos=n_pos_p, passaggi_neg=n_neg_p, stima=stima, ci95=None)
    ok = len(pos) >= MIN_ANSWERS and len(neg) >= MIN_ANSWERS and n_pos_p >= MIN_PASSAGES and n_neg_p >= MIN_PASSAGES
    out["valutabile"] = ok
    if not ok or stima is None:
        return out
    passages = sorted({p for p, _ in pos} | {p for p, _ in neg})
    idx = {p: i for i, p in enumerate(passages)}
    gp, gn = defaultdict(list), defaultdict(list)
    for p, s in pos:
        gp[idx[p]].append(s)
    for p, s in neg:
        gn[idx[p]].append(s)
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(passages), len(passages))
        a = [s for i in pick for s in gp.get(i, ())]
        b = [s for i in pick for s in gn.get(i, ())]
        if a and b:
            estimates.append(auroc([1] * len(a) + [0] * len(b), a + b))
    if estimates:
        out["ci95"] = [float(q) for q in np.quantile(estimates, [.025, .975])]
    return out


def verdict_hc4(stat):
    if not stat.get("valutabile") or stat.get("ci95") is None:
        return "NON VALUTABILE"
    lo, hi = stat["ci95"]
    if lo > .5 and stat["stima"] >= .70:
        return "CONFERMATA"
    return "NON CONFERMATA" if hi <= .5 else "NON CONCLUSIVA"


def hc4_sets(synthetic, categories, scores):
    def pick(rule):
        return [(r["passaggio_id"], scores.get(r["row_id"])) for r in synthetic if rule(r, categories.get(r["row_id"]))]
    in_c = lambda r: r["kind"] == "C" and r["famiglia"] in FAM_MAIN  # noqa: E731
    in_b = lambda r: r["kind"] == "B"  # noqa: E731
    unsupported_c = lambda r, c: in_c(r) and c in K.NON_SUPPORTATE_C  # noqa: E731
    correct_b_main = lambda r, c: in_b(r) and r["famiglia"] in FAM_MAIN and c in K.SUPPORTATE_B  # noqa: E731
    return dict(
        entro_C=(pick(unsupported_c), pick(lambda r, c: in_c(r) and c in K.SUPPORTATE_C)),
        entro_B=(pick(lambda r, c: in_b(r) and c in K.NON_SUPPORTATE_B), pick(lambda r, c: in_b(r) and c in K.SUPPORTATE_B)),
        entro_C_con_astensioni=(pick(unsupported_c),
                                pick(lambda r, c: in_c(r) and (c in K.SUPPORTATE_C or c == "astensione"))),
        C_non_supportate_contro_B_corrette=(pick(unsupported_c), pick(correct_b_main)),
        C_contro_B_con_astensioni=(pick(unsupported_c),
                                   pick(lambda r, c: correct_b_main(r, c) or (in_c(r) and c == "astensione"))),
    )


def read_responses(z):
    with z.open("risposte_C.csv") as f:
        return list(csv.DictReader(TextIOWrapper(f, encoding="utf-8", newline="")))


def replay_c_hc4(path, seed=SEED, n_boot=BOOT):
    errors, checked = [], 0
    with c_archive(path) as z:
        original = read_json(z, "esiti_C.json")
        if original.get("versione") != "C-notebook-3-Csel8" or original.get("modalita") != "completo":
            raise ValueError("Only frozen Test C v3 full archive supported")
        frozen_rules = z.read("script/tc_classifica.py")
        rows = read_json(z, "dati/righe_C_selezionate.json")
        passages = read_json(z, "dati/passaggi_selezionati.json")
        if isinstance(passages, list):
            passages = {p["passaggio_id"]: p for p in passages}
        archived = read_responses(z)
        sources, _ = c_sources(z)
        m1 = {m: read_json(z, f"uscite/M1_{m}.json") for m in MODELS}
        m4 = read_json(z, "uscite/M4.json")
    with open(K.__file__, "rb") as f:
        if f.read() != frozen_rules:
            errors.append({"field": "tc_classifica.py", "note": "vendored rules differ from the archived script"})
    if original.get("regole_classificazione") != K.VERSIONE_REGOLE:
        errors.append({"field": "regole_classificazione", "expected": original.get("regole_classificazione"),
                       "actual": K.VERSIONE_REGOLE})
    synthetic = [r for r in rows if r["insieme"].startswith("sintetico")]
    natural = [r for r in rows if r["insieme"] == "naturale"]

    # 1. labels
    series = {}
    for m in MODELS:
        series[(m, "M1-riferimento")] = {r["row_id"]: r["generated"] for r in m1[m]["riferimento"]}
        series[(m, "M1-LM-Polygraph")] = {r["row_id"]: r["greedy_polygraph"] for r in m1[m]["polygraph"]}
    series[("llama", "M4-generazione")] = {g["row_id"]: g["generated"] for g in m4["generazione"]}
    labels = {k: classify(rows, passages, answers) for k, answers in series.items()}
    by_series = defaultdict(dict)
    for r in archived:
        by_series[(r["modello"], r["origine"])][r["row_id"]] = r
    label_stats = {}
    for key, (cat, det) in labels.items():
        arch = by_series.get(key, {})
        same = sum(arch.get(rid, {}).get("categoria") == c for rid, c in cat.items())
        same_detail = sum(rid in arch and json.loads(arch[rid]["dettagli"]) == json.loads(json.dumps(det[rid]))
                          for rid in cat)
        if same != len(cat) or same_detail != len(cat) or len(arch) != len(cat):
            errors.append({"field": "labels." + "/".join(key), "archived": len(arch), "recomputed": len(cat),
                           "same_label": same, "same_detail": same_detail})
        label_stats["/".join(key)] = {"answers": len(cat), "same_label": same, "same_detail": same_detail}
        checked += 2 * len(cat)
    for m in MODELS:
        cat = labels[(m, "M1-riferimento")][0]
        beh = original["comportamento"][m]
        computed = dict(categorie=category_counts(rows, cat), accuratezza_B_sintetico=accuracy_B(synthetic, cat),
                        accuratezza_B_naturale=accuracy_B(natural, cat),
                        quota_altro_sintetico=sum(cat.get(r["row_id"]) == "altro" for r in synthetic) / len(synthetic))
        checked += compare({k: beh[k] for k in computed}, computed, f"comportamento.{m}", errors)
        poly = labels[(m, "M1-LM-Polygraph")][0]
        common = sorted(cat.keys() & poly.keys())
        checked += compare(beh["confronto_M1_riferimento"]["categoria_uguale"],
                           sum(poly[k] == cat[k] for k in common), f"comportamento.{m}.categoria_uguale", errors)

    # 2. HC4 statistics
    results = []
    for row in original["risultati"]:
        method, model = row["metodo"], row["modello"]
        if "HC4" not in row:
            continue
        if method.startswith("M1-"):
            cat = labels[(model, "M1-LM-Polygraph")][0]
        elif method in ("M4-lin", "M4-LoRA"):
            cat = labels[("llama", "M4-generazione")][0]
        else:
            cat = labels[(model, "M1-riferimento")][0]
        hc0 = row.get("HC0")
        hc0_passed = bool(hc0 and hc0.get("superato"))
        computed = {}
        for name, (pos, neg) in hc4_sets(synthetic, cat, sources[(method, model)]).items():
            stat = auroc_by_passage(pos, neg, seed, n_boot)
            if name in ("entro_C", "entro_B"):
                stat["esito"] = verdict_hc4(stat) if hc0_passed else "NON VALUTABILE"
            computed[name] = stat
        checked += compare(row["HC4"], computed, f"HC4.{method}/{model}", errors)
        results.append({"metodo": method, "modello": model,
                        "entro_C": computed["entro_C"]["esito"], "entro_B": computed["entro_B"]["esito"]})
    return {
        "test": "C-HC4", "passed": not errors, "values_checked": checked, "errors": errors[:50],
        "n_errors": len(errors), "labels": label_stats, "hc4": results, "rules": K.VERSIONE_REGOLE,
        "scope": ("HC4 recomputed from the archived answers with the frozen classifier and the archived scores. "
                  "Correctness of the labels is not shown: classifier agreement with the owner's 100-answer "
                  "sample was 0.680 (threshold 0.90), and HC4 within C is confounded with passage family."),
    }


SUPPORTED_C = {"alternative", "attribuite"}
UNSUPPORTED_C = {"entrambi affermati", "un valore del contesto", "valore assente dal contesto"}


def hc4_class(category):
    return "supportata" if category in SUPPORTED_C else "non supportata" if category in UNSUPPORTED_C else "esclusa"


def annotation_agreement(human, key):
    """Agreement of the frozen classifier with human labels, as in the original concordance script.

    ``human``: {n: category} from a filled-in sample; ``key``: the archived
    ``campione_classificazione_chiave.json`` (list of {n, categoria, ...}).
    Rows without a human category are left out and counted.
    """
    auto = {int(x["n"]): x["categoria"] for x in key}
    labelled = [k for k in auto if human.get(k)]
    if not labelled:
        return {"n": 0, "missing": len(auto)}
    n = len(labelled)
    acc = sum(human[k] == auto[k] for k in labelled) / n
    cats = sorted(set(auto.values()) | {human[k] for k in labelled})
    pa, ph = Counter(auto[k] for k in labelled), Counter(human[k] for k in labelled)
    pe = sum(pa[c] * ph[c] for c in cats) / n ** 2
    kappa = (acc - pe) / (1 - pe) if pe < 1 else None
    by_class = sum(hc4_class(human[k]) == hc4_class(auto[k]) for k in labelled) / n
    per = defaultdict(lambda: [0, 0])
    for k in labelled:
        per[auto[k]][0] += human[k] == auto[k]
        per[auto[k]][1] += 1
    return {"n": n, "missing": len(auto) - n, "agreement": acc, "kappa": kappa, "agreement_hc4_class": by_class,
            "threshold": 0.90, "meets_threshold": acc >= 0.90,
            "per_category": {c: {"same": a, "total": t} for c, (a, t) in sorted(per.items())},
            "disagreements": [{"n": k, "automatic": auto[k], "human": human[k]}
                              for k in sorted(labelled) if human[k] != auto[k]]}


def read_human_labels(path):
    """CSV with columns n and categoria_Simona (or categoria_umana)."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    column = "categoria_Simona" if rows and "categoria_Simona" in rows[0] else "categoria_umana"
    return {int(r["n"]): (r.get(column) or "").strip() for r in rows if r.get("n")}


def key_from_archive(path):
    with c_archive(path) as z:
        return read_json(z, "campione_classificazione_chiave.json")
