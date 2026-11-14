# Test C, selezione dei dati (protocollo v3, §3.3 punto 4, §3.3c, §3.5). Gira in env_sirin, senza GPU: servono solo i
# tokenizer dei 4 modelli (alle revisioni fissate) e del giudice M3, e SQuAD 2.0 dev alla revisione fissata.
#   Sintetico: per ogni passaggio della riserva, nell'ordine, e per ogni famiglia si sceglie la coppia di varianti
#   (B, C) con la differenza massima più piccola sui 4 tokenizer (a parità la prima), se è ≤ TOLLERANZA; poi si controlla il testo ricevuto da
#   ogni modello (prompt di risposta con il chat template e formato SIRIN di M2, ≤ 512 token, confine dell'assistente,
#   ritorno identico dalla decodifica). Un passaggio entra solo se tutte le sue otto versioni (4 famiglie × B/C)
#   passano. Definitivo: i primi validi, nell'ordine della riserva, entro quote fisse per tipo di attributo × schema di
#   posizione (stessi 200 passaggi per tutti i modelli e metodi). Prova: i primi 10 validi.
#   Naturale (descrittivo): RIM-nat e DUE-nat da SQuAD 2.0 dev, esclusi le 400 domande di HM0 e i loro paragrafi.
# Nessuna risposta dei modelli entra in nessuna scelta. Uso: python sel_testC.py <config.json>
import hashlib
import json
import random
import re
import string
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tm_comune import chat_text, read_json, say, write_json  # noqa: E402
from tm_m2_comune import MAX_TOKEN, Renderer  # noqa: E402
import controlli_semantici_naturale as N  # noqa: E402
import gen_testC as G  # noqa: E402  (stesso generatore: i controlli formali si ripetono in questo ambiente)

ISTRUZIONE = "Answer the question using the passage. Reply with a short answer or UNKNOWN."   # protocollo v3, §4


def prompt_risposta(testo, domanda):
    return f"{ISTRUZIONE}\n\nPassage: {testo}\n\nQuestion: {domanda}"


def sha_testo(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- controlli sul testo ricevuto
def decodifica_letterale(tokenizer, ids):
    """Decodifica senza normalizzazione degli spazi: controllo fedele del prompt.

    La pulizia predefinita di alcuni tokenizer trasforma 'word ?' in 'word?'
    (e analogamente prima di altri segni): sono falsi scarti del controllo di
    integrita', non modifiche ai token presentati al modello. Non cambia
    codifica, token count, template, SIRIN o criteri di qualita' naturali.
    """
    return tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)


class Controlli:
    def __init__(self, modelli, giudice):
        from transformers import AutoTokenizer
        self.tok, self.ren = {}, {}
        self.rev = {k: v[1] for k, v in modelli.items()}
        self.rev["giudice"] = giudice[1]
        for key, (mid, sha) in modelli.items():
            self.ren[key] = Renderer(mid, sha)              # formato SIRIN di M2 (come nel notebook B)
            self.tok[key] = AutoTokenizer.from_pretrained(mid, revision=sha)
            say(f"tokenizer {key}: {mid}@{(sha or '-')[:8]}")
        self.giudice = AutoTokenizer.from_pretrained(giudice[0], revision=giudice[1])

    def descrizione(self):
        """Revisioni e impronte dei tokenizer usati (salvate prima di qualsiasi inferenza)."""
        out = {}
        for k, t in list(self.tok.items()) + [("giudice", self.giudice)]:
            vocab = t.get_vocab()
            out[k] = dict(nome=t.name_or_path, revisione=self.rev.get(k), classe=type(t).__name__, vocabolario=len(vocab),
                          impronta_vocabolario=hashlib.sha256(json.dumps(sorted(vocab.items())).encode()).hexdigest(),
                          chat_template_sha256=hashlib.sha256((t.chat_template or "").encode()).hexdigest())
        return out

    def n_testo(self, testo):
        return {k: len(t(testo, add_special_tokens=False)["input_ids"]) for k, t in self.tok.items()}

    def prompt(self, testo, domanda):
        """Problemi del testo ricevuto da ogni modello (vuoto se tutto va bene) e lunghezze."""
        probl, lung = [], {}
        p = prompt_risposta(testo, domanda)
        for k, t in self.tok.items():
            chat = chat_text(t, k, p)
            ids = t(chat, add_special_tokens=False)["input_ids"]
            dec = decodifica_letterale(t, ids)
            if testo not in dec or domanda not in dec:
                probl.append(f"{k}: passaggio o domanda non intatti nel prompt di risposta")
            lung[f"risposta_{k}"] = len(ids)
            b = self.ren[k].boundary({"contesto": testo, "domanda": domanda})
            lung[f"sirin_{k}"] = b["n_full"]
            if (b["n_full"] > MAX_TOKEN or not b["prefix_ok"] or not b["roundtrip_ok"] or b["errore_localizzatore"]
                    or b["ans_start"] != b["n_user"]):
                probl.append(f"{k}: formato SIRIN non valido ({b['n_full']} token, confine {b['ans_start']}/{b['n_user']}, "
                             f"errore {b['errore_localizzatore']})")
        from tm_m2_comune import inspection_prompt
        lung["giudice"] = len(self.giudice(inspection_prompt(testo, domanda), add_special_tokens=False)["input_ids"])
        return probl, lung


# --------------------------------------------------------------------------- sintetico
def valuta_passaggio(p, ctl, tolleranza):
    """Controlli di un candidato: restituisce (versione selezionabile o None, problemi). Entra solo se tutte e otto le
    versioni (4 famiglie × B/C) superano tutti i controlli."""
    if p["controlli_generatore"]["problemi"]:
        return None, ["controlli del generatore: " + "; ".join(p["controlli_generatore"]["problemi"][:3])]
    ripetuti, _ = G.controlla_passaggio(p)          # controlli formali ripetuti qui, sul testo di ogni variante
    if ripetuti:
        return None, ["controlli del generatore ripetuti: " + "; ".join(ripetuti[:3])]
    probl, fam_out = [], {}
    for fam, F in p["famiglie"].items():
        # fra le coppie di varianti si sceglie quella con la differenza massima (sui 4 tokenizer) più piccola; a parità,
        # la prima nell'ordine fisso (B, poi C). Entra solo se quella differenza è ≤ tolleranza.
        scelta, migliore = None, None
        n_c = [ctl.n_testo(vc["testo"]) for vc in F["C"]]
        for kb, vb in enumerate(F["B"]):
            nb = ctl.n_testo(vb["testo"])
            for kc, nc in enumerate(n_c):
                diff = {k: nc[k] - nb[k] for k in nb}
                d = max(abs(x) for x in diff.values())
                if migliore is None or d < migliore:
                    migliore, scelta = d, (kb, kc, diff, nb, nc)
        if migliore is None or migliore > tolleranza:
            scelta = None
        if scelta is None:
            probl.append(f"{fam}: nessuna coppia di varianti entro {tolleranza} token")
            continue
        kb, kc, diff, nb, nc = scelta
        lati = {}
        for lato, k in (("B", kb), ("C", kc)):
            v = F[lato][k]
            # testo destinato al modello: il passaggio estratto dal prompt di risposta coincide con la variante e,
            # riletto, dà la stessa rappresentazione e gli stessi valori compatibili
            prm = prompt_risposta(v["testo"], p["domanda"])
            estratto = prm.split("\n\nPassage: ", 1)[1].rsplit("\n\nQuestion: ", 1)[0]
            atteso = [p["valore_B"]] if lato == "B" else ("LIBERO" if fam == "RIM" else sorted([p["valore_B"], p["valore_alternativo"]]))
            try:
                ent, rep2 = G.analizza(p["genere"], p["tipo_attributo"], G.dividi_frasi(estratto))
                ris2, _ = G.risolvi(rep2)
                if estratto != v["testo"] or rep2 != v["rep"] or ris2 != atteso:
                    probl.append(f"{fam}/{lato}: il passaggio nel prompt non dà la rappresentazione attesa")
            except ValueError as e:
                probl.append(f"{fam}/{lato}: rilettura del passaggio nel prompt fermata: {e}")
            pr, lung = ctl.prompt(v["testo"], p["domanda"])
            probl += [f"{fam}/{lato}: {x}" for x in pr]
            lati[lato] = dict(variante=k, testo=v["testo"], frasi=v["frasi"], rep=v["rep"], lunghezze=lung,
                              token_testo=nb if lato == "B" else nc)
        fam_out[fam] = dict(posizione=F["posizione"], indici_blocco=F["indici_blocco"],
                            bilanciamento=F["bilanciamento"], differenza_token_C_meno_B=diff, **lati)
    if probl:
        return None, probl
    q = {k: v for k, v in p.items() if k != "famiglie"}
    q["famiglie"] = fam_out
    return q, []


def seleziona_sintetico(riserva, ctl, tolleranza, quote=None, n_totale=None):
    """Regola di selezione (protocollo v3, §3.3c). Si valutano tutti i candidati nell'ordine della riserva; poi:
    - definitivo: per ogni strato (tipo di attributo, schema di posizione) i primi validi fino alla quota fissata;
    - prova: i primi n_totale validi.
    Restituisce i passaggi scelti e il registro di tutti i candidati (ordine, esito, motivi)."""
    registro, validi = [], []
    for p in riserva:
        q, probl = valuta_passaggio(p, ctl, tolleranza)
        registro.append(dict(ordine=p["indice_riserva"], passaggio_id=p["passaggio_id"], tipo=p["tipo_attributo"],
                             schema_posizione=p.get("schema_posizione"), genere=p["genere"],
                             esito="valido" if q else "escluso", motivi=probl))
        if q:
            validi.append(q)
    scelti, presi = [], Counter()
    for q in validi:
        strato = f"{q['tipo_attributo']}/{q.get('schema_posizione')}"
        rec = next(r for r in registro if r["passaggio_id"] == q["passaggio_id"])
        if quote is not None:
            if presi[strato] < quote[strato]:
                presi[strato] += 1
                scelti.append(q)
                rec["esito"] = "scelto"
            else:
                rec["esito"] = "valido, quota dello strato già piena"
        else:
            if len(scelti) < n_totale:
                scelti.append(q)
                rec["esito"] = "scelto"
            else:
                rec["esito"] = "valido, numero già raggiunto"
    mancanti = ({k: v - presi[k] for k, v in quote.items() if presi[k] < v} if quote is not None
                else ({"totale": n_totale - len(scelti)} if len(scelti) < n_totale else {}))
    return scelti, registro, mancanti


def righe_sintetico(passaggi, insieme):
    righe = []
    for p in passaggi:
        for fam, F in p["famiglie"].items():
            for lato in ("B", "C"):
                righe.append(dict(
                    row_id=f"{p['passaggio_id']}|{fam}|{lato}", insieme=insieme, passaggio_id=p["passaggio_id"],
                    famiglia=fam, kind=lato, pair_key=f"{p['passaggio_id']}|{fam}", genere=p["genere"],
                    tipo_attributo=p["tipo_attributo"], posizione=F["posizione"], bilanciamento=F["bilanciamento"],
                    contesto=F[lato]["testo"], domanda=p["domanda"], prompt=prompt_risposta(F[lato]["testo"], p["domanda"]),
                    valore_B=p["valore_B"], valore_alternativo=p["valore_alternativo"],
                    risposte_B=p["risposte_B"], risposte_alternativo=p["risposte_alternativo"],
                    valori_compatibili=([p["valore_B"]] if lato == "B" else
                                        ("LIBERO" if fam == "RIM" else sorted([p["valore_B"], p["valore_alternativo"]]))),
                    variante=F[lato]["variante"]))
    return righe


# --------------------------------------------------------------------------- naturale (SQuAD 2.0 dev)
def normalizza(s):                                     # normalizzazione SQuAD
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


UNITA = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
DECINE = {30: "thirty", 40: "forty", 50: "fifty", 60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety"}
STOP = set("a an the of in on at to for from by with and or is was were are be been what which who whom whose when "
           "where why how did does do many much year years did as that this these those it its his her their they he "
           "she after before during than into about".split())


def forme_equivalenti(ans):
    """Forme di una risposta che si cercano nel testo: la risposta, senza virgole delle migliaia, e per i numeri
    piccoli la forma in lettere (e viceversa)."""
    f = {normalizza(ans)}
    a = ans.replace(",", "")
    f.add(normalizza(a))
    if a.strip().isdigit():
        n = int(a)
        if n <= 20:
            f.add(UNITA[n])
        if n in DECINE:
            f.add(DECINE[n])
    for i, w in enumerate(UNITA):
        if normalizza(ans) == w:
            f.add(str(i))
    for n, w in DECINE.items():
        if normalizza(ans) == w:
            f.add(str(n))
    return {x for x in f if x}


def contiene(frase_norm, forma):
    return re.search(r"(?<!\w)" + re.escape(forma) + r"(?!\w)", frase_norm) is not None


def tipo_risposta(ans):
    a = ans.strip()
    if re.fullmatch(r"(1[0-9]{3}|20[0-2][0-9])", a):
        return "anno"
    if re.fullmatch(r"[0-9][0-9,\.]*", a) or normalizza(a) in UNITA[1:] or normalizza(a) in DECINE.values():
        return "numero"
    words = a.split()
    if 1 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.lower() not in STOP) and not any(
            ch.isdigit() for ch in a):
        return "nome"
    return None


ABBREVIAZIONI = set("mr mrs ms dr st mt jr sr prof gen col lt capt sgt rev gov sen rep no nos vol vols vs etc e.g i.e "
                    "u.s u.k u.n inc co ltd corp ave jan feb mar apr jun jul aug sep sept oct nov dec a.m p.m c ca "
                    "approx fig al op ed eds dept univ est bros".split())


def frasi_di(testo):
    """Divisione in frasi (C-sel-4). Un confine è un punto, punto esclamativo o interrogativo seguito da spazio e da
    maiuscola, virgolette o parentesi, tranne quando:
    - la parola che finisce con il punto è un'iniziale («A.», «H.») o un'abbreviazione dell'elenco («St.», «U.S.»);
    - il punto sta dentro una parentesi o fra virgolette doppie non ancora chiuse.
    Così un inciso fra parentesi che contiene più frasi resta un'unica unità (correzioni di Simona dell'11 novembre).
    C-sel-5 (11 novembre, sera): il confine vale anche prima di una cifra («in 1413. 14th century …») o di una maiuscola
    non ASCII («Ögedei»), le parentesi quadre contano come le tonde e le chiusure possono includere ] e virgolette curve."""
    testo = testo.strip()
    confini = []
    for m in re.finditer(r"[\.\!\?][\"'\)\]\u201d\u2019]*\s+(?=\S)", testo):
        dopo = testo[m.end()]
        if not (dopo.isupper() or dopo.isdigit() or dopo in "\"'(\u201c"):    # C-sel-5: anche cifre e maiuscole accentate
            continue
        prima = testo[:m.start() + 1]
        parola = re.search(r"(\S+)$", prima).group(1)
        nuda = parola.strip("\"'()[]").rstrip(".").lower()
        if testo[m.start()] == "." and (re.fullmatch(r"[A-Za-z]", nuda) or nuda in ABBREVIAZIONI
                                         or re.fullmatch(r"(?:[A-Za-z]\.)+[A-Za-z]", nuda)):
            continue
        fino = testo[:m.end()]
        if (fino.count("(") + fino.count("[") > fino.count(")") + fino.count("]") or fino.count('"') % 2 == 1
                or fino.count("\u201c") > fino.count("\u201d")):
            continue
        confini.append(m.end())
    parti, ini = [], 0
    for c in confini:
        parti.append(testo[ini:c].strip())
        ini = c
    parti.append(testo[ini:].strip())
    return [x for x in parti if x]


def testo_integro(testo):
    """Il testo C del naturale non deve mostrare segni di taglio: parentesi bilanciate e chiuse in ordine, virgolette
    doppie in numero pari, ogni frase che comincia con maiuscola, cifra, virgolette o parentesi e che finisce con un
    segno di fine frase (eventualmente seguito da virgolette o parentesi)."""
    prof = 0
    for ch in testo:
        prof += (ch == "(") - (ch == ")")
        if prof < 0:
            return False
    if prof != 0 or testo.count('"') % 2 or testo.count("\u201c") != testo.count("\u201d"):
        return False
    for f in frasi_di(testo):
        if not re.match(r"[A-Z0-9\"'\(\u201c]", f) or not re.search(r"[\.\!\?][\"'\)\u201d]*$", f):
            return False
    return True


DOMANDA_ANNO = re.compile(r"\b(what|which|in what|in which) year\b|\bwhen\b", re.I)
DOMANDA_NUMERO = re.compile(r"\bhow (many|much)\b", re.I)


def risposte_coerenti(answers, tipo, domanda):
    """Le risposte di riferimento di SQuAD devono dire la stessa cosa (C-sel-4, correzioni di Simona dell'11 novembre):
    - si prende come risposta canonica la più breve fra quelle del tipo (anno, numero o nome);
    - ogni altra risposta deve contenere la canonica o esserne contenuta, dopo la normalizzazione SQuAD
      («Rankine» e «Rankine cycle», «2003» e «March 2003» vanno bene; «1864» e «Battle of Cedar Creek» no);
    - per anni e numeri, ogni risposta non deve contenere altri valori del tipo («415,000 to 587,000» no; «270,000» e
      «121,200» no);
    - una domanda sull'anno vuole un anno, una domanda «how many/how much» un numero.
    Restituisce il motivo dell'esclusione, oppure None."""
    uniche = sorted({a.strip() for a in answers if a.strip()})
    del_tipo = sorted((a for a in uniche if tipo_risposta(a) == tipo), key=lambda a: (len(a), a))
    if not del_tipo:
        return "nessuna risposta di riferimento del tipo"
    canon = normalizza(del_tipo[0])
    valore = normalizza(del_tipo[0].replace(",", ""))
    for a in uniche:
        na = normalizza(a)
        if not (contiene(na, canon) or contiene(canon, na)):
            return "risposte di riferimento con valori diversi"
        if tipo in ("anno", "numero"):
            vals = {normalizza(v.replace(",", "")) for v in valori_stesso_tipo(a, tipo)}
            vals = {v.rstrip(".") for v in vals if v}
            if vals and vals != {valore}:
                return "risposte di riferimento con valori diversi"
    if re.search(r"\b(what|which) year\b", domanda, re.I) and tipo != "anno":
        return "domanda sull'anno con risposta che non è un anno"
    if DOMANDA_NUMERO.search(domanda) and tipo != "numero":
        return "domanda «how many/much» con risposta che non è un numero"
    return None


def valori_stesso_tipo(frase, tipo):
    if tipo == "anno":
        return re.findall(r"(?<!\d)(1[0-9]{3}|20[0-2][0-9])(?!\d)", frase)
    if tipo == "numero":
        return re.findall(r"(?<![\w])[0-9][0-9,\.]*(?![\w])", frase) + [w for w in re.findall(r"[a-z]+", frase.lower())
                                                                     if w in UNITA[1:] or w in DECINE.values()]
    return re.findall(r"(?<!^)(?<![\.\!\?] )\b[A-Z][a-z]+(?: [A-Z][a-z]+)*", frase)


def riferimento_tipizzato(ex):
    """Il tipo non dipende dal primo annotatore: riferimenti coerenti, canonico più breve.

    Se più tipi risultano compatibili si scarta, senza preferirne uno. L'indice
    conserva l'allineamento con answer_start per la sostituzione in DUE-nat.
    """
    risposte = ex["answers"]["text"]
    possibili = {tipo_risposta(a) for a in risposte} - {None}
    validi = []
    for tipo in possibili:
        if risposte_coerenti(risposte, tipo, ex["question"]) is None:
            indici = [i for i,a in enumerate(risposte) if tipo_risposta(a) == tipo]
            i = min(indici, key=lambda j: (len(risposte[j]), risposte[j], j))
            validi.append((tipo, i))
    return validi[0] if len(validi) == 1 else (None, None)


def parole_domanda(q):
    return {w for w in normalizza(q).split() if w not in STOP and len(w) > 2}


AUSILIARI = set("is was are were did does do has have had can could would will should".split())


def classe_domanda(domanda, tipo, risposta=None):
    return N.classe_precisa(domanda, tipo, risposta)


def numero_di(testo):
    """Valore di una risposta numerica. C-sel-5: le cifre si leggono prima della normalizzazione di SQuAD, che toglie la
    punteggiatura e quindi anche il punto decimale (in C-sel-4 «11.1» valeva 111 e «0.2» valeva 2)."""
    c = testo.replace(",", "").strip().lower()
    c = re.sub(r"^(?:a|an|the)\s+", "", c).strip().strip("$£€%").strip()
    if re.fullmatch(r"[0-9]+(\.[0-9]+)?", c):
        return float(c)
    t = normalizza(testo.replace(",", ""))
    if t in UNITA:
        return float(UNITA.index(t))
    for n, w in DECINE.items():
        if t == w:
            return float(n)
    return None


def distrattore_plausibile(risposta, candidato, tipo):
    """Anni entro 50 anni dalla risposta; numeri dello stesso ordine di grandezza (fra metà e doppio, e per i numeri
    fino a 20 entro 5). Per i nomi questo controllo è neutro: si richiedono
    separatamente classe precisa e provenienza con evidenza del ruolo."""
    if tipo == "anno":
        a, b = numero_di(risposta), numero_di(candidato)
        return a is not None and b is not None and 0 < abs(a - b) <= 50
    if tipo == "numero":
        a, b = numero_di(risposta), numero_di(candidato)
        if a is None or b is None or a == b or a <= 0 or b <= 0:
            return False
        if a.is_integer() and not b.is_integer():
            return False
        return abs(a - b) <= 5 if max(a, b) <= 20 else 0.5 <= b / a <= 2
    return True


def testo_ricevuto_ok(it, ctl, motivi, fam):
    """Controlli sul testo ricevuto dai modelli (B e C), fatti prima di accettare la coppia: se non passa, la coppia
    si scarta e si prosegue con i candidati successivi fino alla quota. Restituisce l'elenco dei problemi (vuoto se va)."""
    probl = []
    for lato in ("B", "C"):
        pr, lung = ctl.prompt(it[lato], it["ex"]["question"])
        probl += [f"{lato}: {x}" for x in pr]
        it[f"lunghezze_{lato}"] = lung
    if probl:
        motivi[f"{fam}: testo ricevuto non valido"] += 1
    return probl


def costruisci_naturale(cfg, ctl):
    from datasets import load_dataset
    sys.path.insert(0, str(Path(__file__).parent))
    rev = cfg["squad_revisione"]
    tr = load_dataset("rajpurkar/squad_v2", split="train", revision=rev)
    va = load_dataset("rajpurkar/squad_v2", split="validation", revision=rev)
    # le 400 domande di HM0, ricostruite come nella cella 6 dei notebook A e B (seme 20261106, impronta del test 4)
    import numpy as np
    rng = np.random.default_rng(20261106)
    titles = sorted(set(tr["title"]))
    rng.shuffle(titles)
    cut = int(0.6 * len(titles))
    T_tr, T_cal = set(titles[:cut]), set(titles[cut:])
    un_tr = np.array([len(a["text"]) == 0 for a in tr["answers"]])
    tt = np.array(tr["title"])
    un_va = np.array([len(a["text"]) == 0 for a in va["answers"]])

    def take(mask, n):
        return np.sort(rng.choice(np.where(mask)[0], n, replace=False))
    in_tr, in_cal = np.isin(tt, list(T_tr)), np.isin(tt, list(T_cal))
    sel = [(tr, take(in_tr & ~un_tr, 300)), (tr, take(in_tr & un_tr, 300)), (tr, take(in_cal & ~un_tr, 200)),
           (tr, take(in_cal & un_tr, 200)), (va, take(~un_va, 200)), (va, take(un_va, 200))]
    SQ_INSTR = ("Answer the question using only the passage below. If the passage does not contain the answer, "
                "reply exactly UNKNOWN.")
    righe_t4 = [ds[int(i)]["id"] + SQ_INSTR + "\n\nPassage: " + ds[int(i)]["context"].strip() + "\n\nQuestion: "
                + ds[int(i)]["question"].strip() for ds, idx in sel for i in idx]
    sha_t4 = hashlib.sha256("\n".join(righe_t4).encode()).hexdigest()
    if cfg.get("sha_selezione_test4") and sha_t4 != cfg["sha_selezione_test4"]:
        raise RuntimeError(f"selezione SQuAD diversa dal test 4: {sha_t4}")
    idx_hm0 = list(sel[4][1]) + list(sel[5][1])
    hm0_ids = {va[int(i)]["id"] for i in idx_hm0}
    hm0_ctx = {va[int(i)]["context"] for i in idx_hm0}
    assert len(hm0_ids) == 400
    sha_hm0 = hashlib.sha256("\n".join(sorted(hm0_ids)).encode()).hexdigest()
    say(f"naturale: SQuAD dev {len(va)} domande, HM0 400 escluse (sha {sha_hm0[:12]}), paragrafi esclusi {len(hm0_ctx)}")

    # possibili distrattori di DUE-nat: risposte coerenti di altre domande, con tipo e classe della domanda (C-sel-4)
    classe_dist, dist_per_titolo, dev_tutti = {}, defaultdict(list), []
    for ex in va:
        if ex["id"] in hm0_ids or ex["context"] in hm0_ctx or not ex["answers"]["text"]:
            continue
        t, indice = riferimento_tipizzato(ex)
        if t is None:
            continue
        a = ex["answers"]["text"][indice]
        if N.ancoraggio_domanda(ex["question"], N.frase_del_valore(ex, a)):
            continue
        a = a.strip().rstrip(".,;:")
        if tipo_risposta(a) != t:
            continue
        classe_dist[ex["id"]] = (t, classe_domanda(ex["question"], t, a))
        dist_per_titolo[ex["title"]].append((ex, a))
        dev_tutti.append((ex, a))
    by_title = defaultdict(list)
    for ex in va:
        by_title[ex["title"]].append(ex)
    cand = []
    motivi = Counter()
    # registro di ogni domanda di SQuAD dev (C-sel-4): fase, esito e controllo esatto che non è passato
    registro = []

    def scarta(reg, chiave, motivo):
        motivi[motivo] += 1
        reg[chiave] = "escluso: " + motivo
    for ex in va:
        rec = dict(sq_id=ex["id"], titolo=ex["title"], fase="filtro")
        registro.append(rec)
        if ex["id"] in hm0_ids or ex["context"] in hm0_ctx:
            scarta(rec, "esito", "HM0 o suo paragrafo")
            continue
        if not ex["answers"]["text"]:
            rec["esito"] = "escluso: domanda senza risposta in SQuAD"
            continue
        tipo, indice = riferimento_tipizzato(ex)
        if tipo is None:
            scarta(rec, "esito", "nessun tipo univoco con riferimenti coerenti")
            continue
        motivo = risposte_coerenti(ex["answers"]["text"], tipo, ex["question"])
        if motivo:
            scarta(rec, "esito", motivo)
            continue
        canon = ex["answers"]["text"][indice]
        motivo = N.ancoraggio_domanda(ex["question"], N.frase_del_valore(ex, canon))
        if motivo:
            scarta(rec, "esito", "naturale: " + motivo)
            continue
        sem = N.domanda_non_univoca(ex["question"])
        if sem:
            scarta(rec, "esito", "naturale: " + sem)
            continue
        if tipo == "nome" and not all(N.nome_intero(a) for a in ex["answers"]["text"]):
            scarta(rec, "esito", "naturale: riferimento nominale incompleto")
            continue
        rec.update(esito="candidato", tipo=tipo)
        cand.append((ex, tipo))
    rr = random.Random(cfg["seme_naturale"])
    rr.shuffle(cand)
    per_id = {r["sq_id"]: r for r in registro}
    rim, due, usati_ctx = [], [], {"RIM": set(), "DUE": set()}
    usate_domande = set()
    for ordine, (ex, tipo) in enumerate(cand):         # in ordine: si prosegue finché le due quote sono piene
        rec = per_id[ex["id"]]
        rec.update(fase="candidati", ordine=ordine)
        if len(rim) >= cfg["n_naturale"] and len(due) >= cfg["n_naturale"]:
            rec.update(RIM="non valutato: quote piene", DUE="non valutato: quote piene")
            continue
        ctx, q = ex["context"], ex["question"]
        _, indice_canonico = riferimento_tipizzato(ex)
        canon = ex["answers"]["text"][indice_canonico]
        forme = set().union(*[forme_equivalenti(a) for a in ex["answers"]["text"]])
        frasi = frasi_di(ctx)
        forme_nomi = N.forme_nominali(ex["answers"]["text"], ctx) if tipo == "nome" else set()
        con_risposta = [i for i, f in enumerate(frasi) if any(contiene(normalizza(f), x) for x in forme)
                        or any(N.frase_contiene(f, x) for x in forme_nomi)]
        if not con_risposta:
            scarta(rec, "RIM", "risposta non trovata nelle frasi")
            rec["DUE"] = rec["RIM"]
            continue
        # RIM-nat
        if len(rim) >= cfg["n_naturale"]:
            rec["RIM"] = "non valutato: quota RIM-nat piena"
        elif ctx in usati_ctx["RIM"]:
            rec["RIM"] = "non valutato: paragrafo già usato in RIM-nat"
        elif ex["id"] in usate_domande:
            rec["RIM"] = "non valutato: domanda già usata"
        else:
            pq = parole_domanda(q)
            via = set(con_risposta)
            for i, f in enumerate(frasi):
                if i in via:
                    continue
                soglia = 1 if tipo in ("anno", "numero") else 2
                if N.altre_vie_nominali(q, f) or (valori_stesso_tipo(f, tipo)
                        and len(pq & set(normalizza(f).split())) >= soglia):
                    via.add(i)                          # possibile altra via alla risposta: si toglie anche questa
            resto = [f for i, f in enumerate(frasi) if i not in via]
            testo_c = " ".join(resto)
            rec["RIM_frasi"] = dict(totali=len(frasi), tolte=sorted(via), restanti=len(resto))
            rischio = N.rischio_discorso(frasi, via)
            if tipo == "numero":
                rischio = rischio or ("enumerazione residua" if N.elenco_residuo(q, testo_c) else None)
                rischio = rischio or N.aritmetica_residua(q, testo_c, numero_di(canon))
            if rischio:
                scarta(rec, "RIM", "RIM-nat: " + rischio)
            elif len(resto) < 3:
                scarta(rec, "RIM", "RIM-nat: meno di 3 frasi dopo la rimozione")
            elif not testo_integro(testo_c):
                scarta(rec, "RIM", "RIM-nat: testo con segni di taglio (parentesi, virgolette o frase incompleta)")
            elif (any(contiene(normalizza(testo_c), x) for x in forme)
                  or any(N.frase_contiene(testo_c, x) for x in forme_nomi)):
                scarta(rec, "RIM", "RIM-nat: la risposta resta nel testo")
            else:
                it = dict(ex=ex, tipo=tipo, B=ctx, C=testo_c, tolte=sorted(via))
                pr = testo_ricevuto_ok(it, ctl, motivi, "RIM-nat")
                if not pr:
                    rim.append(it)
                    usati_ctx["RIM"].add(ctx)
                    usate_domande.add(ex["id"])
                    rec.update(RIM="scelto", DUE="non valutato: domanda già usata in RIM-nat")
                    continue
                rec["RIM"] = "escluso: RIM-nat: testo ricevuto non valido: " + "; ".join(pr[:4])
        # DUE-nat
        if len(due) >= cfg["n_naturale"]:
            rec["DUE"] = "non valutato: quota DUE-nat piena"
        elif ctx in usati_ctx["DUE"]:
            rec["DUE"] = "non valutato: paragrafo già usato in DUE-nat"
        elif ex["id"] in usate_domande:
            rec["DUE"] = "non valutato: domanda già usata"
        else:
            if len(con_risposta) != 1:
                scarta(rec, "DUE", "DUE-nat: la risposta compare in più frasi")
                continue
            start, span = ex["answers"]["answer_start"][indice_canonico], canon
            if ctx[start:start + len(span)] != span or sum(contiene(normalizza(ctx), x) for x in forme) == 0:
                scarta(rec, "DUE", "DUE-nat: span non allineato")
                continue
            if len(re.findall(r"(?<!\w)" + re.escape(normalizza(span)) + r"(?!\w)", normalizza(ctx))) != 1:
                scarta(rec, "DUE", "DUE-nat: lo span compare più volte")
                continue
            # Distrattore: stessa classe precisa, risposta coerente di un'altra domanda,
            # valore plausibile, assente dal paragrafo e diverso dalle risposte.
            # C-sel-6: i nomi restano nello stesso articolo e richiedono evidenza
            # del ruolo; soltanto anni e numeri possono ricorrere a tutto SQuAD dev.
            classe = classe_domanda(q, tipo, span)
            if classe is None:
                scarta(rec, "DUE", "DUE-nat: classe della domanda non riconosciuta")
                continue

            # C-nat-7: i vincoli possono essere in un'altra frase. Si maschera
            # soltanto lo span della risposta, poi si controlla tutto il paragrafo.
            frase_target = frasi[con_risposta[0]]
            residuo = ctx[:start] + " VALORE_RIMOSSO " + ctx[start + len(span):]
            vincolo = N.vincoli_quantitativi(q, residuo, tipo)
            if vincolo:
                scarta(rec, "DUE", "DUE-nat: " + vincolo)
                continue
            if tipo == "numero":
                rischio = N.aritmetica_residua(q, residuo, numero_di(span))
                sottoinsieme = N.sottoinsieme_numerico(q, frase_target, span)
                if rischio or N.elenco_residuo(q, residuo) or sottoinsieme:
                    motivo_num = rischio or ("conteggio di un sottoinsieme" if sottoinsieme else "enumerazione residua")
                    scarta(rec, "DUE", "DUE-nat: " + motivo_num)
                    continue
            # Nei nomi, una via lessicale residua alla stessa relazione è un motivo
            # prudente di esclusione: non si risolve scegliendo un distrattore facile.
            pq = parole_domanda(q)
            if any((tipo == "nome" and N.altre_vie_nominali(q, f))
                   for i, f in enumerate(frasi) if i not in con_risposta):
                scarta(rec, "DUE", "DUE-nat: possibile risposta nominale alternativa")
                continue

            def pool_da(esempi):
                pool = []
                for other, a in esempi:
                    if other["id"] == ex["id"] or classe_dist.get(other["id"]) != (tipo, classe):
                        continue
                    if (not (forme_equivalenti(a) & forme)
                            and not any(contiene(normalizza(ctx), x) for x in forme_equivalenti(a))
                            and distrattore_plausibile(span, a, tipo)):
                        if (tipo == "numero" and re.search(r"\bpercent(?:age)?\b", q, re.I)
                                and not re.search(r"\bincrease\b|\bgrowth\b|\bchange\b|\brise\b|\bdecrease\b", q, re.I)
                                and not (0 < numero_di(a) <= 100)):
                            continue
                        if tipo == "nome":
                            ok, evidenza = N.prova_distrattore(ex, other, a, classe)
                            if not ok:
                                continue
                        else:
                            evidenza = "stesso tipo e distanza numerica ammessa"
                        pool.append(dict(valore=a, sq_id=other["id"], titolo=other["title"], domanda=other["question"],
                                         frase=N.frase_del_valore(other, a), evidenza=evidenza))
                # Un valore si usa una volta sola; la fonte a parità è fissata per ID.
                unici = {}
                for item in sorted(pool, key=lambda x: (x["valore"], x["sq_id"])):
                    unici.setdefault(item["valore"], item)
                return list(unici.values())
            pool = pool_da(dist_per_titolo[ex["title"]])
            origine = "stesso articolo"
            if not pool and tipo != "nome" and classe in ("anno", "numero"):
                pool, origine = pool_da(dev_tutti), "SQuAD dev"
            if not pool:
                scarta(rec, "DUE", "DUE-nat: nessun distrattore plausibile")
                rec["DUE_classe"] = classe
                continue
            fonte_dis = random.Random(f"{cfg['seme_naturale']}|{ex['id']}").choice(pool)
            dis = fonte_dis["valore"]
            ordine_span = random.Random(f"{cfg['seme_naturale']}|{ex['id']}|ordine").random() < 0.5
            nuovo = f"{span} or {dis}" if ordine_span else f"{dis} or {span}"
            it = dict(ex=ex, tipo=tipo, B=ctx, C=ctx[:start] + nuovo + ctx[start + len(span):],
                      distrattore=dis, ordine_span_primo=ordine_span, classe_domanda=classe, origine_distrattore=origine,
                      fonte_distrattore=fonte_dis)
            rec.update(DUE_classe=classe, DUE_distrattore=dis, DUE_origine=origine,
                       DUE_fonte_sq_id=fonte_dis["sq_id"], DUE_evidenza=fonte_dis["evidenza"])
            pr = testo_ricevuto_ok(it, ctl, motivi, "DUE-nat")
            if pr:
                rec["DUE"] = "escluso: DUE-nat: testo ricevuto non valido: " + "; ".join(pr[:4])
                continue
            due.append(it)
            usati_ctx["DUE"].add(ctx)
            usate_domande.add(ex["id"])
            rec["DUE"] = "scelto"
    out = {"RIM-nat": rim, "DUE-nat": due}
    for fam, items in out.items():
        say(f"naturale {fam}: {len(items)} coppie su {cfg['n_naturale']}")
    righe = []
    for fam, items in out.items():
        for it in items:
            ex = it["ex"]
            pk = f"N|{fam}|{ex['id']}"
            for lato in ("B", "C"):
                r = dict(row_id=f"{pk}|{lato}", insieme="naturale", passaggio_id=f"N|{ex['id']}", famiglia=fam,
                         kind=lato, pair_key=pk, sq_id=ex["id"], titolo=ex["title"], tipo_attributo=it["tipo"],
                         contesto=it[lato], domanda=ex["question"], prompt=prompt_risposta(it[lato], ex["question"]),
                         risposte_B=ex["answers"]["text"], lunghezze=it[f"lunghezze_{lato}"])
                if fam == "RIM-nat":
                    r["frasi_tolte"] = it["tolte"]
                else:
                    r["distrattore"] = it["distrattore"]
                    r["classe_domanda"] = it["classe_domanda"]
                    r["origine_distrattore"] = it["origine_distrattore"]
                    r["fonte_distrattore"] = it["fonte_distrattore"]
                righe.append(r)
    info = dict(regole_semantiche=N.VERSIONE, squad_revisione=rev, sha_hm0_ids=sha_hm0, sha_selezione_test4=sha_t4, candidati=len(cand), motivi=dict(motivi),
                coppie={k: len(v) for k, v in out.items()}, quota=cfg["n_naturale"],
                completo={k: len(v) == cfg["n_naturale"] for k, v in out.items()},
                nota="si prosegue sui candidati successivi fino alla quota; se i candidati finiscono, l'insieme è dichiarato incompleto",
                tipi={k: dict(Counter(it["tipo"] for it in v)) for k, v in out.items()},
                registro=dict(domande=len(registro),
                              esiti_filtro=dict(Counter(r["esito"].split(":")[0] for r in registro)),
                              esiti_RIM=dict(Counter(r["RIM"].split(" non valido:")[0] for r in registro if "RIM" in r)),
                              esiti_DUE=dict(Counter(r["DUE"].split(" non valido:")[0] for r in registro if "DUE" in r))))
    return righe, info, registro


def campione_revisione(passaggi, righe_nat, seme):
    rng = random.Random(seme)
    out = ["# Test C: campione per la revisione manuale (protocollo v3, §3.4 e §3.5)", "",
           "Per ogni coppia: B determina la risposta e C no? In CONF le due fonti sono alla pari? In LOG la disgiunzione ha "
           "lo stesso ruolo in B e in C? Per RIM-nat: C permette ancora di rispondere? Per DUE-nat: il distrattore è "
           "plausibile, cioè C non si risolve dal solo tipo del valore? Le frasi che cambiano sono in grassetto.", ""]
    n = 0
    for fam in ["RIM", "DUE", "CONF", "LOG"]:
        for p in rng.sample(passaggi, 5):
            n += 1
            F = p["famiglie"][fam]
            b, c = F["B"]["frasi"], F["C"]["frasi"]
            out += [f"## {n}. {fam}, {p['passaggio_id']} ({p['genere']}, {p['tipo_attributo']}, {F['posizione']})", "",
                    f"**Domanda:** {p['domanda']}  ", f"**Risposta in B:** {p['valore_B']}", ""]
            for lab, fr, other in (("B", b, c), ("C", c, b)):
                out += ["**" + lab + ".** " + " ".join(f"**{x}**" if x != y else x for x, y in zip(fr, other)), ""]
    rim = [r for r in righe_nat if r["famiglia"] == "RIM-nat" and r["kind"] == "C"]
    for r in rng.sample(rim, min(30, len(rim))):
        n += 1
        b = next(x for x in righe_nat if x["row_id"] == r["row_id"][:-1] + "B")
        out += [f"## {n}. RIM-nat, {r['sq_id']} ({r['tipo_attributo']})", "", f"**Domanda:** {r['domanda']}  ",
                f"**Risposte di SQuAD:** {r['risposte_B']}", "", f"**B (originale).** {b['contesto']}", "",
                f"**C (frasi tolte: {r['frasi_tolte']}).** {r['contesto']}", ""]
    # DUE-nat (aggiunte in C-sel-4): il distrattore è plausibile, cioè C non si risolve dal solo tipo del valore?
    due = [r for r in righe_nat if r["famiglia"] == "DUE-nat" and r["kind"] == "C"]
    for r in rng.sample(due, min(20, len(due))):
        n += 1
        frase = next((f for f in frasi_di(r["contesto"]) if f" or " in f and r["distrattore"] in f), r["contesto"])
        out += [f"## {n}. DUE-nat, {r['sq_id']} ({r['tipo_attributo']}, classe {r.get('classe_domanda')}, "
                f"distrattore da {r.get('origine_distrattore')})", "", f"**Domanda:** {r['domanda']}  ",
                f"**Risposte di SQuAD:** {r['risposte_B']}  ", f"**Distrattore:** {r['distrattore']}", "",
                f"**Frase di C con «or».** {frase}", "",
                f"**Origine del distrattore:** {r.get('fonte_distrattore', {}).get('domanda', '')}", "",
                f"**B completo.** {next(x['contesto'] for x in righe_nat if x['row_id'] == r['row_id'][:-1] + 'B')}", "",
                f"**C completo.** {r['contesto']}", ""]
    return "\n".join(out)


def main(cfg_path):
    cfg = read_json(cfg_path)
    out = Path(cfg["uscite"])
    out.mkdir(parents=True, exist_ok=True)
    for k, exp in cfg["sha_riserve"].items():
        got = sha_testo(cfg["riserve"][k])
        if got != exp:
            raise RuntimeError(f"riserva {k}: sha256 {got} invece di {exp}")
    ctl = Controlli({k: tuple(v) for k, v in cfg["modelli"].items()}, tuple(cfg["giudice"]))
    rapporto = dict(versione=cfg["versione"], tolleranza_token=cfg["tolleranza"], max_token_sirin=MAX_TOKEN,
                    istruzione=ISTRUZIONE, modelli=cfg["modelli"], giudice=cfg["giudice"], sha_riserve=cfg["sha_riserve"],
                    sha_script=cfg["sha_script"])
    righe = []
    rapporto["tokenizer"] = ctl.descrizione()
    for nome, kw in (("definitivo", dict(quote=cfg["quote"])), ("prova", dict(n_totale=cfg["n_prova"]))):
        ris = read_json(cfg["riserve"][nome])["passaggi"]
        scelti, registro, mancanti = seleziona_sintetico(ris, ctl, cfg["tolleranza"], **kw)
        attesi = sum(cfg["quote"].values()) if nome == "definitivo" else cfg["n_prova"]
        scartati = [(r["passaggio_id"], r["motivi"]) for r in registro if r["esito"] == "escluso"]
        write_json(out / f"registro_candidati_{nome}.json", registro)
        say(f"sintetico {nome}: {len(scelti)} scelti su {attesi}, {len(scartati)} candidati esclusi, quote mancanti {mancanti}")
        varianti = Counter(f"{fam}:B{F['B']['variante']}C{F['C']['variante']}" for p in scelti for fam, F in p["famiglie"].items())
        rapporto[nome] = dict(scelti=len(scelti), attesi=attesi, completo=len(scelti) == attesi and not mancanti,
                              quote_mancanti=mancanti, candidati_valutati=len(registro),
                              esiti_candidati=dict(Counter(r["esito"] for r in registro)),
                              motivi_esclusione=dict(Counter(m.split(":")[0] for r in registro for m in r["motivi"])),
                              scartati=[dict(passaggio_id=a, problemi=b[:5]) for a, b in scartati],
                              strati=dict(Counter(f"{p['tipo_attributo']}/{p.get('schema_posizione')}" for p in scelti)),
                              tipi=dict(Counter(p["tipo_attributo"] for p in scelti)),
                              generi=dict(Counter(p["genere"] for p in scelti)),
                              posizioni={fam: dict(Counter(p["famiglie"][fam]["posizione"] for p in scelti)) for fam in
                                         ["RIM", "DUE", "CONF", "LOG"]},
                              varianti_scelte=dict(varianti),
                              differenza_token_max={k: max(abs(F["differenza_token_C_meno_B"][k]) for p in scelti
                                                           for F in p["famiglie"].values()) for k in cfg["modelli"]} if scelti else {},
                              token_sirin_max={k: max(F[l]["lunghezze"][f"sirin_{k}"] for p in scelti
                                                      for F in p["famiglie"].values() for l in "BC") for k in cfg["modelli"]} if scelti else {})
        write_json(out / f"testC_sintetico_{nome}.json", dict(versione=cfg["versione"], insieme=nome, passaggi=scelti))
        rapporto[nome]["sha256_file"] = sha_testo(out / f"testC_sintetico_{nome}.json")
        rapporto[nome]["sha256_id"] = hashlib.sha256("\n".join(p["passaggio_id"] for p in scelti).encode()).hexdigest()
        if nome == "definitivo":
            sint_def = scelti
        righe += righe_sintetico(scelti, f"sintetico_{nome}")
    righe_nat, info_nat, registro_nat = costruisci_naturale(cfg, ctl)
    write_json(out / "registro_candidati_naturale.json", registro_nat)
    rapporto["naturale"] = info_nat
    righe += righe_nat
    ids = [r["row_id"] for r in righe]
    assert len(ids) == len(set(ids))
    write_json(out / "righe_C.json", righe)
    rapporto["righe"] = dict(Counter(r["insieme"] for r in righe))
    rapporto["sha256_righe_C"] = sha_testo(out / "righe_C.json")
    (out / "campione_revisione.md").write_text(campione_revisione(sint_def, righe_nat, cfg["seme_revisione"]))
    write_json(out / "rapporto_selezione.json", rapporto)
    rapporto["sha256_campione_revisione"] = sha_testo(out / "campione_revisione.md")
    write_json(out / "rapporto_selezione.json", rapporto)
    say("selezione finita:", json.dumps({k: rapporto[k] for k in ("righe", "sha256_righe_C")}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
