"""Ricalcolo indipendente del W della parte B da punteggi.csv (uso: python -I ricalcolo_parteB.py <cartella_modello>...).
W = media sulle storie della quota di coppie con punteggio C > B (pareggio = 0.5); IC95 bootstrap sulle storie (2000)."""
import collections, csv, random, sys

def w(rows):
    d = collections.defaultdict(dict)
    for x in rows:
        d[x["pair_id"]][x["side"]] = x
    per = collections.defaultdict(list)
    for v in d.values():
        c, b = float(v["C"]["score"]), float(v["B"]["score"])
        per[v["C"]["block_id"]].append(1 if c > b else 0.5 if c == b else 0)
    s = {k: sum(v) / len(v) for k, v in per.items()}
    random.seed(0)
    ks = list(s)
    bs = sorted(sum(s[random.choice(ks)] for _ in ks) / len(ks) for _ in range(2000))
    return sum(s.values()) / len(s), bs[50], bs[1949], len(d), len(s)

for cartella in sys.argv[1:]:
    rows = list(csv.DictReader(open(f"{cartella}/punteggi.csv")))
    for cond in sorted({x["condizione"] for x in rows}):
        print(cartella, cond, "W %.4f IC95 [%.4f, %.4f] coppie %d storie %d" % w([x for x in rows if x["condizione"] == cond]))
