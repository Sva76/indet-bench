"""CPU replay of frozen Test C and Test M notebook B, from per-row scores.

This module recalculates W, paired ΔW, confidence intervals, domain controls,
and family breakdowns. It deliberately does NOT validate HC4 class labels.
Requires optional extra: pip install 'indetbench[replay]'.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import contextmanager
import hashlib
from io import BytesIO
import json
from math import isfinite
from pathlib import Path
import sys
from zipfile import ZipFile

import numpy as np

SEED = 20261108
BOOT = 2000
FAMILIES_C = ("DUE", "CONF", "LOG")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(z, name):
    return json.loads(z.read(name))


@contextmanager
def c_archive(path):
    """Accept outer complete ZIP and compact nested result ZIP."""
    with ZipFile(path) as outer:
        names = set(outer.namelist())
        if {"esiti_C.json", "dati/righe_C_selezionate.json"} <= names:
            yield outer
        elif "completo/testC_completo_risultati.zip" in names:
            with ZipFile(BytesIO(outer.read("completo/testC_completo_risultati.zip"))) as inner:
                yield inner
        else:
            raise ValueError("Not the original Test C complete-results archive")


def scores(rows, value):
    result = {}
    for row in rows:
        k = row["row_id"]
        if k in result:
            raise ValueError("Duplicate score row " + k)
        x = row.get(value)
        result[k] = None if x is None else float(x)
    return result


def make_pairs(rows, *, m=False):
    """Keep the original dataset order: it affects bootstrap resampling."""
    pairs = {}
    for row in rows:
        kind = row["kind"]
        if kind not in ("B", "C"):
            continue
        key = (row["set"] + "|" if m else "") + row["pair_key"]
        block = row["story_id"] if m else row["passaggio_id"]
        family = row["family"] if m else row["famiglia"]
        old = pairs.setdefault(key, {"block": block, "family": family})
        if old["block"] != block or old["family"] != family or kind in old:
            raise ValueError("Inconsistent or duplicate pair " + key)
        if m:
            old["format"] = row["set"]
        old[kind] = row["row_id"]
    if not pairs or any(not {"B", "C"} <= set(row) for row in pairs.values()):
        raise ValueError("Incomplete B/C pairs")
    return pairs


def wins(sc, pairs, families):
    for key, pair in pairs.items():
        if pair["family"] not in families:
            continue
        b, c = sc.get(pair["B"]), sc.get(pair["C"])
        if not all(isinstance(v, (float, int)) and isfinite(v) for v in (b, c)):
            continue
        yield key, pair["block"], 1.0 if c > b else 0.5 if c == b else 0.0


def boot_stat(values, seed, n_boot):
    values = np.asarray(list(values), float)
    if not len(values):
        return {"stima": None, "ci95": None}
    ci = None
    if n_boot and len(values) > 1:
        rng = np.random.default_rng(seed)
        b = values[rng.integers(0, len(values), (n_boot, len(values)))].mean(axis=1)
        ci = [float(x) for x in np.quantile(b, [0.025, 0.975])]
    return {"stima": float(values.mean()), "ci95": ci}


def W(sc, pairs, families, seed, n_boot):
    grouped = defaultdict(list)
    n_valid = 0
    for _, block, win in wins(sc, pairs, families):
        grouped[block].append(win)
        n_valid += 1
    stat = boot_stat((np.mean(v) for v in grouped.values()), seed, n_boot)
    stat["valide"] = n_valid
    return stat


def delta_W(sc, ref, pairs, families, seed, n_boot):
    a = {k: (block, win) for k, block, win in wins(sc, pairs, families)}
    b = {k: (block, win) for k, block, win in wins(ref, pairs, families)}
    differences, ref_values = defaultdict(list), defaultdict(list)
    common = 0
    for k, pair in pairs.items():
        if pair["family"] not in families or k not in a or k not in b:
            continue
        block1, win1 = a[k]
        block2, win2 = b[k]
        if block1 != block2:
            raise ValueError("Unmatched passage for " + k)
        differences[block1].append(win1 - win2)
        ref_values[block1].append(win2)
        common += 1
    stat = boot_stat((np.mean(v) for v in differences.values()), seed, n_boot)
    stat["coppie"] = common
    stat["W_riferimento_stesse_coppie"] = (
        float(np.mean([np.mean(v) for v in ref_values.values()])) if ref_values else None
    )
    return stat


def D_rim(sc, pairs, seed, n_boot):
    rim, main = {}, defaultdict(list)
    for pair in pairs.values():
        b, c = sc.get(pair["B"]), sc.get(pair["C"])
        if not all(isinstance(v, (float, int)) and isfinite(v) for v in (b, c)):
            continue
        win = 1.0 if c > b else 0.5 if c == b else 0.0
        if pair["family"] == "RIM":
            rim[pair["block"]] = win
        elif pair["family"] in FAMILIES_C:
            main[pair["block"]].append(win)
    blocks = sorted(set(rim) & set(main))
    return boot_stat((rim[k] - np.mean(main[k]) for k in blocks), seed, n_boot)


def verify(label, original, computed, errors, tolerance=1e-10):
    """Compare archived statistics with independent replay, including bootstrap."""
    for key in ("stima",):
        expected, actual = original.get(key), computed.get(key)
        if (expected is None) != (actual is None) or (
            expected is not None and abs(expected - actual) > tolerance
        ):
            errors.append({"field": label + "." + key, "expected": expected, "actual": actual})
    ec, ac = original.get("ci95"), computed.get("ci95")
    if ec is not None and (ac is None or len(ac) != len(ec) or
                           any(abs(x - y) > tolerance for x, y in zip(ec, ac))):
        errors.append({"field": label + ".ci95", "expected": ec, "actual": ac})
    if "copertura" in original and "valide" in computed:
        if original["copertura"]["valide"] != computed["valide"]:
            errors.append({"field": label + ".valide"})
    if "coppie" in original and "coppie" in computed:
        if original["coppie"] != computed["coppie"]:
            errors.append({"field": label + ".coppie"})


def c_sources(z):
    result, references = {}, {}
    models = ("qwen", "mistral", "olmo", "llama")
    for model in models:
        m1 = read_json(z, f"uscite/M1_{model}.json")
        key = ("riferimento p(UNKNOWN)", model)
        result[key] = scores(m1["riferimento"], "p_UNKNOWN")
        for estimator in ("MSP", "Perplexity", "MeanTokenEntropy", "SemanticEntropy", "PTrue"):
            name = "M1-" + estimator
            result[(name, model)] = scores(m1["polygraph"], "u_" + estimator)
            references[(name, model)] = result[key]
        rs = read_json(z, f"uscite/REF_env_sirin_{model}.json")
        sirin_ref = scores(rs["riferimento"], "p_UNKNOWN")
        m2 = read_json(z, f"uscite/M2_{model}.json")
        for variant, name in (("originale", "M2"), ("senza_l2", "M2-senzaℓ2")):
            result[(name, model)] = scores(m2["righe"][variant], "p_non_risp")
            references[(name, model)] = sirin_ref
        references[("M3", model)] = sirin_ref
    judge = scores(read_json(z, "uscite/M3.json")["righe"], "p_non_risp")
    for model in models:
        result[("M3", model)] = judge
    obeso = read_json(z, "uscite/M4.json")
    obeso_ref = scores(obeso["generazione"], "p_UNKNOWN")
    names = {"llama3_1_8b_linear": "M4-lin",
             "llama3_1_8b_lora_lambda_kl_0_05": "M4-LoRA"}
    for key, rows in obeso["sonde"].items():
        name = names[key]
        result[(name, "llama")] = scores(rows, "sonda_max")
        references[(name, "llama")] = obeso_ref
    return result, references


def replay_c(path, seed=SEED, n_boot=BOOT):
    errors, checked = [], 0
    with c_archive(path) as z:
        original = read_json(z, "esiti_C.json")
        if original.get("versione") != "C-notebook-3-Csel8" or original.get("modalita") != "completo":
            raise ValueError("Only frozen Test C v3 full archive supported")
        allrows = read_json(z, "dati/righe_C_selezionate.json")
        synthetic = make_pairs([r for r in allrows if r["insieme"].startswith("sintetico")])
        natural = make_pairs([r for r in allrows if r["insieme"] == "naturale"])
        sources, references = c_sources(z)
        for row in original["risultati"]:
            method, model = row["metodo"], row["modello"]
            key = (method, model)
            sc, ref = sources[key], references.get(key)
            tag = method + "/" + model
            checks = [("W", row["W"], W(sc, synthetic, FAMILIES_C, seed, n_boot)),
                      ("W_RIM", row["W_RIM"], W(sc, synthetic, ("RIM",), seed, n_boot)),
                      ("D_RIM", row["D_RIM"], D_rim(sc, synthetic, seed, n_boot))]
            if ref is not None:
                checks.append(("delta_W", row["delta_W"], delta_W(sc, ref, synthetic, FAMILIES_C, seed, n_boot)))
            for family in FAMILIES_C:
                fam = row["famiglie"][family]
                checks.append((family + ".W", fam["W"], W(sc, synthetic, (family,), seed, n_boot)))
                if ref is not None:
                    checks.append((family + ".delta_W", fam["delta_W"],
                                   delta_W(sc, ref, synthetic, (family,), seed, n_boot)))
            if "naturale" in row:
                for family in ("RIM-nat", "DUE-nat"):
                    checks.append((family + ".W", row["naturale"][family],
                                   W(sc, natural, (family,), seed, 0)))
                    if ref is not None:
                        checks.append((family + ".delta_W", row["naturale_delta_W"][family],
                                       delta_W(sc, ref, natural, (family,), seed, 0)))
            for metric, expected, computed in checks:
                verify(tag + "." + metric, expected, computed, errors)
                checked += 1
    return {"experiment": "C", "version": "C-notebook-3-Csel8",
            "method_model_combinations": len(original["risultati"]),
            "synthetic_pairs": len(synthetic), "natural_pairs": len(natural),
            "statistics_checked": checked, "differences": errors, "passed": not errors,
            "scope": "W, paired delta-W and controls only; HC4 classification NOT revalidated"}


def replay_m_b(path, seed=SEED, n_boot=BOOT):
    errors, checked = [], 0
    with ZipFile(path) as z:
        if not {"esiti_B.json", "dati/righe.json"} <= set(z.namelist()):
            raise ValueError("Not the original Test M notebook B results ZIP")
        original = read_json(z, "esiti_B.json")
        if original.get("versione") != "M-B-notebook-4" or original.get("modalita") != "completo":
            raise ValueError("Only frozen Test M notebook B full archive supported")
        pairs = make_pairs(read_json(z, "dati/righe.json"), m=True)
        names = z.namelist()
        for row in original["risultati"]:
            method, model = row["metodo"], row["modello"]
            source = next((n for n in names if n.startswith("uscite/M2_") and
                           n.endswith(f"/M2_{model}.json")), None)
            refpath = next((n for n in names if n.startswith("riferimenti_A/REF_env_sirin_") and
                            n.endswith(f"/REF_env_sirin_{model}.json")), None)
            if not source or not refpath:
                raise ValueError("Missing original scores for " + model)
            data = read_json(z, source)
            if method not in ("M2", "M2-senzaℓ2"):
                raise ValueError("Unexpected method " + method)
            sc = scores(data["coppie"] if method == "M2" else data["senza_l2"]["coppie"], "p_non_risp")
            ref = scores(read_json(z, refpath)["riferimento"], "p_UNKNOWN")
            for fmt, code in (("P−S", "PN"), ("S−S", "SN")):
                fmtpairs = {k: v for k, v in pairs.items() if v["format"] == code}
                entry = row["formati"][fmt]
                tag = method + "/" + model + "/" + fmt
                checks = [("W", entry["W"], W(sc, fmtpairs, ("AND", "OR", "IMPLIES"), seed, n_boot)),
                          ("delta_W", entry["delta_W"], delta_W(sc, ref, fmtpairs,
                                                                ("AND", "OR", "IMPLIES"), seed, n_boot))]
                for family in ("AND", "OR", "IMPLIES"):
                    fam = row["famiglie"][fmt][family]
                    checks += [(family + ".W", fam["W_f"], W(sc, fmtpairs, (family,), seed, n_boot)),
                               (family + ".reference_W", fam["W_f_riferimento"],
                                W(ref, fmtpairs, (family,), seed, n_boot)),
                               (family + ".delta_W", fam["delta_W_f"],
                                delta_W(sc, ref, fmtpairs, (family,), seed, n_boot))]
                for metric, expected, computed in checks:
                    verify(tag + "." + metric, expected, computed, errors)
                    checked += 1
    return {"experiment": "M-B", "version": "M-B-notebook-4",
            "method_model_combinations": len(original["risultati"]),
            "pairs_two_formats": len(pairs), "statistics_checked": checked,
            "differences": errors, "passed": not errors,
            "scope": "Test M notebook B only. Notebook A NOT reproduced"}


def main(argv=None):
    p = argparse.ArgumentParser(description="CPU replay of Test C or Test M B archived statistics")
    p.add_argument("archive")
    p.add_argument("--kind", choices=("C", "M-B"), default="C")
    p.add_argument("--expected-sha256")
    p.add_argument("--json-out")
    args = p.parse_args(argv)
    actual = sha256(args.archive)
    if args.expected_sha256 and actual != args.expected_sha256.lower():
        p.error(f"Archive SHA-256 mismatch: {actual} vs {args.expected_sha256}")
    report = (replay_c if args.kind == "C" else replay_m_b)(args.archive)
    report["sha256"] = actual
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.json_out:
        Path(args.json_out).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
