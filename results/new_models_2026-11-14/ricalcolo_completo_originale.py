# Ricalcolo indipendente (pandas/numpy, senza il codice di indetbench) dai punteggi.csv del completo.
import glob, gzip, json, sys
import numpy as np, pandas as pd
base = "full/indetbench_modelli_nuovi/completo"
frozen = json.loads(gzip.decompress(open("/home/user/indet-bench/research_originals/step2/frozen/M_Original_4800_righe.json.gz", "rb").read()))
G = pd.DataFrame([r for r in frozen if r["set"] == "PN" and r["kind"] in "BC"]).set_index("row_id")
u2 = pd.read_csv("u2/punteggi.csv", keep_default_na=False)
u2q = u2[(u2.modello == "qwen") & (u2.set == "PN")].set_index("row_id")
rng_seed = 20261108
def W_story(t, col):
    w = t.pivot(index=["block_id", "pair_id"], columns="side", values=col)
    win = (w.C > w.B) + 0.5 * (w.C == w.B)
    s = win.groupby(level=0).mean()
    return s
def boot(s, n=2000):
    x = s.to_numpy(); r = np.random.default_rng(rng_seed)
    b = x[r.integers(0, len(x), (n, len(x)))].mean(1); return np.quantile(b, [.025, .975])
out = {}
for d in sorted(glob.glob(base + "/*-*/")):
    nome = d.rstrip("/").split("/")[-1].rsplit("-", 1)[0]
    t = pd.read_csv(d + "punteggi.csv", keep_default_na=False)
    e = json.load(open(d + "esito.json"))
    assert len(t) == 1600 and t.row_id.is_unique and set(t.row_id) == set(G.index), nome
    assert (t.coppia_esclusa_lunghezza.astype(str) == "False").all()
    t["gold"] = t.row_id.map(G.condition); t["family"] = t.row_id.map(G.family)
    assert (t.prompt_tokens.groupby(t.pair_id).nunique() == 1).all()
    p = t[["p_yes", "p_no", "p_unknown"]].to_numpy(float); n = p / p.sum(1, keepdims=True)
    t["mpmax"] = -n.max(1); t["ent"] = -(n * np.log(np.clip(n, 1e-300, None))).sum(1); t["unk01"] = (t.parsed == "UNKNOWN").astype(float)
    s = W_story(t, "score"); lo, hi = boot(s)
    B = t[t.side == "B"]; acc = (B.parsed == B.gold)
    r = dict(W=s.mean(), IC=(lo, hi), accB=acc.mean(), accNO=acc[B.gold == "NO"].mean(), accYES=acc[B.gold == "YES"].mean(),
             W_ent=W_story(t, "ent").mean(), W_mpmax=W_story(t, "mpmax").mean(), W_unk=W_story(t, "unk01").mean(),
             fam={f: W_story(t[t.family == f], "score").mean() for f in ("AND", "OR", "IMPLIES")},
             massa=(t.mass_total.median(), t.mass_total.min()), altro=(t.parsed == "ALTRO").sum())
    # ΔW appaiato descrittivo p(UNKNOWN) − migliore baseline indipendente (stesso ricampionamento delle storie)
    best = max(("ent", "mpmax", "unk01"), key=lambda c: W_story(t, c).mean())
    dlt = s - W_story(t, best); dlo, dhi = boot(dlt)
    r["dW_vs"] = (best, dlt.mean(), dlo, dhi)
    rep = e["report_indetbench"]; g = rep["competence_gate"]
    r["coincide_report"] = (abs(rep["W_p_unknown"]["value"] - r["W"]) < 1e-12 and abs(g["accuracy_B"] - r["accB"]) < 1e-12)
    if nome == "qwen_controllo":
        q = t.set_index("row_id")
        r["qwen_vs_U2"] = dict(max_delta=float((q.score - u2q.p_UNKNOWN.loc[q.index]).abs().max()),
                               risposte_uguali=int((q.parsed == u2q.parsed.loc[q.index]).sum()))
    out[nome] = r
    print(nome, {k: (np.round(v, 4).tolist() if isinstance(v, (tuple, np.ndarray)) else v) for k, v in r.items() if k not in ("fam", "dW_vs")},
          {k: round(v, 3) for k, v in r["fam"].items()}, "dW vs", r["dW_vs"][0], np.round(r["dW_vs"][1:], 4))
