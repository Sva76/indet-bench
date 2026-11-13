# Test C: verifica indipendente della selezione (C-sel-7; divisore in frasi del naturale corretto l'11 novembre). Non importa né il generatore né lo script di selezione:
# rilegge il testo con regole proprie, scritte qui, e ricalcola la regola di selezione dai registri. Ogni controllo non
# superato è un errore: alla fine lo script esce con codice 1 se c'è almeno un errore.
#
# Uso: python -I verifica_selezione_v4.py <cartella selezione> [--squad dev-v2.0.json]
#   <cartella selezione> contiene dati/ (righe_C.json, testC_sintetico_*.json, registro_candidati_*.json,
#   rapporto_selezione.json) e le due riserve testC_sintetico_*_riserva.json.
#   --squad (facoltativo): il file ufficiale di SQuAD 2.0 dev; se c'è, contesti, domande e risposte del naturale si
#   confrontano con la fonte.
#
# Cosa non verifica: i conteggi dei token (servono i tokenizer; qui si controlla solo che i valori salvati rispettino
# i limiti) e l'esclusione delle 400 domande di HM0 (serve il train di SQuAD per ricostruirle).
import json
import re
import string
import sys
from collections import Counter, defaultdict

ISTRUZIONE = "Answer the question using the passage. Reply with a short answer or UNKNOWN."
QUOTE = {"anno/0": 17, "anno/1": 17, "anno/2": 16, "numero/0": 17, "numero/1": 16, "numero/2": 17, "luogo/0": 16,
         "luogo/1": 17, "luogo/2": 17, "persona/0": 17, "persona/1": 17, "persona/2": 16}
N_PROVA, N_NATURALE, TOLLERANZA, MAX_SIRIN = 10, 200, 3, 512
MARCATORI = ["maybe", "probably", "possibly", "perhaps", "likely", "unlikely", "uncertain", "unknown", "unclear",
             "seems", "appears to", "may", "might", "could", "believed", "said to", "reportedly", "allegedly",
             "estimated", "about", "around", "roughly", "approximately", "not known", "no record"]
CIFRE = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12}

err = Counter()
esempi = defaultdict(list)


def errore(chiave, dettaglio):
    err[chiave] += 1
    if len(esempi[chiave]) < 5:
        esempi[chiave].append(dettaglio)


def occorrenze(testo, w):
    return len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(w) + r"(?![A-Za-z0-9])", testo))


def frasi_sintetiche(testo):
    # nei passaggi sintetici ogni frase finisce con un punto e la successiva comincia con una maiuscola
    out, cur = [], []
    for tok in testo.split(" "):
        cur.append(tok)
        if tok.endswith("."):
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def anni(testo):
    return [int(x) for x in re.findall(r"(?<![0-9])(1[0-9]{3}|20[0-9]{2})(?![0-9])", testo)]


# --------------------------------------------------------------------------- sintetico: lettura dal testo
def maschera(frase, togli):
    for w in sorted(togli, key=len, reverse=True):
        frase = re.sub(r"(?<![A-Za-z0-9])" + re.escape(w) + r"(?![A-Za-z0-9])", "§", frase)
    return frase


def cifre(p, chiave):
    # per i numeri anche la forma in cifre («seven» e «7»); per gli anni la risposta coincide con il valore
    return [x for x in p[chiave] if x.isdigit()] if p["tipo_attributo"] == "numero" else []


def valori_in(frase, p):
    forme = {p["valore_B"]: [p["valore_B"]] + cifre(p, "risposte_B"),
             p["valore_alternativo"]: [p["valore_alternativo"]] + cifre(p, "risposte_alternativo")}
    return [v for v, ff in forme.items() if any(occorrenze(frase, f) for f in ff)]


def controlla_versione_famiglia(p, fam, B, C, tag):
    """Determinabilità letta dal testo, famiglia per famiglia, con regole indipendenti dai template."""
    v1, v2 = p["valore_B"], p["valore_alternativo"]
    fb, fc = frasi_sintetiche(B), frasi_sintetiche(C)
    if len(fb) != len(fc):
        errore("B e C con un numero diverso di frasi", tag)
        return
    diverse = [i for i in range(len(fb)) if fb[i] != fc[i]]
    con_b = [i for i, f in enumerate(fb) if valori_in(f, p)]
    con_c = [i for i, f in enumerate(fc) if valori_in(f, p)]
    if fam == "RIM":
        if [valori_in(fb[i], p) for i in con_b] != [[v1]] or con_c:
            errore("RIM: B non dà il solo valore o C contiene un valore", tag)
        if diverse != con_b:
            errore("RIM: B e C differiscono fuori dalla frase con il valore", (tag, diverse, con_b))
    elif fam == "DUE":
        if [valori_in(fb[i], p) for i in con_b] != [[v1]]:
            errore("DUE: B non afferma il solo valore", tag)
        if len(con_c) != 1 or sorted(valori_in(fc[con_c[0]], p)) != sorted([v1, v2]):
            errore("DUE: C non ha i due valori nella stessa frase", tag)
        else:
            f = fc[con_c[0]]
            if not any(re.search(re.escape(a) + r" or (?:[A-Za-z]+ ){0,3}" + re.escape(b) + r"(?![A-Za-z0-9])", f)
                       for a, b in ((v1, v2), (v2, v1))):
                errore("DUE: in C i due valori non sono uniti da «or»", (tag, f))
        altre = [i for i in diverse if i not in con_b]
        if len(altre) != 1 or fb[altre[0]].replace(" or ", " and ") != fc[altre[0]] or " or " not in fb[altre[0]]:
            errore("DUE: la frase con «or» irrilevante di B non diventa «and» in C (o B e C differiscono altrove)",
                   (tag, diverse))
    elif fam in ("CONF", "LOG"):
        inizio = "According to the " if fam == "CONF" else "Every "
        nomi = p["nomi"]["fonti"] if fam == "CONF" else p["nomi"]["gruppi"]
        for lato, ff in (("B", fb), ("C", fc)):
            blocco = [f for f in ff if f.startswith(inizio) and any(occorrenze(f, n) for n in nomi)]
            if len(blocco) != 2:
                errore(f"{fam}: {lato} non ha due frasi «{inizio.strip()}»", tag)
                continue
            nominati = [[n for n in nomi if occorrenze(f, n)] for f in blocco]
            vals = [valori_in(f, p) for f in blocco]
            if sorted(sum(nominati, [])) != sorted(nomi) or any(len(x) != 1 for x in nominati):
                errore(f"{fam}: le due frasi non nominano una {'fonte' if fam == 'CONF' else 'regola di gruppo'} "
                       "diversa ciascuna", (tag, lato, nominati))
            # pari rango: tolti il nome e il valore, le due frasi sono identiche
            m = [maschera(f, nomi + [v1, v2] + cifre(p, "risposte_B") + cifre(p, "risposte_alternativo"))
                 for f in blocco]
            if m[0] != m[1]:
                errore(f"{fam}: le due frasi non sono parallele (pari rango)", (tag, lato, m))
            attesi = [[v1], [v1]] if lato == "B" else None
            if lato == "B" and vals != attesi:
                errore(f"{fam}: in B le due frasi non danno lo stesso valore", (tag, vals))
            if lato == "C" and (sorted(sum(vals, [])) != sorted([v1, v2]) or any(len(x) != 1 for x in vals)):
                errore(f"{fam}: in C le due frasi non danno i due valori, uno ciascuna", (tag, lato, vals))
            fuori = [f for f in ff if valori_in(f, p) and f not in blocco]
            if fuori:
                errore(f"{fam}: valori fuori dal blocco", (tag, lato, fuori))
        if len(diverse) != 1 or not (fb[diverse[0]].startswith(inizio) and any(occorrenze(fb[diverse[0]], n) for n in nomi)):
            errore(f"{fam}: B e C non differiscono in una sola frase del blocco", (tag, diverse))
        if fam == "LOG":
            for lato, ff in (("B", fb), ("C", fc)):
                disg = [f for f in ff if all(occorrenze(f, n) for n in nomi) and " or " in f]
                if len(disg) != 1 or not occorrenze(disg[0], p["soggetto"]):
                    errore("LOG: manca la frase «soggetto … G1 … or … G2»", (tag, lato))
            if [f for f in fb if " or " in f] != [f for f in fc if " or " in f]:
                errore("LOG: la disgiunzione cambia fra B e C", tag)


def controlla_passaggio(p, insieme):
    pid = p["passaggio_id"]
    v1, v2, tipo = p["valore_B"], p["valore_alternativo"], p["tipo_attributo"]
    if occorrenze(p["domanda"], v1) or occorrenze(p["domanda"], v2):
        errore("domanda con un valore", pid)
    if not occorrenze(p["domanda"], p["entita"]):
        errore("domanda senza l'entità", pid)
    if v1 == v2:
        errore("valori uguali", pid)
    atteso_occ = {("RIM", "B"): (1, 0), ("RIM", "C"): (0, 0), ("DUE", "B"): (1, 0), ("DUE", "C"): (1, 1),
                  ("CONF", "B"): (2, 0), ("CONF", "C"): (1, 1), ("LOG", "B"): (2, 0), ("LOG", "C"): (1, 1)}
    attesi_or = {"RIM": 0, "CONF": 0, "DUE": 1, "LOG": 1}
    for fam, F in p["famiglie"].items():
        tag = f"{insieme}/{pid}/{fam}"
        B, C = F["B"]["testo"], F["C"]["testo"]
        for lato, t in (("B", B), ("C", C)):
            o1 = occorrenze(t, v1) + sum(occorrenze(t, x) for x in cifre(p, "risposte_B"))
            o2 = occorrenze(t, v2) + sum(occorrenze(t, x) for x in cifre(p, "risposte_alternativo"))
            if (o1, o2) != atteso_occ[(fam, lato)]:
                errore("occorrenze dei valori", (tag, lato, (o1, o2)))
            if occorrenze(t, "or") != attesi_or[fam]:
                errore("numero di «or»", (tag, lato, occorrenze(t, "or")))
            for w in MARCATORI:
                if re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", t, re.I):
                    errore("marcatore di riserva nel testo", (tag, lato, w))
            if not 120 <= len(t.split()) <= 180:
                errore("parole fuori da 120–180", (tag, lato, len(t.split())))
            if " ".join(F[lato]["frasi"]) != t:
                errore("testo diverso dall'unione delle frasi salvate", (tag, lato))
            for k, n in F[lato]["lunghezze"].items():
                if k.startswith("sirin") and n > MAX_SIRIN:
                    errore("prompt SIRIN oltre 512 token", (tag, lato, k, n))
            # cronologia: nei passaggi di tipo anno ogni altro anno viene dopo entrambi i valori
            if tipo == "anno":
                prima = [y for y in anni(t) if str(y) not in (v1, v2) and y <= max(int(v1), int(v2))]
                if prima:
                    errore("cronologia: anni di contorno non successivi all'anno bersaglio", (tag, lato, prima, v1, v2))
        if sorted(y for y in anni(B) if str(y) not in (v1, v2)) != sorted(y for y in anni(C) if str(y) not in (v1, v2)):
            errore("anni di contorno diversi fra B e C", tag)
        d = F["differenza_token_C_meno_B"]
        if not d or max(abs(x) for x in d.values()) > TOLLERANZA:
            errore("differenza di token oltre la tolleranza", (tag, d))
        controlla_versione_famiglia(p, fam, B, C, tag)


# --------------------------------------------------------------------------- selezione: primi validi
def controlla_regola(riserva, scelti, registro, nome, quote=None, n=None):
    ordine_ris = [p["passaggio_id"] for p in riserva]
    if [r["passaggio_id"] for r in registro] != ordine_ris:
        errore("registro non nell'ordine della riserva", nome)
    for r in registro:
        if r["esito"] == "escluso" and not r["motivi"]:
            errore("candidato escluso senza motivo", (nome, r["passaggio_id"]))
        if r["esito"] != "escluso" and r["motivi"]:
            errore("candidato valido con motivi", (nome, r["passaggio_id"]))
    validi = [r for r in registro if r["esito"] != "escluso"]
    attesi, presi = [], Counter()
    for r in validi:
        st = f"{r['tipo']}/{r['schema_posizione']}"
        if quote is not None and presi[st] < quote[st]:
            presi[st] += 1
            attesi.append(r["passaggio_id"])
        elif quote is None and len(attesi) < n:
            attesi.append(r["passaggio_id"])
    ids = [p["passaggio_id"] for p in scelti]
    if ids != attesi:
        errore("la selezione non è «i primi validi» (ricalcolo dal registro)", (nome, len(ids), len(attesi)))
    if {r["passaggio_id"] for r in registro if r["esito"] == "scelto"} != set(ids):
        errore("esiti «scelto» del registro diversi dai passaggi scelti", nome)
    if quote is not None and dict(presi) != quote:
        errore("quote per strato non piene", (nome, dict(presi)))
    if quote is None and len(ids) != n:
        errore("numero della prova diverso da 10", (nome, len(ids)))
    # il testo scelto è quello della variante indicata nella riserva, senza modifiche
    per_id = {p["passaggio_id"]: p for p in riserva}
    for p in scelti:
        q = per_id.get(p["passaggio_id"])
        if q is None:
            errore("passaggio scelto assente dalla riserva", p["passaggio_id"])
            continue
        for fam, F in p["famiglie"].items():
            for lato in ("B", "C"):
                if q["famiglie"][fam][lato][F[lato]["variante"]]["testo"] != F[lato]["testo"]:
                    errore("testo scelto diverso dalla variante della riserva", (p["passaggio_id"], fam, lato))
        for k in ("valore_B", "valore_alternativo", "domanda", "entita", "tipo_attributo", "genere"):
            if q[k] != p[k]:
                errore("metadati diversi dalla riserva", (p["passaggio_id"], k))


def parole_nomi(ps):
    w = set()
    for p in ps:
        w |= {p["entita"].lower(), p["nomi"]["regione"].lower()} | {x.lower() for x in p["nomi"]["gruppi"] + p["nomi"]["fonti"]}
        if p["tipo_attributo"] in ("luogo", "persona"):
            w |= {x.lower() for v in (p["valore_B"], p["valore_alternativo"]) for x in v.split()}
    return w


# --------------------------------------------------------------------------- naturale
def norm(s):
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


ABBR = {"mr", "mrs", "ms", "dr", "st", "jr", "sr", "prof", "gen", "col", "lt", "gov", "sen", "rep", "rev", "capt",
        "sgt", "mt", "ft", "no", "vs", "etc", "inc", "ltd", "co", "corp", "jan", "feb", "mar", "apr", "jun", "jul",
        "aug", "sep", "sept", "oct", "nov", "dec", "e.g", "i.e", "u.s", "u.k", "a.d", "b.c", "c", "ca", "approx", "fig",
        "vol", "op", "pp", "ed", "eds", "est", "dept", "univ", "assn", "bros", "cf", "al"}


def frasi_naturali(testo):
    """Frasi di un paragrafo naturale, scritte qui da capo: una frase si chiude su . ! ? seguito da eventuali virgolette
    o parentesi di chiusura, poi da uno o più spazi e da maiuscola, cifra, virgolette o parentesi; il confine vale solo
    se, dopo le chiusure, non resta aperta nessuna parentesi o virgoletta, e mai dopo un'iniziale (una lettera sola) o
    un'abbreviazione. La parola prima del punto è l'intera sequenza senza spazi («1950s» non è un'iniziale).
    Versione corretta l'11 novembre (C-sel-5): la versione per C-sel-4 non chiudeva le frasi che finiscono con «."» o
    «.)», leggeva «1950s.» come iniziale e non accettava due spazi dopo il punto."""
    out, inizio, prof, virg, curve = [], 0, 0, False, 0
    i, n = 0, len(testo)
    while i < n:
        ch = testo[i]
        if ch in "([":
            prof += 1
        elif ch in ")]":
            prof = max(0, prof - 1)
        elif ch == '"':
            virg = not virg
        elif ch == "\u201c":
            curve += 1
        elif ch == "\u201d":
            curve = max(0, curve - 1)
        if ch in ".!?":
            j, p2, v2, c2 = i + 1, prof, virg, curve
            while j < n and testo[j] in "\"')]\u201d\u2019":     # chiusure subito dopo il segno
                if testo[j] in ")]":
                    p2 = max(0, p2 - 1)
                elif testo[j] == '"':
                    v2 = not v2
                elif testo[j] == "\u201d":
                    c2 = max(0, c2 - 1)
                j += 1
            k = j
            while k < n and testo[k] in " \t\n":
                k += 1
            if (k > j and k < n and p2 == 0 and not v2 and c2 == 0
                    and (testo[k].isupper() or testo[k].isdigit() or testo[k] in "\"'(\u201c")):
                parola = re.findall(r"(\S+)$", testo[inizio:i])
                parola = parola[0].lstrip("\"'([\u201c").lower() if parola else ""
                if ch == "." and (re.fullmatch(r"[a-z]", parola) or parola in ABBR
                                  or re.fullmatch(r"(?:[a-z]\.)+[a-z]", parola)):
                    i += 1
                    continue
                out.append(testo[inizio:j].strip())
                inizio = k
                prof, virg, curve = p2, v2, c2
                i = k
                continue
        i += 1
    if testo[inizio:].strip():
        out.append(testo[inizio:].strip())
    return out


def numeri(testo):
    t = testo.lower().replace(",", "")
    out = {float(x) for x in re.findall(r"(?<![0-9.])[0-9]+(?:\.[0-9]+)?(?![0-9])", t)}
    parole = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
              "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
              "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
              "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100}
    out |= {float(parole[w]) for w in re.findall(r"[a-z]+", t) if w in parole}
    return out


def risposte_coerenti(risposte, tipo):
    """Regola di validazione dei riferimenti (C-sel-4), riscritta qui: per anni e numeri tutte le risposte portano lo
    stesso unico valore; per i nomi la più corta è contenuta in tutte le altre (o le contiene)."""
    rr = [r for r in risposte if norm(r)]
    if not rr:
        return "nessuna risposta"
    if tipo == "anno":
        vv = [set(anni(r)) for r in rr]
        if any(len(v) != 1 for v in vv) or len(set.union(*vv)) != 1:
            return f"anni diversi o multipli nelle risposte: {rr}"
        return None
    if tipo == "numero":
        vv = [numeri(r) for r in rr]
        if any(len(v) != 1 for v in vv) or len(set.union(*vv)) != 1:
            return f"numeri diversi o multipli nelle risposte: {rr}"
        return None
    base = norm(min(rr, key=len))
    for r in rr:
        n = norm(r)
        if not (re.search(r"(?<!\w)" + re.escape(base) + r"(?!\w)", n) or re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", base)):
            return f"risposte che non si contengono: {rr}"
    return None


def testo_integro(testo):
    if testo.count("(") != testo.count(")") or testo.count("[") != testo.count("]") or testo.count('"') % 2:
        return "parentesi o virgolette non bilanciate"
    for f in frasi_naturali(testo):
        if not (f[0].isupper() or f[0].isdigit() or f[0] in "\"'("):
            return f"frase che non comincia con la maiuscola: {f[:40]}"
        if not re.search(r"[.!?][\"')\]]*$", f):
            return f"frase senza punto finale: {f[-40:]}"
    return None


# Controlli semantici C-verifica-4, riscritti qui: non importano i filtri della selezione.
def parole_semantiche_v(testo):
    s = re.sub(r"['’]s\b", "", testo.casefold())
    return re.findall(r"[a-z0-9]+", s)


def rim_nome_residuo(B, C, risposte):
    parole_c = parole_semantiche_v(C)
    alias = {"china": ["chinese"], "france": ["french"], "germany": ["german", "germans"],
             "scotland": ["scottish", "scots"], "poland": ["polish"], "england": ["english"],
             "netherlands": ["dutch"], "japan": ["japanese"], "india": ["indian", "indians"],
             "norman": ["normans"]}
    sequenze = []
    for risposta in risposte:
        pp = parole_semantiche_v(risposta)
        if not pp:
            continue
        sequenze.append(pp)
        if len(pp) == 1:
            sequenze += [[w] for w in alias.get(pp[0], [])]
            if len(pp[0]) >= 4 and not pp[0].endswith("s"):
                sequenze.append([pp[0] + "s"])
                if pp[0].endswith("a"):
                    sequenze.append([pp[0] + "n"])
        else:
            generici = {"the", "school", "university", "college", "river", "city", "town", "court", "justice", "king", "queen",
                        "prince", "princess", "saint", "doctor", "sir", "lady", "lord", "admiral", "general", "captain",
                        "hurricane", "storm", "war", "battle", "north", "south", "east", "west", "new", "old", "great",
                        "grand", "royal", "national", "united", "company", "corporation"}
            sequenze.extend([w] for w in pp if len(w) >= 4 and w not in generici)
        for app in re.finditer(re.escape(risposta) + r"\s*\(([^)]*)\)", B, flags=re.I):
            a = app.group(1).strip().strip('"\u201c\u201d')
            if re.fullmatch(r"[A-Za-z -]{1,45}", a) and len(a.split()) <= 3:
                sequenze.append(parole_semantiche_v(a))
    for pp in sequenze:
        if pp and any(parole_c[i:i + len(pp)] == pp for i in range(len(parole_c) - len(pp) + 1)):
            return " ".join(pp)
    return None


def valore_base_v(testo):
    vals = numeri(testo)
    return next(iter(vals)) if len(vals) == 1 else None


def via_calcolo_v(domanda, residuo, target):
    if target is None or not re.search(r"\b(?:how many|how much|population|total|overall|number)\b", domanda, re.I):
        return False
    import itertools
    import math
    tokens = list(re.finditer(r"\d[\d,]*(?:\.\d+)?|\b[A-Za-z]+\b", residuo))
    vv = []
    lettere = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve "
                                         "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
    lettere.update(dict(thirty=30, forty=40, fifty=50, sixty=60, seventy=70, eighty=80, ninety=90))
    for match in tokens:
        tok = match.group()
        if tok[0].isdigit():
            before = residuo[match.start() - 1] if match.start() else ""
            after = residuo[match.end()] if match.end() < len(residuo) else ""
            if (before and (before.isalnum() or before in "_.")) or (after and (after.isalnum() or after == "_")):
                continue
            vv.append(float(tok.replace(",", "")))
        elif tok.lower() in lettere:
            vv.append(float(lettere[tok.lower()]))
    if len(vv) > 18:
        return True
    uguale = lambda x: math.isclose(x, target, rel_tol=1e-9, abs_tol=1e-9)
    for k in range(2, min(len(vv), 6) + 1):
        if any(uguale(sum(v)) for v in itertools.combinations(vv, k)):
            return True
    return any(uguale(abs(a - b)) or (min(a, b) > 1 and uguale(a * b))
               for a, b in itertools.combinations(vv, 2))


def controlli_nuovi_naturale(B, C, sq, fam, squad):
    q, b, c = B["domanda"], B["contesto"], C["contesto"]
    qn = q.lower()
    if re.search(r"\bborn\b|\bbirth\b", q, re.I):
        frasi_riferimento = [f for f in frasi_naturali(b) if any(a in f for a in B["risposte_B"])]
        if not any(re.search(r"\bborn\b|\bbirth\b", f, re.I) for f in frasi_riferimento):
            errore("naturale: nascita non esplicita nella frase della risposta", sq)
    if ("one of" in qn or re.search(r"\bname (a|an)\b|\bgive (?:an? )?example\b|\bsome (researchers|scientists|historians)\b", qn)):
        errore("naturale: domanda con risposta aperta o alcune posizioni", (sq, q))
    if any(re.search(r"['’]s\s*$", a) for a in B["risposte_B"]):
        errore("naturale: riferimento possessivo incompleto", sq)
    if fam == "RIM-nat":
        if B["tipo_attributo"] == "nome":
            a = rim_nome_residuo(b, c, B["risposte_B"])
            if a:
                errore("RIM-nat: nome o variante morfologica ancora presente", (sq, a))
        fb, fc = frasi_naturali(b), frasi_naturali(c)
        scelti = set(fc)
        for i, f in enumerate(fb):
            if f in scelti and i and fb[i - 1] not in scelti:
                if (f.split()[0] in {"It", "Its", "They", "Their", "He", "She", "His", "Her", "These", "Those", "This", "Such"}
                        or (f.startswith("The ") and len(f.split()) > 1 and f.split()[1][0].islower())):
                    errore("RIM-nat: anafora o sintagma definito dopo una frase rimossa", (sq, f[:90]))
                if re.search(r"^(?:In (?:the )?(?:following|subsequent|next)|Similarly\b|Later\b|Afterwards\b|(?:A|One) (?:mere )?[^.!?]{0,35}\blater\b)", f):
                    errore("RIM-nat: riferimento temporale dopo una frase rimossa", (sq, f[:90]))
        if B["tipo_attributo"] == "numero":
            if re.search(r"\bhow many\b|\bnumber of\b", q, re.I) and re.search(r"(?:^|[.!?]\s+)(?:These|Those) (?:are|include)\b[^.!?]+(?:,|\band\b)", c):
                errore("RIM-nat: enumerazione residua", sq)
            if re.search(r"\bhow many\b|\bnumber of\b", q, re.I) and re.search(r":\s*[^.!?]*(?:;|,\s*[A-Za-z]|\band\b)", c):
                errore("RIM-nat: possibile enumerazione dopo i due punti", sq)
            if via_calcolo_v(q, c, valore_base_v(B["risposte_B"][0])):
                errore("RIM-nat: calcolo residuo", sq)
    else:
        dis = C.get("distrattore", "")
        # Si ricostruisce lo span effettivamente cambiato, non il primo
        # riferimento dell'elenco (che può includere 'rows' oppure '%').
        span_modificato = None
        for ref in sorted(set(B["risposte_B"]), key=lambda x: (len(x), x)):
            for occ in re.finditer(re.escape(ref), b):
                left, right = b[:occ.start()], b[occ.end():]
                if c in (left + ref + " or " + dis + right, left + dis + " or " + ref + right):
                    span_modificato = ref
                    break
            if span_modificato is not None:
                break
        a0 = span_modificato or min(B["risposte_B"], key=len)
        residuo_contesto = b.replace(a0, " VALORE_RIMOSSO ", 1)
        if B["tipo_attributo"] == "numero" and re.search(r"\b(?:average|averaged|mean)\b", residuo_contesto, re.I):
            if re.search(r"\b(?:maximum|minimum|at most|at least|as high as|as low as|up to|no more than)\b", residuo_contesto, re.I):
                errore("DUE-nat: media con estremi da verificare", sq)
        if B["tipo_attributo"] == "anno" and re.search(r"\b(?:after|before|since|until|from|between)\s+(?:the (?:year|years) )?\d{4}\b", residuo_contesto, re.I):
            errore("DUE-nat: vincolo cronologico residuo", sq)
        if re.search(r"['’]s\s*$", dis):
            errore("DUE-nat: distrattore possessivo incompleto", (sq, dis))
        if B["tipo_attributo"] == "numero":
            a = a0
            frase = next((f for f in frasi_naturali(b) if a in f), "")
            residuo = b.replace(a, " VALORE_RIMOSSO ", 1)
            if via_calcolo_v(q, residuo, valore_base_v(a)):
                errore("DUE-nat: totale o valore ricavabile dalle altre quantità", sq)
            if re.search(r"\bhow many of\b", q, re.I) or re.search(re.escape(a) + r"\s+(?:out )?of\s+(?:the\s+)?", frase, re.I):
                errore("DUE-nat: conteggio di un sottoinsieme", sq)
            if re.search(r"\bhow many\b|\bnumber of\b", q, re.I) and (re.search(r":\s*[^.!?]*(?:;|,\s*[A-Za-z]|\band\b)", residuo)
                    or re.search(r"(?:^|[.!?]\s+)(?:These|Those) (?:are|include)\b[^.!?]+(?:,|\band\b)", residuo)):
                errore("DUE-nat: enumerazione residua", sq)
        fonte = C.get("fonte_distrattore")
        if not fonte or not fonte.get("sq_id") or not fonte.get("domanda"):
            errore("DUE-nat: provenienza del distrattore mancante", sq)
        elif squad is not None:
            ex = squad.get(fonte["sq_id"])
            if not ex or ex["question"] != fonte["domanda"] or fonte.get("valore") != dis:
                errore("DUE-nat: fonte del distrattore non corrispondente a SQuAD", sq)
            elif not any(norm(dis) == norm(a) or re.search(r"(?<!\w)" + re.escape(norm(dis)) + r"(?!\w)", norm(a)) for a in ex["answers"]):
                errore("DUE-nat: il distrattore non è una risposta della fonte", sq)
            if ex is not None and (fonte.get("frase", "") not in ex["context"]
                                   or (ex.get("title") and fonte.get("titolo") != ex["title"])):
                errore("DUE-nat: frase o articolo della fonte non corrispondenti", sq)
        if B["tipo_attributo"] == "nome":
            if C.get("origine_distrattore") != "stesso articolo" or (fonte or {}).get("titolo") != B["titolo"]:
                errore("DUE-nat: nome fuori dall'articolo", sq)
            if C.get("classe_domanda") in {None, "cosa:other", "cosa:entity", "cosa:thing"}:
                errore("DUE-nat: classe nominale generica", sq)
            if not fonte or not fonte.get("evidenza"):
                errore("DUE-nat: ruolo nominale non documentato", sq)
            else:
                if C.get("classe_domanda") == "persona":
                    if re.search(r"\b(?:muslims|christians|catholics|protestants|mongols|chinese|administrators|troops|soldiers|people|immigrants|settlers|officials|scientists|researchers)\b", dis, re.I):
                        errore("DUE-nat: nome collettivo usato come persona", sq)
                    source_question = fonte["domanda"]
                    autore = r"\b(?:wrote|write|written|author|writer|novelist|poet|journalist|bestseller)\b"
                    if re.search(autore, q, re.I) and not re.search(autore, source_question, re.I):
                        errore("DUE-nat: ruolo di autore non documentato nella domanda fonte", sq)
                    if re.search(r"\bfounder\b|\bfounded\b", q, re.I) and re.search(r"\b(?:corporation|company|firm|business)\b", q, re.I):
                        if not (re.search(r"\bfounder\b|\bfounded\b", source_question, re.I)
                                and re.search(r"\b(?:corporation|company|firm|business)\b", source_question, re.I)):
                            errore("DUE-nat: fondatore di impresa non documentato nella domanda fonte", sq)
                    militare = r"\b(?:army|military|attack|campaign|battle|general|commander)\b"
                    if re.search(militare, q, re.I) and not re.search(militare, source_question, re.I):
                        errore("DUE-nat: ruolo militare non documentato nella domanda fonte", sq)
                for lemma in fonte["evidenza"].split(", "):
                    inizio = re.escape(lemma[:-1]) + r"(?:y|ies)" if lemma.endswith("y") else re.escape(lemma)
                    if not all(re.search(r"\b" + inizio, testo, re.I)
                               for testo in (q, fonte["domanda"])):
                        errore("DUE-nat: evidenza del ruolo assente dalle domande", (sq, lemma))
                regioni = {"england": ("england", "english"), "scotland": ("scotland", "scottish"),
                           "holland": ("holland", "netherlands", "dutch"), "netherlands": ("holland", "netherlands", "dutch"),
                           "france": ("france", "french"), "germany": ("germany", "german"), "china": ("china", "chinese"),
                           "japan": ("japan", "japanese"), "india": ("india", "indian"), "nepal": ("nepal", "nepali", "nepalese")}
                for regione, aliases in regioni.items():
                    if re.search(r"\b" + regione + r"\b", q, re.I) and not any(
                            re.search(r"\b" + a + r"\b", fonte["domanda"] + " " + fonte["frase"], re.I) for a in aliases):
                        errore("DUE-nat: vincolo geografico non corroborato dalla fonte", (sq, regione))
    # Rischio ferroviario: domanda generica sul fornitore e altri operatori ancora nominati.
    if re.search(r"\btrain|\brail", q, re.I) and re.search(r"compan(?:y|ies)|service", q, re.I):
        residue = frasi_naturali(c) if fam == "RIM-nat" else [f for f in frasi_naturali(b) if not any(a in f for a in B["risposte_B"])]
        if any(re.search(r"\b(?:train|trains|railway|railways|railroad|railroads|branchline|branchlines)\b", f, re.I) for f in residue):
            errore("naturale: altra via nominale ferroviaria non esclusa", sq)



def controlla_naturale(righe, registro, squad):
    nat = [r for r in righe if r["insieme"] == "naturale"]
    coppie = defaultdict(dict)
    for r in nat:
        coppie[(r["famiglia"], r["sq_id"])][r["kind"]] = r
    per_fam = Counter(f for f, _ in coppie)
    for fam in ("RIM-nat", "DUE-nat"):
        if per_fam[fam] != N_NATURALE:
            errore("naturale: coppie diverse dalla quota", (fam, per_fam[fam]))
    usate = defaultdict(set)
    for (fam, sq), d in coppie.items():
        if set(d) != {"B", "C"}:
            errore("naturale: coppia incompleta", (fam, sq))
            continue
        B, C = d["B"], d["C"]
        if sq in usate["domande"]:
            errore("naturale: domanda usata due volte (anche fra famiglie)", sq)
        usate["domande"].add(sq)
        if B["contesto"] in usate[fam]:
            errore("naturale: paragrafo usato due volte nella stessa famiglia", (fam, sq))
        usate[fam].add(B["contesto"])
        if B["domanda"] != C["domanda"] or B["risposte_B"] != C["risposte_B"]:
            errore("naturale: domanda o risposte diverse fra B e C", sq)
        if squad is not None:
            ex = squad.get(sq)
            if ex is None or ex["context"] != B["contesto"] or ex["question"] != B["domanda"] \
                    or list(ex["answers"]) != list(B["risposte_B"]):
                errore("naturale: B diverso dalla fonte SQuAD", sq)
        m = risposte_coerenti(B["risposte_B"], B["tipo_attributo"])
        if m:
            errore("naturale: riferimenti non coerenti", (fam, sq, m))
        controlli_nuovi_naturale(B, C, sq, fam, squad)
        forme = {norm(a) for a in B["risposte_B"] if norm(a)}
        if fam == "RIM-nat":
            fb, fc = frasi_naturali(B["contesto"]), frasi_naturali(C["contesto"])
            it = iter(fb)
            if not all(any(x == y for y in it) for x in fc):
                errore("RIM-nat: le frasi di C non sono frasi intere di B, nello stesso ordine", sq)
            if len(fc) < 3:
                errore("RIM-nat: meno di 3 frasi vere in C", (sq, len(fc)))
            m = testo_integro(C["contesto"])
            if m:
                errore("RIM-nat: segni di taglio in C", (sq, m))
            nc = norm(C["contesto"])
            if any(re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", nc) for a in forme):
                errore("RIM-nat: la risposta resta in C", sq)
            if B["tipo_attributo"] in ("anno", "numero"):
                v = anni(B["risposte_B"][0]) if B["tipo_attributo"] == "anno" else numeri(B["risposte_B"][0])
                vc = anni(C["contesto"]) if B["tipo_attributo"] == "anno" else numeri(C["contesto"])
                if set(v) & set(vc):
                    errore("RIM-nat: il valore della risposta resta in C (in altra forma)", sq)
        else:
            b, c, dis = B["contesto"], C["contesto"], C.get("distrattore", "")
            # C deve essere B con una risposta di SQuAD sostituita da «risposta or distrattore» o «distrattore or risposta»
            ok = False
            for span in set(B["risposte_B"]):
                for mm in re.finditer(re.escape(span), b):
                    s, e = mm.start(), mm.end()
                    if c in (b[:s] + f"{span} or {dis}" + b[e:], b[:s] + f"{dis} or {span}" + b[e:]):
                        ok = True
            if not dis or not ok:
                errore("DUE-nat: C non è B con la sola aggiunta «or distrattore» accanto alla risposta", (sq, dis))
            if occorrenze(c, "or") != occorrenze(b, "or") + 1:
                errore("DUE-nat: «or» non aumenta di uno", sq)
            if norm(dis) and re.search(r"(?<!\w)" + re.escape(norm(dis)) + r"(?!\w)", norm(b)):
                errore("DUE-nat: il distrattore è già nel paragrafo", sq)
            if norm(dis) in forme:
                errore("DUE-nat: il distrattore coincide con una risposta", sq)
            t = B["tipo_attributo"]
            if t == "anno":
                a, x = anni(B["risposte_B"][0]), anni(dis)
                if len(a) != 1 or len(x) != 1 or not 0 < abs(a[0] - x[0]) <= 50:
                    errore("DUE-nat: anno distrattore non plausibile (oltre 50 anni)", (sq, B["risposte_B"][0], dis))
            elif t == "numero":
                a, x = numeri(B["risposte_B"][0]), numeri(dis)
                if len(a) != 1 or len(x) != 1:
                    errore("DUE-nat: numero non leggibile", (sq, B["risposte_B"][0], dis))
                else:
                    (a,), (x,) = a, x
                    ok = a != x and a > 0 and x > 0 and (abs(a - x) <= 5 if max(a, x) <= 20 else 0.5 <= x / a <= 2)
                    if a.is_integer() and not x.is_integer():
                        ok = False
                    q = B["domanda"]
                    if (re.search(r"\bpercent(?:age)?\b", q, re.I)
                            and not re.search(r"\bincrease\b|\bgrowth\b|\bchange\b|\brise\b|\bdecrease\b", q, re.I)
                            and x > 100):
                        ok = False
                    if not ok:
                        errore("DUE-nat: numero distrattore non plausibile", (sq, B["risposte_B"][0], dis))
    # registro dei candidati del naturale: ogni coppia scelta è «scelto», ogni esclusione ha il suo controllo, e prima
    # dell'ultima coppia scelta nessun candidato è saltato per quota piena (primi validi nell'ordine fissato)
    if registro is None:
        errore("registro dei candidati del naturale mancante", "registro_candidati_naturale.json")
        return
    ids = [r["sq_id"] for r in registro]
    if len(ids) != len(set(ids)):
        errore("registro naturale con domande ripetute", len(ids) - len(set(ids)))
    for chiave, fam in (("RIM", "RIM-nat"), ("DUE", "DUE-nat")):
        scelti_reg = {r["sq_id"] for r in registro if r.get(chiave) == "scelto"}
        scelti_righe = {sq for f, sq in coppie if f == fam}
        if scelti_reg != scelti_righe:
            errore("registro naturale: scelti diversi dalle righe", (fam, len(scelti_reg), len(scelti_righe)))
        ordini = sorted(r["ordine"] for r in registro if r.get(chiave) == "scelto")
        if ordini:
            for r in registro:
                if r.get("ordine", 1e9) < ordini[-1] and str(r.get(chiave, "")).startswith("non valutato: quota"):
                    errore("registro naturale: candidato saltato per quota prima dell'ultimo scelto", (fam, r["sq_id"]))
        for r in registro:
            s = r.get(chiave)
            if s is None:
                continue
            if not (s == "scelto" or (s.startswith("escluso: ") and len(s) > 10) or s.startswith("non valutato: ")):
                errore("registro naturale: esito senza motivo", (fam, r["sq_id"], s))
    for r in registro:
        if r.get("fase") == "filtro" and not str(r.get("esito", "")).startswith("escluso: "):
            errore("registro naturale: filtro senza motivo", r["sq_id"])


def main(cart, squad_path=None):
    L = lambda f: json.load(open(f))
    dati = f"{cart}/dati"
    righe = L(f"{dati}/righe_C.json")
    rap = L(f"{dati}/rapporto_selezione.json")
    if rap.get("versione") != "C-sel-7" or rap.get("naturale", {}).get("regole_semantiche") != "C-nat-7":
        errore("versione della selezione o dei filtri semantici non attesa", rap.get("versione"))
    sel = {n: L(f"{dati}/testC_sintetico_{n}.json")["passaggi"] for n in ("definitivo", "prova")}
    ris = {n: L(f"{cart}/testC_sintetico_{n}_riserva.json")["passaggi"] for n in ("definitivo", "prova")}
    reg = {n: L(f"{dati}/registro_candidati_{n}.json") for n in ("definitivo", "prova")}
    try:
        reg_nat = L(f"{dati}/registro_candidati_naturale.json")
    except FileNotFoundError:
        reg_nat = None
    squad = None
    if squad_path:
        sq = L(squad_path)
        if "data" in sq:                      # file ufficiale dev-v2.0.json
            squad = {q["id"]: dict(title=art["title"], context=par["context"], question=q["question"], answers=[a["text"] for a in q["answers"]])
                     for art in sq["data"] for par in art["paragraphs"] for q in par["qas"]}
        else:                                 # {id: {context, question, answers: [testi]}}, scritto dal notebook
            squad = sq
    # righe: uniche, coppie complete, prompt nel formato, coincidenti con i passaggi scelti
    ids = [r["row_id"] for r in righe]
    if len(ids) != len(set(ids)):
        errore("row_id ripetuti", len(ids) - len(set(ids)))
    for r in righe:
        if r["prompt"] != f"{ISTRUZIONE}\n\nPassage: {r['contesto']}\n\nQuestion: {r['domanda']}":
            errore("prompt fuori formato", r["row_id"])
    for nome, ps in sel.items():
        attese = {(p["passaggio_id"], fam, lato): F[lato]["testo"] for p in ps for fam, F in p["famiglie"].items()
                  for lato in ("B", "C")}
        trovate = {(r["passaggio_id"], r["famiglia"], r["kind"]): r["contesto"] for r in righe
                   if r["insieme"] == f"sintetico_{nome}"}
        if attese != trovate:
            errore("righe sintetiche diverse dai passaggi scelti", (nome, len(attese), len(trovate)))
        for p in ps:
            controlla_passaggio(p, nome)
    controlla_regola(ris["definitivo"], sel["definitivo"], reg["definitivo"], "definitivo", quote=QUOTE)
    controlla_regola(ris["prova"], sel["prova"], reg["prova"], "prova", n=N_PROVA)
    # intersezioni: ID e nomi fra prova e definitivo (sulle intere riserve), domande del naturale
    a, b = ris["definitivo"], ris["prova"]
    if {p["passaggio_id"] for p in a} & {p["passaggio_id"] for p in b}:
        errore("prova e definitivo con ID in comune", "")
    comuni = parole_nomi(a) & parole_nomi(b)
    if comuni:
        errore("prova e definitivo con nomi in comune", sorted(comuni)[:10])
    controlla_naturale(righe, reg_nat, squad)
    print(f"righe: {dict(Counter(r['insieme'] for r in righe))}")
    print(f"controlli sintetici: {sum(len(p['famiglie']) for ps in sel.values() for p in ps)} coppie; naturale: "
          f"{len({(r['famiglia'], r['sq_id']) for r in righe if r['insieme'] == 'naturale'})} coppie"
          f"{' (confrontate con SQuAD)' if squad else ' (senza il file di SQuAD: fonte non confrontata)'}")
    if err:
        print(f"ERRORI: {sum(err.values())}")
        for k, n in err.most_common():
            print(f"  {n:5d}  {k}")
            for e in esempi[k]:
                print(f"         es. {str(e)[:200]}")
        sys.exit(1)
    print("VERIFICA SUPERATA: nessun errore")


if __name__ == "__main__":
    args = sys.argv[1:]
    sq = None
    if "--squad" in args:
        i = args.index("--squad")
        sq = args[i + 1]
        args = args[:i] + args[i + 2:]
    main(args[0], sq)
