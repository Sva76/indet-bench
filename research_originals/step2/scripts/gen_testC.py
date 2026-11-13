# Test C, generatore dei passaggi sintetici (protocollo v3, §3.1–§3.3).
#
# Ogni passaggio nasce da una rappresentazione formale (entità, attributo bersaglio, fonti, regole, disgiunzioni).
# Da questa si scrive il testo con template fissi. Poi:
#   1. un risolutore calcola i valori compatibili con la rappresentazione;
#   2. un analizzatore inverso rilegge il testo, ricostruisce la rappresentazione e rilancia il risolutore;
#   3. si controllano le occorrenze dei valori, le «or», i marcatori di riserva, le parole vietate, i nomi e il bilanciamento.
# Un passaggio che non supera un controllo esce dalla riserva (con il motivo registrato). La riserva è ordinata e
# riproducibile: la selezione finale (prime 50 per tipo di attributo che superano anche i controlli sui tokenizer,
# fatti su Colab) non dipende da nessuna risposta dei modelli.
#
# Uso: python -I gen_testC.py <cartella_di_uscita>
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict

VERSIONE = "C-gen-4"
SEME_DEFINITIVO = 20261111
SEME_PROVA = 20261112
N_RISERVA = 400            # riserva ordinata per i 200 definitivi (100 per tipo, circa 33 per tipo e schema di posizione)
N_RISERVA_PROVA = 16       # riserva per i 10 della prova
FAMIGLIE = ["RIM", "DUE", "CONF", "LOG"]
TIPI = ["anno", "numero", "luogo", "persona"]
GENERI = ["citta", "azienda", "nave", "festival"]
POSIZIONI = ["inizio", "meta", "fine"]
N_FRASI = 8
PAROLE_MIN, PAROLE_MAX = 120, 180
ANNI_DOPO = (3, 70)         # anni di contorno fra 3 e 70 anni dopo l'anno di riferimento (C-gen-4)
ANNO_MAX_CONTORNO = 1995

NUMERI = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
          10: "ten", 11: "eleven", 12: "twelve"}
PAROLE_NUMERO = set(NUMERI.values()) | {"one", "zero", "thirteen", "fourteen", "fifteen", "twenty"}
MARCATORI_RISERVA = ["maybe", "probably", "possibly", "perhaps", "likely", "unlikely", "uncertain", "unknown",
                     "unclear", "seems", "appears to", "may", "might", "could", "believed", "said to", "reportedly",
                     "allegedly", "estimated", "about", "around", "roughly", "approximately", "not known", "no record"]

# --------------------------------------------------------------------------- lessico per genere
# soggetto del passaggio, gruppo per LOG, fonte per CONF, predicati dell'attributo bersaglio (un solo valore per
# definizione), domanda, frase neutra di RIM, frase con «or» irrilevante (DUE), frasi di contorno.
GEN = {
    "citta": dict(
        soggetto="{N}", nome_tipo="town",
        intro="{N} is a small and quiet town in the green hills of the {R} province, far from the main roads and the large cities of the region.",
        gruppo_appartenenza="{S} lies on the {G1} river or on the {G2} river.",
        gruppo_regola="Every town on the {G} river {P}.",
        fonte="According to the {F} archive, {s} {P}.",
        pred={"anno": "was founded in {v}", "numero": "has {v} bridges",
              "luogo": "keeps its original charter in {v}", "persona": "has Saint {v} as its only patron saint"},
        pads={"anno": ["was founded in the year {v}", "was founded in the course of the year {v}"],
              "numero": ["has a total of {v} bridges"],
              "luogo": ["keeps its original charter in the city of {v}", "keeps the original charter of the town in the city of {v}"],
              "persona": ["has Saint {v} as the only patron saint of the town", "has Saint {v} as the one and only patron saint of the town"]},
        domanda={"anno": "In what year was {N} founded?", "numero": "How many bridges does {N} have?",
                 "luogo": "In which city is the original charter of {N} kept?", "persona": "Who is the only patron saint of {N}?"},
        vietate={"anno": ["found"], "numero": ["bridge"], "luogo": ["charter"], "persona": ["saint", "patron"]},
        neutre=["{S} appears in an old travel guide.",
                "{S} was described in an old travel guide.",
                "{S} is described in some detail in an old travel guide.",
                "{S} was described at length in an old travel guide for visitors.",
                "{S} is described in some detail in an old travel guide for visitors from abroad.",
                "{S} was described at length and in some detail in an old travel guide for visitors from abroad."],
        or_frase=("Visitors usually reach {S} by boat or by train.", "Visitors usually reach {S} by boat and by train."),
        contorno=[
            ("anno", "A stone school with a red roof and a small garden for the pupils was built near the eastern gate of {S} in {y}."),
            ("anno", "The old covered market in the centre of {S}, where farmers still sell their vegetables, was rebuilt after a fire in {y}."),
            ("numero", "The main square of {S} has {n} public fountains, a long row of chestnut trees and a few wooden benches in the shade."),
            ("numero", "Each spring the people of {S} plant {n} new gardens along the edge of the old wall that once protected the town."),
            ("luogo", "Merchants from {L} often travel to {S} in the autumn to buy wool, cheese, honey and dried fruit from the local farms."),
            ("luogo", "The heavy bells of the clock tower in {S} were cast in a family workshop in {L} and carried up the hill on carts."),
            ("persona", "The local choir of {S}, which sings in the church every Sunday morning, is led by a retired teacher called {Q}."),
            ("persona", "A painter named {Q} once lived in a narrow house beside the river in {S} and painted the hills in every season."),
            ("libera", "Many families in {S} keep small orchards behind their houses and sell apples, pears and plums at the weekly market in autumn."),
            ("libera", "The streets of {S} are narrow and steep, and most of them are paved with grey stone that becomes slippery in winter."),
        ]),
    "azienda": dict(
        soggetto="{N} Works", nome_tipo="company",
        intro="{N} Works is a family company that makes hand tools, small machines and spare parts for farmers in the {R} province.",
        gruppo_appartenenza="{S} is registered in the {G1} district or in the {G2} district.",
        gruppo_regola="Every company registered in the {G} district {P}.",
        fonte="According to the {F} registry, {s} {P}.",
        pred={"anno": "was founded in {v}", "numero": "has {v} offices",
              "luogo": "has its only warehouse in {v}", "persona": "has Doctor {v} as its sole auditor"},
        pads={"anno": ["was founded in the year {v}", "was founded in the course of the year {v}"],
              "numero": ["has a total of {v} offices"],
              "luogo": ["has its only warehouse in the city of {v}", "has the only warehouse of the company in the city of {v}"],
              "persona": ["has Doctor {v} as the sole auditor of the company", "has Doctor {v} as the one and only auditor of the company"]},
        domanda={"anno": "In what year was {N} Works founded?", "numero": "How many offices does {N} Works have?",
                 "luogo": "In which city is the only warehouse of {N} Works?", "persona": "Who is the sole auditor of {N} Works?"},
        vietate={"anno": ["found"], "numero": ["office"], "luogo": ["warehouse"], "persona": ["audit", "doctor"]},
        neutre=["{S} appears in an old trade journal.",
                "{S} was mentioned in an old trade journal.",
                "{S} is mentioned in some detail in an old trade journal.",
                "{S} was mentioned at length in an old trade journal for merchants.",
                "{S} is mentioned in some detail in an old trade journal for merchants from abroad.",
                "{S} was mentioned at length and in some detail in an old trade journal for merchants from abroad."],
        or_frase=("Clients can contact {S} by letter or by telephone.", "Clients can contact {S} by letter and by telephone."),
        contorno=[
            ("anno", "A second workshop with large windows and a high wooden ceiling was opened behind the main building of {S} in {y}."),
            ("anno", "The engineers of {S} won a prize for a new kind of light hand drill at a crowded trade fair in {y}."),
            ("numero", "The main workshop of {S} has {n} long benches where the workers sharpen the blades and polish the metal parts by hand."),
            ("numero", "Every year {S} trains {n} young apprentices who come from the nearby villages and learn the trade over several long winters."),
            ("luogo", "Most of the steel used by {S} for its blades and gears is bought from a large steelworks in {L}."),
            ("luogo", "The strong wooden boxes in which {S} packs its tools are made by a group of carpenters in {L}."),
            ("persona", "In every meeting with the managers, the workers of {S} are represented by a calm and patient woman called {Q}."),
            ("persona", "The first printed catalogue of {S}, with pictures of every tool, was drawn by hand by an engraver named {Q}."),
            ("libera", "The tools made by {S} are known in the whole region for their smooth wooden handles and their simple, practical design."),
            ("libera", "The workers of {S} take a long break at noon and often eat bread and soup together in the sunny yard behind the workshop."),
        ]),
    "nave": dict(
        soggetto="The {N}", nome_tipo="ship",
        intro="The {N} is a wooden sailing ship that carries passengers, letters and goods along the long rocky coast of the {R} province.",
        gruppo_appartenenza="{S} belongs to the {G1} fleet or to the {G2} fleet.",
        gruppo_regola="Every ship of the {G} fleet {P}.",
        fonte="According to the {F} register, {s} {P}.",
        pred={"anno": "was launched in {v}", "numero": "carries {v} lifeboats",
              "luogo": "has {v} as its only home port", "persona": "has Admiral {v} as its sole commander"},
        pads={"anno": ["was launched in the year {v}", "was launched in the course of the year {v}"],
              "numero": ["carries a total of {v} lifeboats"],
              "luogo": ["has the city of {v} as its only home port", "has the city of {v} as the only home port of the ship"],
              "persona": ["has Admiral {v} as the sole commander of the ship", "has Admiral {v} as the one and only commander of the ship"]},
        domanda={"anno": "In what year was the {N} launched?", "numero": "How many lifeboats does the {N} carry?",
                 "luogo": "What is the only home port of the {N}?", "persona": "Who is the sole commander of the {N}?"},
        vietate={"anno": ["launch"], "numero": ["lifeboat"], "luogo": ["home port"], "persona": ["admiral", "command"]},
        neutre=["{S} appears in an old picture.",
                "{S} was painted by a sailor in an old picture.",
                "{S} is painted in some detail by a sailor in an old picture.",
                "{S} was painted by a young sailor in an old picture for a small museum.",
                "{S} is painted in some detail by a young sailor in an old picture for a small museum.",
                "{S} was painted with great care and in some detail by a young sailor in an old picture for a small museum."],
        or_frase=("Passengers can board {s} at the bow or at the stern.", "Passengers can board {s} at the bow and at the stern."),
        contorno=[
            ("anno", "The main mast of {s} was replaced with a taller and stronger one after a violent winter storm in {y}."),
            ("anno", "A new wooden figure of a sea bird with open wings was carved and painted for the front of {s} in {y}."),
            ("numero", "The lower deck of {s} has {n} small cabins with round windows, narrow beds and a little shelf for books."),
            ("numero", "On a normal voyage in good weather {s} stops in {n} harbours before it turns back to the north again."),
            ("luogo", "The large white sails of {s} were sewn from strong cloth by a group of skilled women in {L}."),
            ("luogo", "Every summer {s} carries heavy barrels of oil, salt and wine to the busy market of {L}."),
            ("persona", "The cook on board {s} is a cheerful old man called {Q}, who makes fish soup for the whole crew."),
            ("persona", "A young musician named {Q} often plays the fiddle on the deck of {s} when the sea is calm in the evening."),
            ("libera", "The deck of {s} is cleaned every morning, and the ropes and sails are checked carefully before each departure."),
            ("libera", "Children who travel on {s} like to watch the dolphins that follow the ship near the rocky coast in the morning."),
        ]),
    "festival": dict(
        soggetto="The {N} Festival", nome_tipo="festival",
        intro="The {N} Festival is a popular music festival with singers, bands and dancers that takes place every summer in the {R} province.",
        gruppo_appartenenza="{S} is held in the {G1} valley or in the {G2} valley.",
        gruppo_regola="Every festival held in the {G} valley {P}.",
        fonte="According to the {F} chronicle, {s} {P}.",
        pred={"anno": "was first held in {v}", "numero": "lasts {v} days",
              "luogo": "has all its prizes made in {v}", "persona": "has Lady {v} as its sole patron"},
        pads={"anno": ["was first held in the year {v}", "was first held in the course of the year {v}"],
              "numero": ["lasts a total of {v} days"],
              "luogo": ["has all its prizes made in the city of {v}", "has all the prizes of the festival made in the city of {v}"],
              "persona": ["has Lady {v} as the sole patron of the festival", "has Lady {v} as the one and only patron of the festival"]},
        domanda={"anno": "In what year was the {N} Festival first held?", "numero": "How many days does the {N} Festival last?",
                 "luogo": "In which city are all the prizes of the {N} Festival made?", "persona": "Who is the sole patron of the {N} Festival?"},
        vietate={"anno": ["first held"], "numero": ["day", "last"], "luogo": ["prize"], "persona": ["patron", "lady"]},
        neutre=["{S} appears in an old music magazine.",
                "{S} was praised in an old music magazine.",
                "{S} is praised in some detail in an old music magazine.",
                "{S} was praised at length in an old music magazine for young readers.",
                "{S} is praised in some detail in an old music magazine for young readers from abroad.",
                "{S} was praised at length and in some detail in an old music magazine for young readers from abroad."],
        or_frase=("Guests can buy tickets for {s} at the gate or at the town hall.",
                  "Guests can buy tickets for {s} at the gate and at the town hall."),
        contorno=[
            ("anno", "A large wooden stage with a striped roof against the rain was added to the main field of {s} in {y}."),
            ("anno", "The poster of {s}, with a drawing of a violin and a river, was printed in bright colours in {y}."),
            ("numero", "The main field of {s} has {n} tents where local cooks sell soup, bread, cheese and cold drinks to the visitors."),
            ("numero", "Each evening of {s} ends with {n} short songs played by the local brass band in front of the old church."),
            ("luogo", "Many of the young musicians who play at {s} come from {L} and travel to the province by bus."),
            ("luogo", "The colourful paper lanterns that hang above the paths of {s} are made by hand in {L}."),
            ("persona", "The tickets for {s} are sold from a small wooden kiosk by a friendly young man called {Q}."),
            ("persona", "The opening song of {s}, which everybody in the audience knows by heart, was written by a singer named {Q}."),
            ("libera", "During {s} the paths between the tents are lit by lanterns, and children dance on the grass until late at night."),
            ("libera", "The audience of {s} sits on blankets on the grass, listens to the music and brings food and drinks from home."),
        ]),
}
for g in GEN.values():
    g["soggetto_minuscolo"] = g["soggetto"][0].lower() + g["soggetto"][1:] if g["soggetto"].startswith("The ") else g["soggetto"]

# --------------------------------------------------------------------------- nomi inventati
SILLABE_A = ["lor", "ves", "tal", "mer", "dar", "kel", "sor", "bren", "hal", "vor", "nel", "tor", "gal", "fen", "mar",
             "ost", "rel", "sel", "brav", "cor", "dun", "eld", "fal", "grim", "hev", "jor", "kal", "lun", "mor", "nar",
             "pel", "quen", "ral", "sten", "tov", "ulm", "vel", "wen", "yar", "zor"]
SILLABE_B = ["a", "e", "i", "o", "u", "ae", "ei", "ou"]
SILLABE_C = ["ne", "th", "rin", "mar", "dor", "vik", "len", "wyn", "sk", "ra", "mo", "nd", "ric", "tas", "ven", "ro",
             "lis", "ker", "gan", "dell", "mir", "sar", "tel", "bor"]


def real_names():
    import geonamescache
    from english_words import get_english_words_set
    from faker.providers.person.de_DE import Provider as Pde
    from faker.providers.person.en_US import Provider as Pen
    from faker.providers.person.es_ES import Provider as Pes
    from faker.providers.person.fr_FR import Provider as Pfr
    from faker.providers.person.it_IT import Provider as Pit
    gc = geonamescache.GeonamesCache()
    s = set(get_english_words_set(["web2", "gcide"], lower=True))
    for c in gc.get_cities().values():
        s.add(c["name"].lower())
        for a in (c.get("alternatenames") or []):
            s.add(a.lower())
    s |= {c["name"].lower() for c in gc.get_countries().values()}
    s |= {c["name"].lower() for c in gc.get_us_states().values()}
    for P in (Pen, Pit, Pde, Pfr, Pes):
        for attr in ("first_names", "last_names", "first_names_male", "first_names_female"):
            v = getattr(P, attr, None)
            if v:
                s |= {x.lower() for x in (v.keys() if isinstance(v, dict) else v)}
    return s


class Nomi:
    def __init__(self, rng, reali, vietati=()):
        self.rng, self.reali, self.usati = rng, reali, set(vietati)
        self.scartati_reali = 0

    def nuovo(self, n_sillabe=None):
        while True:
            k = n_sillabe or self.rng.choice([2, 3])
            parts = [self.rng.choice(SILLABE_A)] + [self.rng.choice(SILLABE_B) + self.rng.choice(SILLABE_C)
                                                   for _ in range(k - 1)]
            w = "".join(parts).capitalize()
            if not (5 <= len(w) <= 10) or w.lower() in self.usati or re.search(r"(.)\1\1", w):
                continue
            if w.lower() in self.reali or w.lower() in {"or", "and"}:
                self.scartati_reali += 1
                continue
            self.usati.add(w.lower())
            return w


# --------------------------------------------------------------------------- valori
def due_valori(rng, tipo, nomi, gen):
    if tipo == "anno":
        a = rng.randint(1720, 1930)
        b = a + rng.choice([-1, 1]) * rng.randint(2, 9)
        return str(a), str(b)
    if tipo == "numero":
        a = rng.randint(4, 10)
        b = a + rng.choice([-1, 1]) * rng.randint(1, 2)
        return NUMERI[a], NUMERI[b]
    n = rng.choice([2, 3])
    if tipo == "luogo":
        return nomi.nuovo(n), nomi.nuovo(n)
    return nomi.nuovo(n), nomi.nuovo(n)              # persona: un solo nome, dopo il titolo del genere


TITOLO = {"citta": "Saint", "azienda": "Doctor", "nave": "Admiral", "festival": "Lady"}


def PREF_PERSONA(gen, tipo):
    # nella disgiunzione il titolo si ripete davanti al secondo nome («Saint Orrin or Saint Vell»)
    return TITOLO[gen] + " " if tipo == "persona" else ""


def alias(tipo, genere, v):
    a = {v}
    if tipo == "numero":
        a.add(str([k for k, w in NUMERI.items() if w == v][0]))
    if tipo == "persona":
        a.add(f"{TITOLO[genere]} {v}")
        if genere == "citta":
            a |= {f"St. {v}", f"St {v}"}
    return sorted(a)


# --------------------------------------------------------------------------- rappresentazione formale
# Una frase è un dict {"tipo": ..., campi}. Tipi:
#   intro(R); fatto(v); fatto_pad(v); fatto_o(v1, v2); fonte(F, v); regola(G, v); appartenenza(G1, G2);
#   neutra(k); o_frase(); e_frase(); contorno(i, valore)
def frase_testo(gen, ent, tipo_attr, f):
    g = GEN[gen]
    S = g["soggetto"].format(N=ent)
    s = g["soggetto_minuscolo"].format(N=ent)
    P = lambda v, pad=None: (g["pred"][tipo_attr] if pad is None else g["pads"][tipo_attr][pad]).format(v=v)
    t = f["tipo"]
    if t == "intro":
        return g["intro"].format(N=ent, R=f["R"])
    if t == "fatto":
        return f"{S} {P(f['v'])}."
    if t == "fatto_pad":
        return f"{S} {P(f['v'], f['p'])}."
    if t == "fatto_o":
        return f"{S} {P(f['v1'] + ' or ' + PREF_PERSONA(gen, tipo_attr) + f['v2'])}."
    if t == "fonte":
        return g["fonte"].format(F=f["F"], s=s, P=P(f["v"]))
    if t == "regola":
        return g["gruppo_regola"].format(G=f["G"], P=P(f["v"]))
    if t == "appartenenza":
        return g["gruppo_appartenenza"].format(S=S, G1=f["G1"], G2=f["G2"])
    if t == "neutra":
        return g["neutre"][f["k"]].format(S=S)
    if t == "o_frase":
        return g["or_frase"][0].format(S=S, s=s)
    if t == "e_frase":
        return g["or_frase"][1].format(S=S, s=s)
    if t == "contorno":
        kind, tpl = g["contorno"][f["i"]]
        return tpl.format(S=S, s=s, y=f.get("val"), n=f.get("val"), L=f.get("val"), Q=f.get("val"))
    raise ValueError(t)


def risolvi(rep):
    """Valori compatibili con la rappresentazione per l'attributo bersaglio.

    Restituisce un insieme ordinato di valori, oppure "LIBERO" se il passaggio non vincola il valore.
    Fatti diretti e disgiunzioni danno i loro valori. Fonti di pari rango senza priorità: ogni valore dichiarato da
    una fonte è possibile. Regole di gruppo e appartenenza disgiuntiva: il valore della regola di ciascun gruppo
    possibile (se un gruppo possibile non ha regola, il valore è libero)."""
    meccanismi = []
    vals = set()
    dirette = [f for f in rep if f["tipo"] in ("fatto", "fatto_pad")]
    if dirette:
        meccanismi.append("fatto")
        vals |= {f["v"] for f in dirette}
    for f in rep:
        if f["tipo"] == "fatto_o":
            meccanismi.append("disgiunzione")
            vals |= {f["v1"], f["v2"]}
    fonti = [f for f in rep if f["tipo"] == "fonte"]
    if fonti:
        meccanismi.append("fonti")
        vals |= {f["v"] for f in fonti}
    app = [f for f in rep if f["tipo"] == "appartenenza"]
    if app:
        meccanismi.append("regole")
        regole = {}
        for f in rep:
            if f["tipo"] == "regola":
                if f["G"] in regole and regole[f["G"]] != f["v"]:
                    raise ValueError("due regole diverse per lo stesso gruppo")
                regole[f["G"]] = f["v"]
        for a in app:
            for G in (a["G1"], a["G2"]):
                if G not in regole:
                    return "LIBERO", meccanismi
                vals.add(regole[G])
    if len(set(meccanismi)) > 1:
        raise ValueError(f"più meccanismi nello stesso passaggio: {meccanismi}")
    return (sorted(vals) if vals else "LIBERO"), meccanismi


# --------------------------------------------------------------------------- analizzatore inverso
def _rx(tpl):
    out, pos = "", 0
    for m in re.finditer(r"\{(\w+)\}", tpl):
        out += re.escape(tpl[pos:m.start()])
        out += f"(?P<{m.group(1)}>.+?)"
        pos = m.end()
    return "^" + out + re.escape(tpl[pos:]) + "$"


def analizza(gen, tipo_attr, frasi):
    """Rilegge le frasi e ricostruisce la rappresentazione, senza usare quella originale.
    Ogni frase deve corrispondere a uno e un solo template. Il nome dell'entità si legge dall'introduzione."""
    g = GEN[gen]
    m = re.match(_rx(g["intro"]), frasi[0])
    if not m:
        raise ValueError(f"introduzione non riconosciuta: {frasi[0]}")
    ent = m.group("N")
    S = g["soggetto"].format(N=ent)
    s = g["soggetto_minuscolo"].format(N=ent)
    pr = g["pred"][tipo_attr]
    cand = []
    cand.append(("intro", "^" + re.escape(g["intro"].split("{R}")[0].format(N=ent)) + r"(?P<R>[A-Z][a-z]+)"
                 + re.escape(g["intro"].split("{R}")[1]) + "$", None))
    cand.append(("fatto_o", _rx(f"{S} " + pr.replace("{v}", "{v1} or " + PREF_PERSONA(gen, tipo_attr) + "{v2}") + "."), None))
    for ip, pp in enumerate(g["pads"][tipo_attr]):
        cand.append(("fatto_pad", _rx(f"{S} " + pp + "."), {"p": ip}))
    cand.append(("fatto", _rx(f"{S} " + pr + "."), None))
    cand.append(("fonte", _rx(g["fonte"].replace("{s}", s).replace("{P}", pr)), None))
    cand.append(("regola", _rx(g["gruppo_regola"].replace("{P}", pr)), None))
    cand.append(("appartenenza", _rx(g["gruppo_appartenenza"].replace("{S}", S)), None))
    for k, t in enumerate(g["neutre"]):
        cand.append(("neutra", "^" + re.escape(t.format(S=S)) + "$", {"k": k}))
    cand.append(("o_frase", "^" + re.escape(g["or_frase"][0].format(S=S, s=s)) + "$", None))
    cand.append(("e_frase", "^" + re.escape(g["or_frase"][1].format(S=S, s=s)) + "$", None))
    for i, (kind, t) in enumerate(g["contorno"]):
        field = {"anno": "y", "numero": "n", "luogo": "L", "persona": "Q"}.get(kind)
        t2 = t.replace("{S}", S).replace("{s}", s)
        cand.append(("contorno", _rx(t2), {"i": i, "campo": field}))
    rep = []
    for fr in frasi:
        hits = []
        for tipo, rx, extra in cand:
            mm = re.match(rx, fr)
            if mm:
                hits.append((tipo, mm, extra))
        # «fatto» e «fatto_pad» o «fatto_o» possono sovrapporsi come regex: si tiene la lettura più specifica
        tipi = {h[0] for h in hits}
        if "fatto_o" in tipi or "fatto_pad" in tipi:
            hits = [h for h in hits if h[0] != "fatto"]
        if "fatto_o" in tipi:
            hits = [h for h in hits if h[0] != "fatto_pad"]
        if len(hits) != 1:
            raise ValueError(f"frase con {len(hits)} letture: {fr}")
        tipo, mm, extra = hits[0]
        d = {"tipo": tipo}
        gd = mm.groupdict()
        if tipo == "intro":
            d["R"] = gd["R"]
        elif tipo == "fatto":
            d["v"] = gd["v"]
        elif tipo == "fatto_pad":
            d["v"], d["p"] = gd["v"], extra["p"]
        elif tipo == "fatto_o":
            d["v1"], d["v2"] = gd["v1"], gd["v2"]
        elif tipo == "fonte":
            d["F"], d["v"] = gd["F"], gd["v"]
        elif tipo == "regola":
            d["G"], d["v"] = gd["G"], gd["v"]
        elif tipo == "appartenenza":
            d["G1"], d["G2"] = gd["G1"], gd["G2"]
        elif tipo == "neutra":
            d["k"] = extra["k"]
        elif tipo == "contorno":
            d["i"] = extra["i"]
            if extra["campo"]:
                d["val"] = gd[extra["campo"]]
        rep.append(d)
    return ent, rep


# --------------------------------------------------------------------------- costruzione
def slot(fam, pos):
    """Indici delle frasi del blocco bersaglio (l'introduzione è la frase 0)."""
    if fam == "RIM":
        return {"inizio": [1], "meta": [4], "fine": [7]}[pos]
    if fam == "DUE":
        return {"inizio": [1], "meta": [4], "fine": [7]}[pos]
    if fam == "CONF":
        return {"inizio": [1, 4], "meta": [2, 5], "fine": [4, 7]}[pos]
    if fam == "LOG":
        return {"inizio": [1, 2, 3], "meta": [3, 4, 5], "fine": [5, 6, 7]}[pos]


def costruisci_passaggio(rng, idx, k, gen, tipo, nomi, prefisso):
    ent = nomi.nuovo()
    R = nomi.nuovo()
    v1, v2 = due_valori(rng, tipo, nomi, gen)
    g = GEN[gen]
    # valori di contorno: dello stesso tipo dei loro campi, tutti diversi dai due valori in gioco e fra loro.
    # Cronologia (C-gen-4): gli anni di contorno (lavori, premi, restauri) vengono dopo l'anno di riferimento: nei
    # passaggi di tipo anno dopo entrambi i valori in gioco (fondazione, varo, prima edizione), negli altri dopo un anno
    # di riferimento estratto e mai scritto. Così nessuna attività precede la nascita dell'entità.
    ancora = max(int(v1), int(v2)) if tipo == "anno" else rng.randint(1720, 1930)
    usati_val = {v1, v2}
    contorno = []
    for i, (kind, _) in enumerate(g["contorno"]):
        if kind == "anno":
            while True:
                y = str(rng.randint(ancora + ANNI_DOPO[0], min(ancora + ANNI_DOPO[1], ANNO_MAX_CONTORNO)))
                if y not in usati_val:
                    break
            val = y
        elif kind == "numero":
            while True:
                n = NUMERI[rng.randint(2, 12)]
                if n not in usati_val:
                    break
            val = n
        elif kind == "luogo":
            val = nomi.nuovo()
        elif kind == "persona":
            val = f"{nomi.nuovo(2)} {nomi.nuovo()}"
        else:
            val = None
        usati_val.add(val)
        d = {"tipo": "contorno", "i": i}
        if val is not None:
            d["val"] = val
        contorno.append(d)
    ordine_contorno = list(range(len(contorno)))
    rng.shuffle(ordine_contorno)
    G1, G2 = nomi.nuovo(2), nomi.nuovo(2)
    F1, F2 = nomi.nuovo(), nomi.nuovo()
    # k = indice del passaggio dentro il suo tipo di attributo. Schema di posizione, genere e bilanciamenti binari
    # ruotano su k, così ogni tipo ha gli stessi schemi in quote quasi uguali e la selezione può usare quote fisse.
    pos_base = k % 3
    fam_out = {}
    for fi, fam in enumerate(FAMIGLIE):
        pos = POSIZIONI[(pos_base + fi) % 3]
        alt = (k // 12 + fi) % 2                      # bilanciamenti binari: ordine dei valori, fonte o ramo che cambia
        ids = slot(fam, pos)
        if fam == "RIM":
            B_blocco = [[{"tipo": "fatto", "v": v1}]]
            C_varianti = [[{"tipo": "neutra", "k": k}] for k in range(len(g["neutre"]))]
            lati = {"B": [B_blocco[0]], "C": C_varianti}
        elif fam == "DUE":
            a, b = (v1, v2) if alt == 0 else (v2, v1)
            lati = {"B": [[{"tipo": "fatto", "v": v1}]] + [[{"tipo": "fatto_pad", "v": v1, "p": ip}]
                                                           for ip in range(len(g["pads"][tipo]))],
                    "C": [[{"tipo": "fatto_o", "v1": a, "v2": b}]]}
        elif fam == "CONF":
            Fa, Fb = (F1, F2) if (k // 24 + fi) % 2 == 0 else (F2, F1)
            B = [{"tipo": "fonte", "F": Fa, "v": v1}, {"tipo": "fonte", "F": Fb, "v": v1}]
            C = ([{"tipo": "fonte", "F": Fa, "v": v1}, {"tipo": "fonte", "F": Fb, "v": v2}] if alt == 0
                 else [{"tipo": "fonte", "F": Fa, "v": v2}, {"tipo": "fonte", "F": Fb, "v": v1}])
            lati = {"B": [B], "C": [C]}
        else:
            Ga, Gb = (G1, G2) if (k // 24 + fi) % 2 == 0 else (G2, G1)
            ramo = alt                                   # quale gruppo (primo o secondo citato) cambia valore in C
            regB = [{"tipo": "regola", "G": Ga, "v": v1}, {"tipo": "regola", "G": Gb, "v": v1}]
            regC = [dict(r) for r in regB]
            regC[ramo]["v"] = v2
            app = {"tipo": "appartenenza", "G1": Ga, "G2": Gb}
            lati = {"B": [regB + [app]], "C": [regC + [app]]}
        # contorno: le frasi che restano, nello stesso ordine in B e in C
        n_cont = N_FRASI - 1 - len(ids) - (1 if fam == "DUE" else 0)
        cont = [contorno[j] for j in ordine_contorno[:n_cont]]
        lato_out = {}
        for lato, varianti in lati.items():
            vv = []
            for blocco in varianti:
                frasi_rep = [None] * N_FRASI
                frasi_rep[0] = {"tipo": "intro", "R": R}
                for jb, i in enumerate(ids):
                    frasi_rep[i] = blocco[jb]
                if fam == "DUE":
                    j = 2 if pos != "inizio" else 6
                    frasi_rep[j] = {"tipo": "o_frase"} if lato == "B" else {"tipo": "e_frase"}
                it = iter(cont)
                for i in range(N_FRASI):
                    if frasi_rep[i] is None:
                        frasi_rep[i] = dict(next(it))
                frasi = [frase_testo(gen, ent, tipo, f) for f in frasi_rep]
                vv.append({"rep": frasi_rep, "frasi": frasi, "testo": " ".join(frasi)})
            if len(vv) > 1:                          # varianti di lunghezza: si tengono quelle entro 120–180 parole
                tenute = [v for v in vv if PAROLE_MIN <= len(v["testo"].split()) <= PAROLE_MAX]
                vv = tenute or vv[:1]
            lato_out[lato] = vv
        fam_out[fam] = {"posizione": pos, "indici_blocco": ids, "bilanciamento": alt, **lato_out}
    return {
        "passaggio_id": f"{prefisso}-{idx + 1:04d}", "indice_riserva": idx, "indice_nel_tipo": k,
        "schema_posizione": pos_base, "genere": gen, "tipo_attributo": tipo,
        "entita": ent, "soggetto": g["soggetto"].format(N=ent), "valore_B": v1, "valore_alternativo": v2,
        "risposte_B": alias(tipo, gen, v1), "risposte_alternativo": alias(tipo, gen, v2),
        "domanda": g["domanda"][tipo].format(N=ent), "nomi": {"regione": R, "gruppi": [G1, G2], "fonti": [F1, F2]},
        "famiglie": fam_out,
    }


# --------------------------------------------------------------------------- controlli
def conta_parola(testo, w):
    return len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(w) + r"(?![A-Za-z0-9])", testo))


def dividi_frasi(testo):
    """Frasi del testo destinato al modello: fine di frase = punto seguito da spazio e maiuscola, o fine del testo."""
    return re.split(r"(?<=\.) (?=[A-Z])", testo)


def controlla_passaggio(p):
    """Restituisce l'elenco dei problemi (vuoto se il passaggio è valido) e i dettagli dei controlli."""
    probl, det = [], {}
    gen, tipo = p["genere"], p["tipo_attributo"]
    v1, v2 = p["valore_B"], p["valore_alternativo"]
    vietate = GEN[gen]["vietate"][tipo]
    for fam, F in p["famiglie"].items():
        n_or = {}
        for lato in ("B", "C"):
            for k, var in enumerate(F[lato]):
                tag = f"{fam}/{lato}/{k}"
                # 0. il testo destinato al modello è esattamente l'unione delle frasi, e le sue frasi sono quelle
                if var["testo"] != " ".join(var["frasi"]) or dividi_frasi(var["testo"]) != var["frasi"]:
                    probl.append(f"{tag}: il testo destinato al modello non coincide con le frasi")
                # 1. determinabilità sulla rappresentazione
                try:
                    r1, mecc = risolvi(var["rep"])
                    # 2. determinabilità sul testo riletto
                    ent, rep2 = analizza(gen, tipo, dividi_frasi(var["testo"]))
                    r2, _ = risolvi(rep2)
                except ValueError as e:
                    probl.append(f"{tag}: rilettura o risolutore fermati: {e}")
                    continue
                if ent != p["entita"]:
                    probl.append(f"{tag}: entità riletta {ent}")
                if rep2 != var["rep"]:
                    probl.append(f"{tag}: rappresentazione riletta diversa")
                atteso = ([v1] if lato == "B" else ("LIBERO" if fam == "RIM" else sorted([v1, v2])))
                if r1 != atteso or r2 != atteso:
                    probl.append(f"{tag}: valori compatibili {r1} / {r2}, attesi {atteso}")
                t = var["testo"]
                # 3. occorrenze dei valori (anche in cifre per i numeri)
                occ1 = conta_parola(t, v1)
                occ2 = conta_parola(t, v2)
                if tipo == "numero":            # anche in cifre
                    occ1 += sum(conta_parola(t, x) for x in p["risposte_B"] if x.isdigit())
                    occ2 += sum(conta_parola(t, x) for x in p["risposte_alternativo"] if x.isdigit())
                atteso_occ = {("RIM", "B"): (1, 0), ("RIM", "C"): (0, 0), ("DUE", "B"): (1, 0), ("DUE", "C"): (1, 1),
                              ("CONF", "B"): (2, 0), ("CONF", "C"): (1, 1), ("LOG", "B"): (2, 0), ("LOG", "C"): (1, 1)}
                if (occ1, occ2) != atteso_occ[(fam, lato)]:
                    probl.append(f"{tag}: occorrenze dei valori {(occ1, occ2)}, attese {atteso_occ[(fam, lato)]}")
                # parole dell'attributo bersaglio solo nel blocco bersaglio
                for i, fr in enumerate(var["frasi"]):
                    if i in F["indici_blocco"]:
                        continue
                    for w in vietate:
                        if re.search(r"(?<![A-Za-z])" + w, fr, re.I):
                            probl.append(f"{tag}: parola dell'attributo «{w}» fuori dal blocco: {fr}")
                # marcatori di riserva o di assenza in tutto il testo
                for w in MARCATORI_RISERVA:
                    if re.search(r"(?<![A-Za-z])" + re.escape(w) + r"(?![A-Za-z])", t, re.I):
                        probl.append(f"{tag}: marcatore «{w}» nel testo")
                n_or[(lato, k)] = conta_parola(t, "or")
                nw = len(t.split())
                det.setdefault("parole", []).append(nw)
                if not (PAROLE_MIN <= nw <= PAROLE_MAX):
                    probl.append(f"{tag}: {nw} parole, fuori da {PAROLE_MIN}–{PAROLE_MAX}")
        # «or»: stesso numero in tutte le varianti di B e C; 0 in RIM e CONF, 1 in DUE e LOG
        attesi_or = {"RIM": 0, "CONF": 0, "DUE": 1, "LOG": 1}[fam]
        if set(n_or.values()) != {attesi_or}:
            probl.append(f"{fam}: conteggi di «or» {n_or}, attesi {attesi_or}")
        # coppie minime: B e C coincidono fuori dal blocco (e, in DUE, fuori dalla frase con «or»/«and»)
        for vb in F["B"]:
            for vc in F["C"]:
                diff = [i for i in range(N_FRASI) if vb["frasi"][i] != vc["frasi"][i]]
                ammessi = set(F["indici_blocco"]) | ({2 if F["posizione"] != "inizio" else 6} if fam == "DUE" else set())
                if not set(diff) <= ammessi:
                    probl.append(f"{fam}: B e C differiscono fuori dal blocco, frasi {diff}")
        # in LOG la frase con la disgiunzione è identica in B e in C
        if fam == "LOG":
            ia = [i for i, f in enumerate(F["B"][0]["rep"]) if f["tipo"] == "appartenenza"]
            if F["B"][0]["frasi"][ia[0]] != F["C"][0]["frasi"][ia[0]]:
                probl.append("LOG: disgiunzione diversa fra B e C")
    # cronologia (C-gen-4): nei passaggi di tipo anno ogni altro anno del testo viene dopo entrambi i valori in gioco
    # (letto dal testo di tutte le versioni, non dalla rappresentazione); B e C hanno gli stessi anni di contorno
    if tipo == "anno":
        lim = max(int(v1), int(v2))
        for fam, F in p["famiglie"].items():
            for lato in ("B", "C"):
                for k, var in enumerate(F[lato]):
                    altri = [int(y) for y in re.findall(r"(?<![0-9])(1[0-9]{3}|20[0-9]{2})(?![0-9])", var["testo"])
                             if y not in (v1, v2)]
                    prima = [y for y in altri if y <= lim]
                    if prima:
                        probl.append(f"{fam}/{lato}/{k}: cronologia, anni di contorno non successivi a {lim}: {prima}")
    # domanda: contiene il soggetto e nessun valore
    if conta_parola(p["domanda"], v1) or conta_parola(p["domanda"], v2):
        probl.append("domanda con un valore")
    return probl, det


def main(out_dir):
    import os
    os.makedirs(out_dir, exist_ok=True)
    reali = real_names()
    rapporto = {"versione": VERSIONE, "nomi_reali_nell_elenco": len(reali)}
    insiemi = {}
    vietati = set()
    for nome, seme, n, prefisso in (("definitivo", SEME_DEFINITIVO, N_RISERVA, "C"),
                                    ("prova", SEME_PROVA, N_RISERVA_PROVA, "P")):
        rng = random.Random(seme)
        nomi = Nomi(rng, reali, vietati)
        out, scarti = [], []
        for idx in range(n):
            t = TIPI[idx % 4]                                    # i tipi si alternano
            k = idx // 4                                         # indice dentro il tipo
            strato = TIPI.index(t) * 3 + k % 3                   # tipo × schema di posizione
            g = GENERI[(k // 3 + strato) % 4]                    # in ogni strato i generi ruotano, con partenza diversa
            p = costruisci_passaggio(rng, idx, k, g, t, nomi, prefisso)
            probl, det = controlla_passaggio(p)
            p["controlli_generatore"] = {"superati": not probl, "problemi": probl}
            (out if not probl else scarti).append(p)
        vietati |= nomi.usati
        insiemi[nome] = (out, scarti, nomi)
    # disgiunzione fra prova e definitivo: ID e nomi (tutte le parole dei nomi)
    def parole_nomi(ps):
        w = set()
        for p in ps:
            w |= {p["entita"].lower(), p["nomi"]["regione"].lower()} | {x.lower() for x in p["nomi"]["gruppi"] + p["nomi"]["fonti"]}
            for v in (p["valore_B"], p["valore_alternativo"]):
                if p["tipo_attributo"] in ("luogo", "persona"):
                    w |= {x.lower() for x in v.split()}
            for fam in p["famiglie"].values():
                for f in fam["B"][0]["rep"]:
                    if f["tipo"] == "contorno" and isinstance(f.get("val"), str) and not f["val"].isdigit() \
                            and f["val"] not in NUMERI.values():
                        w |= {x.lower() for x in f["val"].split()}
        return w
    d_all = insiemi["definitivo"][0] + insiemi["definitivo"][1]
    p_all = insiemi["prova"][0] + insiemi["prova"][1]
    comuni = parole_nomi(d_all) & parole_nomi(p_all)
    ids_comuni = {p["passaggio_id"] for p in d_all} & {p["passaggio_id"] for p in p_all}
    rapporto["prova_definitivo_nomi_in_comune"] = sorted(comuni)
    rapporto["prova_definitivo_id_in_comune"] = sorted(ids_comuni)
    if comuni or ids_comuni:
        raise RuntimeError(f"prova e definitivo condividono nomi o ID: {sorted(comuni)[:10]} {sorted(ids_comuni)[:10]}")
    for nome, (out, scarti, nomi) in insiemi.items():
        fname = f"testC_sintetico_{nome}_riserva.json"
        payload = {"versione": VERSIONE, "insieme": nome, "seme": SEME_DEFINITIVO if nome == "definitivo" else SEME_PROVA,
                   "nota": "riserva ordinata; la selezione finale si fa su Colab con i controlli dei tokenizer",
                   "passaggi": out}
        txt = json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True)
        with open(os.path.join(out_dir, fname), "w") as fh:
            fh.write(txt)
        bil = defaultdict(Counter)
        for p in out:
            bil["tipo"][p["tipo_attributo"]] += 1
            bil["genere"][p["genere"]] += 1
            bil["genere_x_tipo"][f"{p['genere']}/{p['tipo_attributo']}"] += 1
            bil["tipo_x_schema_posizione"][f"{p['tipo_attributo']}/{p['schema_posizione']}"] += 1
            for fam, F in p["famiglie"].items():
                bil[f"posizione_{fam}"][F["posizione"]] += 1
                bil[f"bilanciamento_{fam}"][F["bilanciamento"]] += 1
        rapporto[nome] = {
            "file": fname, "sha256": hashlib.sha256(txt.encode()).hexdigest(), "riserva_generata": len(out) + len(scarti),
            "validi": len(out), "scartati": len(scarti),
            "motivi_scarto": Counter(pr.split(":")[0] + ": " + pr.split(":")[1].split(",")[0].strip()[:60]
                                     for p in scarti for pr in p["controlli_generatore"]["problemi"]).most_common(),
            "nomi_scartati_perche_reali": nomi.scartati_reali, "bilanciamento": {k: dict(v) for k, v in bil.items()},
        }
        with open(os.path.join(out_dir, f"scarti_{nome}.json"), "w") as fh:
            json.dump(scarti, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(out_dir, "controlli_generatore.json"), "w") as fh:
        json.dump(rapporto, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print(json.dumps({k: (v if k in ("versione",) else v) for k, v in rapporto.items()}, ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    main(sys.argv[1])
