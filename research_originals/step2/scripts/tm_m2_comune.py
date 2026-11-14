# Funzioni comuni agli script di M2 (env_sirin): testo d'ingresso, resa con il chat template di SIRIN, lunghezze,
# confine dell'assistente e sottoinsiemi annidati dei dati di addestramento.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

MAX_TOKEN = 512


def inspection_prompt(context, question):
    # come M3 e come _inspection_prompt dell'interfaccia di SIRIN (nota M2 v2, §2.5)
    return f'Context:\n{context.strip()}\n\nQuestion:\n{question.strip()}'


def sample_of(row):
    # campione di SIRIN: turno utente con il testo d'ingresso, turno dell'assistente vuoto, nessun prompt di sistema
    return [{"role": "user", "content": inspection_prompt(row["contesto"], row["domanda"])},
            {"role": "assistant", "content": ""}]


class Renderer:
    """Resa del campione come la fa HfModelAdapter di SIRIN (stesso tokenizer, stesso _preprocess_input).

    Il tokenizer si carica con la stessa chiamata di _load_model_and_tokenizer (AutoTokenizer, revisione fissata),
    senza caricare i pesi del modello."""

    def __init__(self, model_id, revision, tokenizer=None, adapter=None):
        from sirin.inference.adapters import HfModelAdapter
        from sirin.models.inference import HFConfig
        from transformers import AutoTokenizer
        if adapter is None:
            adapter = HfModelAdapter(HFConfig(model_path=model_id, revision=revision, device="cpu"))
            tok = tokenizer or AutoTokenizer.from_pretrained(model_id, revision=revision)
            if adapter.config.max_length is not None:
                tok.max_length = min(adapter.config.max_length, tok.model_max_length)
            tok.padding_side = adapter.config.padding_side or "right"
            adapter.tokenizer = tok
        self.adapter = adapter
        self.tok = adapter.tokenizer
        # Il localizzatore di SIRIN (HfTokenLocator.locate) decodifica i token del prompt e li ritokenizza per avere gli
        # offset. Con clean_up_tokenization_spaces=True (default di alcuni tokenizer) la decodifica toglie gli spazi
        # prima di «, . ? ! 's n't…», la ritokenizzazione dà meno token e il localizzatore si ferma (prova del 11
        # novembre: «200 token ids but 198 offsets»). La pulizia agisce solo sulla decodifica: la si spegne sull'istanza
        # del tokenizer, così la decodifica è il testo esatto. La tokenizzazione, e quindi gli stati, non cambiano.
        self.pulizia_spazi_originale = bool(getattr(self.tok, "clean_up_tokenization_spaces", False))
        self.tok.clean_up_tokenization_spaces = False

    def render(self, sample):
        return self.adapter._preprocess_input([sample])[0]

    def ids(self, text):
        # come generate_hiddens: add_special_tokens=False sul testo già reso
        return self.tok(text, add_special_tokens=False)["input_ids"]

    def full_length(self, row):
        return len(self.ids(self.render(sample_of(row))))

    def boundary(self, row):
        """Controlli del confine dell'assistente per un campione.

        n_full: token dell'intero prompt (quelli che entrano nel passaggio in avanti, senza padding né troncamento);
        n_user: token della resa del solo turno utente; ans_start: primo token della parte dell'assistente secondo il
        localizzatore di SIRIN (HfTokenLocator, locate_answer_start), cioè il confine usato da side=LEFT;
        prefix_ok: la resa completa comincia con quella del solo turno utente."""
        from sirin.inference.token_locators import HfTokenLocator
        from sirin.models.inference import TokenLocatorConfig
        sample = sample_of(row)
        full = self.render(sample)
        user = self.adapter._preprocess_input([sample[:1]])[0]
        full_ids = self.ids(full)
        answer = full[len(user):]                    # come locate_tokens di HfModelAdapter
        roundtrip = self.ids(self.tok.decode(full_ids, skip_special_tokens=False)) == full_ids
        try:
            loc = HfTokenLocator(TokenLocatorConfig(locate_answer_start=True)).locate(
                tokens=full_ids, tokenizer=self.tok, answer_text=answer)
            ans_start, err = int(loc["answer_start"]), None
        except ValueError as e:                     # il localizzatore di SIRIN non trova il confine: errore registrato
            ans_start, err = -1, str(e)[:300]
        return dict(n_full=len(full_ids), n_user=len(self.ids(user)), ans_start=ans_start,
                    prefix_ok=full.startswith(user), roundtrip_ok=roundtrip, errore_localizzatore=err, suffix=answer)


def word_ends(text):
    # fine (carattere escluso) di ogni parola, dove una parola è una sequenza di caratteri non bianchi
    return [m.end() for m in re.finditer(r"\S+", text)]


def nested(rows, n_total):
    """Sottoinsieme annidato: le prime n_total/2 righe di ciascuna classe nell'ordine fissato dalla selezione,
    poi l'ordine di addestramento fissato (campo 'ordine'). Le dimensioni piccole sono contenute nelle grandi."""
    assert n_total % 2 == 0, n_total
    half = n_total // 2
    out = []
    for label in (0, 1):
        part = [r for r in rows if r["label"] == label][:half]
        if len(part) != half:
            raise RuntimeError(f"servono {half} righe della classe {label}, ce ne sono {len(part)}")
        out += part
    return sorted(out, key=lambda r: r["ordine"])
