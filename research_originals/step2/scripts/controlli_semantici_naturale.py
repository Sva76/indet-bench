"""Filtri prudenti C-nat-7, fissati prima di inferenze sul naturale.

Non dimostrano l'indeterminatezza. Segnalano vie residue verificabili e
richiedono evidenza del ruolo per i distrattori nominali. Nessun ID è escluso
a mano e nessuna risposta dei modelli è letta da questo modulo.
"""
import itertools
import math
import re

VERSIONE = "C-nat-7"
STOP = set("a an the of in on at to for from by with and or is was were are be been what which who whom whose when "
           "where why how did does do many much year years as that this these those it its his her their they he she "
           "after before during than into about other first last main most some any all only one name names kind type "
           "entity thing person people country city town location place called located provide provides provided "
           "according known total number have has had would will can could should there not also".split())
MODIFICATORI = set("other first last main major important common prominent specific early earliest new only largest "
                  "smallest historic historical ancient modern different famous former".split())
DEMONIMI = {"china": {"chinese"}, "france": {"french"}, "germany": {"german", "germans"},
            "scotland": {"scottish", "scots"}, "poland": {"polish"}, "england": {"english"},
            "netherlands": {"dutch"}, "japan": {"japanese"}, "india": {"indian", "indians"},
            "norman": {"normans"}}
REGIONI = {"england": {"england", "english"}, "scotland": {"scotland", "scottish"},
           "holland": {"holland", "netherlands", "dutch"},
           "netherlands": {"holland", "netherlands", "dutch"},
           "france": {"france", "french"}, "germany": {"germany", "german"},
           "china": {"china", "chinese"}, "japan": {"japan", "japanese"},
           "india": {"india", "indian"}, "nepal": {"nepal", "nepali", "nepalese"}}
RAIL = {"train", "trains", "rail", "railway", "railways", "railroad", "railroads", "branchline", "branchlines"}
PICCOLI = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                     "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
PICCOLI.update(dict(thirty=30, forty=40, fifty=50, sixty=60, seventy=70, eighty=80, ninety=90))


def pulisci_nome(testo):
    s = re.sub(r"['’]s\b", "", testo.lower())
    return " ".join(re.findall(r"[a-z0-9]+", s))


def contenuto(parola):
    if parola.endswith("ies") and len(parola) > 5:
        return parola[:-3] + "y"
    if parola.endswith("s") and not parola.endswith(("ss", "us")) and len(parola) > 4:
        return parola[:-1]
    for fine in ("ing", "ed"):
        if parola.endswith(fine) and len(parola) > len(fine) + 3:
            return parola[:-len(fine)]
    return parola


def parole_ruolo(domanda):
    return {contenuto(w) for w in re.findall(r"[a-z]+", domanda.lower()) if w not in STOP and len(w) > 2}


def frase_contiene(testo, forma):
    return bool(forma and re.search(r"(?<![a-z0-9])" + re.escape(forma) + r"(?![a-z0-9])", pulisci_nome(testo)))


def forme_nominali(risposte, contesto):
    forme = set()
    for a in risposte:
        n = pulisci_nome(a)
        if not n:
            continue
        forme.add(n)
        # Possessivi e composti con trattino si leggono come parole separate.
        if len(n.split()) == 1 and len(n) >= 4 and not n.endswith("s"):
            forme.add(n + "s")
            if n.endswith("a"):
                forme.add(n + "n")
        # Per i nomi composti si elimina anche una menzione abbreviata distintiva
        # (Louis Agassiz -> Agassiz); le parole che indicano soltanto il tipo non
        # sono alias sufficienti (River, School, Court...). È un filtro prudente.
        generici = set("the school university college river city town court justice king queen prince princess "
                       "saint doctor sir lady lord admiral general captain hurricane storm war battle "
                       "north south east west new old great grand royal national united company corporation".split())
        parti = n.split()
        if len(parti) > 1:
            forme.update(p for p in parti if len(p) >= 4 and p not in generici)
        forme.update(DEMONIMI.get(n, ()))
        # Apposizioni esplicite come Porifera (sponges), non un dizionario esterno.
        for m in re.finditer(re.escape(a) + r"\s*\(([^)]{1,45})\)", contesto, re.I):
            alias = m.group(1).strip().strip('"\u201c\u201d')
            if re.fullmatch(r"[A-Za-z -]+", alias) and len(alias.split()) <= 3:
                forme.add(pulisci_nome(alias))
    return forme


def domanda_non_univoca(domanda):
    q = domanda.lower()
    if re.search(r"\bone of\b|\bname (?:a|an)\b|\bgive (?:an? )?example\b|\bsome (?:researchers|scientists|historians)\b", q):
        return "domanda con scelta aperta o posizioni di alcuni ricercatori"
    return None


def nome_intero(testo):
    s = testo.strip()
    if not s or re.search(r"['’]s\s*$", s):
        return False
    if re.search(r"[;:!?]|\b(?:and|or)\b", s, re.I):
        return False
    return 1 <= len(s.split()) <= 5 and bool(re.search(r"[A-Za-z]", s))


def classe_precisa(domanda, tipo, risposta=None):
    if tipo in ("anno", "numero"):
        return tipo
    q = domanda.lower()
    if re.search(r"\bwho(?:m|se)?\b", q):
        return "persona"
    if re.search(r"\bwhere\b", q):
        return "luogo"
    m = re.search(r"\b(?:what|which)\s+(?:kind of |type of |sort of |name of (?:the )?)?([a-z ]+)", q)
    if not m:
        return None
    words = m.group(1).split()
    while words and words[0] in MODIFICATORI:
        words.pop(0)
    vaghi = {"is", "was", "are", "were", "did", "does", "do", "entity", "thing", "type", "kind", "name", "names"}
    if not words or words[0] in vaghi:
        # Per un'intestazione generica, il nome della risposta può certificare
        # soltanto un tipo esplicito; altrimenti il candidato resta non verificato.
        if risposta:
            for head in ("tribunal", "committee", "river", "university", "school", "company", "court", "agency"):
                if re.search(r"\b" + head + r"\b", risposta, re.I):
                    return "cosa:" + head
        return None
    return "cosa:" + contenuto(words[0])


def frase_del_valore(ex, valore):
    # Solo evidenza del candidato: delimitazione locale, non il divisore del selettore.
    ctx = ex["context"]
    p = ctx.lower().find(valore.lower())
    if p < 0:
        return ""
    start = max(ctx.rfind(". ", 0, p), ctx.rfind("? ", 0, p), ctx.rfind("! ", 0, p))
    end = re.search(r"[.!?](?:[\"')\]]*)\s+(?=[A-Z])", ctx[p + len(valore):])
    return ctx[start + 2 if start >= 0 else 0:p + len(valore) + end.end() if end else len(ctx)].strip()


def prova_distrattore(ex, other, valore, classe):
    """Evidenza minima, non una certificazione semantica completa."""
    if not nome_intero(valore):
        return False, "nome candidato incompleto"
    if other["title"] != ex["title"]:
        return False, "nome da un altro articolo"
    a = parole_ruolo(ex["question"])
    b = parole_ruolo(other["question"])
    titolo = {contenuto(w) for w in re.findall(r"[a-z]+", ex["title"].lower())}
    comuni = (a & b) - titolo
    if not comuni:
        return False, "ruolo del candidato non corroborato dalla domanda di origine"
    q, qo = ex["question"].lower(), other["question"].lower()
    persona_collettiva = re.search(r"\b(?:muslims|christians|catholics|protestants|mongols|chinese|administrators|"
                                   r"troops|soldiers|people|immigrants|settlers|officials|scientists|researchers)\b", valore, re.I)
    ruolo_specifico = False
    if classe == "persona":
        if persona_collettiva:
            return False, "gruppo collettivo usato come nome di persona"
        scrive = r"\b(?:wrote|write|written|author|writer|novelist|poet|journalist|bestseller)\b"
        if re.search(scrive, q):
            if not re.search(scrive, qo):
                return False, "ruolo di autore non attestato nella domanda di origine"
            ruolo_specifico = True
        if re.search(r"\bfounder\b|\bfounded\b", q) and re.search(r"\b(?:corporation|company|firm|business)\b", q):
            if not (re.search(r"\bfounder\b|\bfounded\b", qo) and
                    re.search(r"\b(?:corporation|company|firm|business)\b", qo)):
                return False, "fondatore di impresa non attestato nella domanda di origine"
            ruolo_specifico = True
        militare = r"\b(?:army|military|attack|campaign|battle|general|commander)\b"
        if re.search(militare, q):
            if not re.search(militare, qo):
                return False, "ruolo militare non attestato nella domanda di origine"
            ruolo_specifico = True
    deboli = {"alumni", "alumnu", "member", "founder", "treaty", "mongol", "school", "university", "student"}
    if not ruolo_specifico and comuni <= deboli:
        return False, "somiglianza generica senza ruolo specifico del candidato"
    fonte = other["question"] + " " + frase_del_valore(other, valore)
    q = ex["question"].lower()
    for regione, aliases in REGIONI.items():
        if re.search(r"\b" + regione + r"\b", q) and not any(re.search(r"\b" + x + r"\b", fonte, re.I) for x in aliases):
            return False, "vincolo geografico della domanda non corroborato"
    return True, ", ".join(sorted(comuni))


def altre_vie_nominali(domanda, frase):
    q = set(re.findall(r"[a-z]+", domanda.lower()))
    f = set(re.findall(r"[a-z]+", frase.lower()))
    if q & RAIL and f & RAIL and re.search(r"\bcompan(?:y|ies)\b|\bservice\b", domanda, re.I):
        return True
    return False


def rischio_discorso(frasi, tolte):
    for i, f in enumerate(frasi):
        if i not in tolte and i > 0 and i - 1 in tolte:
            if (re.match(r"^(?:It|Its|They|Their|He|She|His|Her|These|Those|This|Such)\b", f)
                    or re.match(r"^The\s+[a-z]", f)):
                return "anafora o sintagma definito dopo una frase rimossa"
            if re.match(r"^(?:In (?:the )?(?:following|subsequent|next)\b|Similarly\b|Later\b|Afterwards\b|"
                        r"(?:A|One) (?:mere )?[^.!?]{0,35}\blater\b)", f):
                return "riferimento temporale dopo una frase rimossa"
    return None


def elenco_residuo(domanda, testo):
    if not re.search(r"\bhow many\b|\bnumber of\b", domanda, re.I):
        return False
    if re.search(r"(?:^|[.!?]\s+)(?:These|Those) (?:are|include)\b[^.!?]+(?:,|\band\b)", testo):
        return True
    # Il numero può essere ricostruito anche da elenchi con due punti e punti
    # e virgola, senza la formula iniziale 'These are'. Non si interpreta la
    # semantica di ogni elemento: si esclude prudentemente il candidato.
    return bool(re.search(r":\s*[^.!?]*(?:;|,\s*[A-Za-z]|\band\b)", testo))


def sottoinsieme_numerico(domanda, frase, risposta):
    """Evita che una disgiunzione contraddica il totale di cui è una parte.

    Si scarta la struttura, senza cambiare la distanza numerica già fissata.
    'six of the seven lines' e 'How many of the six total packages' richiedono
    vincoli di coerenza che il solo ordine di grandezza non certifica.
    """
    if re.search(r"\bhow many of\b", domanda, re.I):
        return True
    return bool(re.search(re.escape(risposta) + r"\s+(?:out )?of\s+(?:the\s+)?", frase, re.I))


def ancoraggio_domanda(domanda, frase):
    # Una data associata a una carica non certifica una data di nascita.
    # Anche una sola data tra parentesi può indicare la durata della carica.
    # Per le domande sulla nascita si richiede l'evento esplicito nella frase.
    if re.search(r"\bborn\b|\bbirth\b", domanda, re.I) and not re.search(r"\bborn\b|\bbirth\b", frase, re.I):
        return "evento di nascita non esplicito nella frase della risposta"
    return None


def vincoli_quantitativi(domanda, contesto, tipo):
    if tipo == "numero" and re.search(r"\b(?:average|averaged|mean)\b", contesto, re.I):
        if re.search(r"\b(?:maximum|minimum|at most|at least|as high as|as low as|up to|no more than)\b", contesto, re.I):
            return "media e vincoli estremi presenti nello stesso contesto"
    if tipo == "anno" and re.search(r"\b(?:after|before|since|until|from|between)\s+(?:the (?:year|years) )?\d{4}\b", contesto, re.I):
        return "vincolo cronologico residuo da verificare semanticamente"
    return None


def numeri(testo):
    out = []
    pattern = r"(?<![\w.])(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(?!\w)"
    for m in re.finditer(pattern, testo):
        out.append(float(m.group().replace(",", "")))
    for w in re.findall(r"\b[a-z]+\b", testo.lower()):
        if w in PICCOLI:
            out.append(float(PICCOLI[w]))
    return out


def aritmetica_residua(domanda, testo_senza_risposta, valore):
    """Esclusione prudente per somme/prodotti/differenze residui, con valori piccoli o totali espliciti."""
    if valore is None or not math.isfinite(valore):
        return None
    if not re.search(r"\bhow many\b|\bhow much\b|\bpopulation\b|\btotal\b|\boverall\b|\bnumber\b", domanda, re.I):
        return None
    vals = [v for v in numeri(testo_senza_risposta) if v >= 0]
    if len(vals) > 18:
        return "troppe quantità residue per escludere calcoli"
    eq = lambda x: math.isclose(x, valore, rel_tol=1e-9, abs_tol=1e-9)
    for n in range(2, min(6, len(vals)) + 1):
        for xs in itertools.combinations(vals, n):
            if eq(sum(xs)):
                return "somma di quantità residue"
    for a, b in itertools.combinations(vals, 2):
        if eq(abs(a - b)) or (a > 1 and b > 1 and eq(a * b)):
            return "differenza o prodotto di quantità residue"
    return None
