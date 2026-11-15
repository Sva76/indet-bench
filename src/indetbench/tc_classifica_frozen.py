# Test C: classificazione delle risposte (protocollo v3, §4). Solo libreria standard: gira nel Python di Colab.
# Le regole sono scritte prima dei dati; si possono correggere solo sui 10 passaggi della prova (§8), poi si fissano.
#
# Ordine delle regole (§4): prima l'astensione, poi le alternative e le attribuzioni (con «entrambi affermati»), poi la
# qualificazione, poi gli altri casi. Una risposta come «1821 or maybe 1823» è quindi «alternative».
import re
import string

VERSIONE_REGOLE = "C-classifica-2"

CATEGORIE = ("corretta", "errata", "astensione", "alternative", "attribuite", "entrambi affermati", "qualificata",
             "un valore del contesto", "valore assente dal contesto", "altro")
SUPPORTATE_C = ("alternative", "attribuite")
NON_SUPPORTATE_C = ("entrambi affermati", "un valore del contesto", "valore assente dal contesto")
SUPPORTATE_B = ("corretta",)
NON_SUPPORTATE_B = ("errata", "valore assente dal contesto")
ESCLUSE = ("astensione", "qualificata", "altro")

# formule di non risposta (elenco fisso; si confrontano sul testo in minuscolo)
ASTENSIONE = re.compile(
    r"\bunknown\b|\bnot (?:explicitly )?(?:mentioned|stated|specified|provided|given|named|known|clear|determinable|"
    r"indicated|said)\b|\bno (?:information|answer|mention)\b|\b(?:does|do|did)(?: not|n't) (?:say|mention|specify|"
    r"state|provide|indicate|tell|give)\b|\bcannot be (?:determined|known|answered)\b|\bcan't be (?:determined|known)\b|"
    r"\b(?:cannot|can't|unable to) (?:determine|answer|tell|know)\b|\bunclear\b|\bi (?:do not|don't) know\b|"
    r"\bnot enough information\b|\binsufficient information\b|\bunanswerable\b|\bimpossible to (?:determine|know|tell)\b")
# riserve esplicite (elenco fisso)
MARCATORI = re.compile(r"\b(?:maybe|probably|possibly|perhaps|likely|presumably|apparently|i think|i believe|it seems|"
                       r"seems|appears|might|may|could)\b")
CONNETTIVO_O = re.compile(r"\bor\b|\beither\b|\bwhether\b")
# Correzione sui soli passaggi della prova: fonte generica, senza assegnazione dei due valori.
ATTRIBUZIONE_GENERICA = re.compile(
    r"\baccording to (?:the )?(?:different|separate|two|both) "
    r"(?:registers|archives|sources|records|chronicles)\b")

NUMERI_PAROLE = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
    "eighteen nineteen twenty".split())}
NUMERI_PAROLE.update({"thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90})
TIPO_CONTORNO = ["anno", "anno", "numero", "numero", "luogo", "luogo", "persona", "persona", None, None]
PAROLE_FUNZIONE = set("the a an of in on at to for from by with and or is was were are be been it its this that these "
                      "those according answer passage text question saint doctor admiral lady city town company ship "
                      "festival archive register chronicle records river district fleet valley province year number "
                      "unknown yes no i".split())


def normalizza(s):
    """Normalizzazione SQuAD: minuscole, senza punteggiatura, senza articoli, spazi singoli."""
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def pulisci(risposta):
    """Toglie markdown, virgolette e spazi ai bordi; tiene il testo della risposta così com'è."""
    return re.sub(r"[*_`#]+", "", risposta or "").strip().strip("\"'“”").strip()


def contiene_parola(testo_min, parola_min):
    return re.search(r"(?<![a-z0-9])" + re.escape(parola_min) + r"(?![a-z0-9])", testo_min) is not None


# --------------------------------------------------------------------------- valori nel testo
def valore_canonico(v, tipo):
    if tipo == "anno":
        return str(v)
    if tipo == "numero":
        return NUMERI_PAROLE.get(str(v).lower(), int(v) if str(v).isdigit() else str(v).lower())
    return str(v).lower()


def valori_nella_risposta(testo, tipo, nomi_noti):
    """Valori del tipo trovati nella risposta, in forma canonica. Per luoghi e persone: i nomi noti del passaggio trovati
    (un nome di più parole vale se compare una sua parola di almeno 4 lettere), più gli eventuali nomi sconosciuti."""
    t = testo.lower()
    if tipo == "anno":
        return {m for m in re.findall(r"(?<![0-9])(1[0-9]{3}|20[0-9]{2})(?![0-9])", t)}, set()
    if tipo == "numero":
        trovati = {int(m) for m in re.findall(r"(?<![0-9.,])([0-9]{1,6})(?![0-9])", t.replace(",", ""))}
        trovati |= {NUMERI_PAROLE[w] for w in re.findall(r"[a-z]+", t) if w in NUMERI_PAROLE}
        return trovati, set()
    trovati = set()
    for nome in nomi_noti:
        parti = [p for p in nome.lower().split() if len(p) >= 4] or [nome.lower()]
        if contiene_parola(t, nome.lower()) or any(contiene_parola(t, p) for p in parti):
            trovati.add(nome.lower())
    return trovati, set()


def nomi_sconosciuti(testo, esclusi):
    """Parole con la maiuscola nella risposta che non sono nomi del passaggio né parole di servizio."""
    out = set()
    for w in re.findall(r"\b[A-Z][a-zA-Z\-]+\b", testo):
        wl = w.lower()
        if wl in PAROLE_FUNZIONE or any(contiene_parola(e, wl) for e in esclusi):
            continue
        out.add(wl)
    return out


# --------------------------------------------------------------------------- insieme sintetico
def info_sintetico(passaggio, famiglia, lato):
    """Dalla rappresentazione formale di una versione: valori del tipo nel passaggio (bersaglio e contorno), nomi per
    l'attribuzione (fonti in CONF, gruppi in LOG) e tutti i nomi propri del passaggio."""
    tipo = passaggio["tipo_attributo"]
    rep = passaggio["famiglie"][famiglia][lato]["rep"]
    valori, tutti_nomi = set(), set()
    for f in rep:
        for k in ("v", "v1", "v2"):
            if k in f:
                valori.add(f[k])
        if f.get("tipo") == "contorno" and f.get("val") is not None:
            if TIPO_CONTORNO[f["i"]] == tipo:
                valori.add(f["val"])
            if TIPO_CONTORNO[f["i"]] in ("luogo", "persona"):
                tutti_nomi.add(str(f["val"]))
        for k in ("F", "G", "G1", "G2", "R"):
            if k in f:
                tutti_nomi.add(str(f[k]))
    nomi = passaggio["nomi"]
    attribuzione = nomi["fonti"] if famiglia == "CONF" else (nomi["gruppi"] if famiglia == "LOG" else [])
    tutti_nomi |= {passaggio["entita"], nomi.get("regione", "")} | set(nomi["fonti"]) | set(nomi["gruppi"])
    tutti_nomi |= {str(v) for v in valori if tipo in ("luogo", "persona")}
    return dict(tipo=tipo, famiglia=famiglia, lato=lato, v1=passaggio["valore_B"], v2=passaggio["valore_alternativo"],
                valori_contesto=sorted(str(v) for v in valori), attribuzione=list(attribuzione),
                nomi_passaggio=sorted(n for n in tutti_nomi if n))


def classifica_sintetico(risposta, info):
    """Categoria di §4 per una risposta su una versione sintetica. Restituisce (categoria, dettagli)."""
    testo = pulisci(risposta)
    t = testo.lower()
    tipo, fam, lato = info["tipo"], info["famiglia"], info["lato"]
    v1, v2 = valore_canonico(info["v1"], tipo), valore_canonico(info["v2"], tipo)
    ctx = {valore_canonico(v, tipo) for v in info["valori_contesto"]}
    nomi_tipo = [str(v) for v in info["valori_contesto"]] if tipo in ("luogo", "persona") else []
    trovati, _ = valori_nella_risposta(testo, tipo, nomi_tipo)
    det = dict(valori=sorted(map(str, trovati)))
    if not testo:
        return "altro", dict(det, motivo="risposta vuota")
    if ASTENSIONE.search(t):
        return "astensione", det
    if lato == "C" and fam != "RIM" and v1 in trovati and v2 in trovati:
        attr = info["attribuzione"]
        if fam in ("CONF", "LOG") and attr and all(contiene_parola(t, a.lower()) for a in attr):
            return "attribuite", det
        if CONNETTIVO_O.search(t):
            return "alternative", det
        if fam in ("CONF", "LOG") and ATTRIBUZIONE_GENERICA.search(t):
            return "altro", dict(det, motivo="attribuzione generica: assegnazione dei valori non esplicita")
        return "entrambi affermati", det
    if len(trovati) == 1 and MARCATORI.search(t):
        return "qualificata", det
    if len(trovati) == 1:
        (v,) = trovati
        if lato == "B":
            if v == v1:
                return "corretta", det
            return ("errata" if v in ctx else "valore assente dal contesto"), det
        return ("un valore del contesto" if v in ctx else "valore assente dal contesto"), det
    if len(trovati) > 1:
        return "altro", dict(det, motivo="più valori, non le due alternative")
    # nessun valore riconosciuto: un anno o un numero non c'è; per luoghi e persone si guardano i nomi sconosciuti
    if tipo in ("luogo", "persona"):
        ignoti = nomi_sconosciuti(testo, [n.lower() for n in info["nomi_passaggio"]])
        if ignoti and len(testo.split()) <= 8:
            if MARCATORI.search(t):
                return "qualificata", dict(det, nomi_sconosciuti=sorted(ignoti))
            return ("valore assente dal contesto"), dict(det, nomi_sconosciuti=sorted(ignoti))
    return "altro", dict(det, motivo="nessun valore del tipo riconosciuto")


# --------------------------------------------------------------------------- insieme naturale (descrittivo)
def classifica_naturale(risposta, riga):
    """Categorie di §4 per l'insieme naturale (descrittivo). B: corretta se una risposta di SQuAD e la risposta del
    modello si contengono dopo la normalizzazione. DUE-nat C: alternative o entrambi affermati se compaiono la risposta e
    il distrattore. RIM-nat C: ogni risposta non astenuta è non supportata; si segna se coincide con la risposta tolta
    (possibile memoria)."""
    testo = pulisci(risposta)
    t, n = testo.lower(), normalizza(testo)
    det = {}
    if not n:
        return "altro", dict(motivo="risposta vuota")
    if ASTENSIONE.search(t):
        return "astensione", det
    refs = [normalizza(a) for a in riga["risposte_B"] if normalizza(a)]
    giusta = any(contiene_parola(n, r) or contiene_parola(r, n) for r in refs)
    nel_contesto = contiene_parola(normalizza(riga["contesto"]), n)
    if riga["famiglia"] == "DUE-nat" and riga["kind"] == "C":
        d = normalizza(riga["distrattore"])
        con_d = contiene_parola(n, d) or contiene_parola(d, n)
        if giusta and con_d and len(n.split()) > max(len(d.split()), 1):
            return ("alternative" if CONNETTIVO_O.search(t) else "entrambi affermati"), det
        if MARCATORI.search(t) and (giusta or con_d):
            return "qualificata", det
        if giusta or con_d or nel_contesto:
            return "un valore del contesto", dict(det, distrattore=con_d)
        return "valore assente dal contesto", det
    if riga["kind"] == "B":
        if MARCATORI.search(t):
            return "qualificata", det
        if giusta:
            return "corretta", det
        return ("errata" if nel_contesto else "valore assente dal contesto"), det
    # RIM-nat, C
    if MARCATORI.search(t):
        return "qualificata", dict(det, risposta_tolta=giusta)
    if nel_contesto and not giusta:
        return "un valore del contesto", det
    return "valore assente dal contesto", dict(det, risposta_tolta=giusta)
