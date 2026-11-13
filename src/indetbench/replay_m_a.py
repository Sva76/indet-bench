"""Reproduce frozen Test M notebook A statistics from the original ZIP (CPU).

Recomputes W(C>B), paired delta-W, p(UNKNOWN) reference W and
bootstrap intervals for M1, M3 and M4. No model weights or source
dataset are redistributed. This is an archival parity check,
not a repeat of the model experiments.
"""
from __future__ import annotations

from zipfile import ZipFile

from .archive_safety import check_zip_archive
from .replay import BOOT, SEED, W, delta_W, make_pairs, read_json, scores, verify


def _member(z, prefix, suffix):
    """Find an exactly matching recorded output; refuse ambiguous alternatives."""
    matches = [
        name for name in z.namelist()
        if name.startswith("uscite/" + prefix) and name.endswith("/" + suffix)
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {prefix} {suffix}; found {len(matches)}")
    return read_json(z, matches[0])


def _reference(z, environment, model):
    if environment == "env_m1":
        output = _member(z, "M1_" + model + "-", "M1_" + model + ".json")
    elif environment == "env_sirin":
        output = _member(z, "REF_env_sirin_" + model + "-", "REF_env_sirin_" + model + ".json")
    elif environment == "env_obeso" and model == "llama":
        output = _member(z, "M4_llama-", "M4.json")
        return scores(output["generazione"], "p_UNKNOWN")
    else:
        raise ValueError(f"Unknown reference environment: {environment} / {model}")
    return scores(output["riferimento"], "p_UNKNOWN")


def _method_scores(z, method, model):
    if method.startswith("M1-") and model in {"qwen", "mistral", "olmo", "llama"}:
        estimator = method.removeprefix("M1-")
        if estimator not in {"MSP", "Perplexity", "MeanTokenEntropy", "SemanticEntropy", "PTrue"}:
            raise ValueError(f"Unexpected M1 estimator {estimator}")
        source = _member(z, "M1_" + model + "-", "M1_" + model + ".json")
        return scores(source["polygraph"], "u_" + estimator), ("env_m1", model)
    if method == "M3" and model == "giudice Qwen3-4B":
        source = _member(z, "M3_giudice-", "M3.json")
        return scores(source["coppie"], "p_non_risp"), None
    if method in {"M4-lin", "M4-LoRA"} and model == "llama":
        source = _member(z, "M4_llama-", "M4.json")
        identifier = ("llama3_1_8b_linear" if method == "M4-lin"
                      else "llama3_1_8b_lora_lambda_kl_0_05")
        return scores(source["sonde"][identifier], "sonda_max"), ("env_obeso", "llama")
    raise ValueError(f"Unrecognized archived method/model combination: {method} / {model}")


def _check(label, expected, computed, errors):
    """Count point estimate and individual CI bounds, not just metric groups."""
    verify(label, expected, computed, errors)
    checked = 1
    if expected.get("ci95") is not None:
        checked += len(expected["ci95"])
    if "copertura" in expected and "valide" in computed:
        checked += 1
    if "coppie" in expected and "coppie" in computed:
        checked += 1
    return checked


def replay_m_a(path, seed=SEED, n_boot=BOOT):
    """Compare every frozen M-A W/delta-W (two formats) with raw-row replay."""
    errors, checked, groups = [], 0, 0
    with ZipFile(path) as z:
        check_zip_archive(z)
        if not {"esiti_A.json", "dati/righe.json"} <= set(z.namelist()):
            raise ValueError("Not a Test M notebook A complete-results ZIP")
        original = read_json(z, "esiti_A.json")
        if (original.get("versione") != "M-A-notebook-8"
                or original.get("modalita") != "completo"):
            raise ValueError("Only frozen Test M notebook A v8 full archive supported")
        rows = read_json(z, "dati/righe.json")
        pairs = make_pairs(rows, m=True)
        if len(pairs) != 1600 or len(rows) != 4800:
            raise ValueError("Unexpected frozen M-A dataset size")
        if len(original["risultati"]) != 23 or len(original["riferimenti"]) != 9:
            raise ValueError("Unexpected frozen M-A method/reference count")
        if len({p["block"] for p in pairs.values()}) != 200:
            raise ValueError("Unexpected frozen M-A number of stories")

        formatted = {
            label: {k: v for k, v in pairs.items() if v["format"] == code}
            for label, code in (("P−S", "PN"), ("S−S", "SN"))
        }
        ref_cache = {}
        for key, rec in original["riferimenti"].items():
            environment, model = key.split("|")
            ref = ref_cache.setdefault(key, _reference(z, environment, model))
            for label, suffix in (("P−S", "PN"), ("S−S", "SN")):
                result = W(ref, formatted[label], ("AND", "OR", "IMPLIES"), seed, n_boot)
                expected = rec["W_" + suffix]
                name = f"reference/{key}/{label}/W"
                checked += _check(name, expected, result, errors)
                groups += 1
                if expected.get("storie") != len({p["block"] for p in formatted[label].values()}):
                    errors.append({"field": name + ".storie", "error": "unexpected story count"})

        for row in original["risultati"]:
            method, model = row["metodo"], row["modello"]
            sc, ref_key = _method_scores(z, method, model)
            ref = None if ref_key is None else ref_cache[ref_key[0] + "|" + ref_key[1]]
            for label in ("P−S", "S−S"):
                fmt_pairs = formatted[label]
                entry = row["formati"][label]
                base = method + "/" + model + "/" + label
                computed = W(sc, fmt_pairs, ("AND", "OR", "IMPLIES"), seed, n_boot)
                checked += _check(base + "/W", entry["W"], computed, errors)
                groups += 1
                if computed["valide"] != entry["copertura"]["valide"]:
                    errors.append({"field": base + ".coverage", "error": "valid-pair mismatch"})
                checked += 1
                if method == "M3":
                    for gen_model, expected in entry["delta_W_descrittivi"].items():
                        reference = ref_cache["env_sirin|" + gen_model]
                        actual = delta_W(sc, reference, fmt_pairs,
                                         ("AND", "OR", "IMPLIES"), seed, n_boot)
                        name = base + "/delta_W_descrittivi/" + gen_model
                        checked += _check(name, expected, actual, errors)
                        groups += 1
                        checked += 1
                        if (expected["W_riferimento_stesse_coppie"] is None
                                or abs(expected["W_riferimento_stesse_coppie"]
                                       - actual["W_riferimento_stesse_coppie"]) > 1e-10):
                            errors.append({"field": name + ".reference_W", "error": "baseline mismatch"})
                else:
                    actual = delta_W(sc, ref, fmt_pairs,
                                     ("AND", "OR", "IMPLIES"), seed, n_boot)
                    expected = entry["delta_W"]
                    name = base + "/delta_W"
                    checked += _check(name, expected, actual, errors)
                    groups += 1
                    checked += 1
                    if (expected["W_riferimento_stesse_coppie"] is None
                            or abs(expected["W_riferimento_stesse_coppie"]
                                   - actual["W_riferimento_stesse_coppie"]) > 1e-10):
                        errors.append({"field": name + ".reference_W", "error": "baseline mismatch"})

    return {
        "experiment": "M-A",
        "version": "M-A-notebook-8",
        "method_model_combinations": len(original["risultati"]),
        "reference_environments": len(original["riferimenti"]),
        "stories": 200,
        "pairs_two_formats": len(pairs),
        "metric_groups_checked": groups,
        "numeric_values_checked": checked,
        "differences": errors,
        "passed": not errors,
        "scope": "Archived W, paired delta-W, bootstrap and coverage only; no new GPU inference",
    }
