# Step 3, proposta per la libreria (bozza v1, 13 novembre)

Da approvare prima di scrivere codice. Base: `../Step2_uscite/Riepilogo_Step2.md` e `../Step1_verifica/Riepilogo_Step1.md`.
Le decisioni chieste a Simona sono raccolte nella sezione 10.

## 1. Che cosa è la libreria, in una frase

Un **benchmark con protocollo di validazione** per misurare se un rilevatore di incertezza o di allucinazioni riconosce i casi in cui la risposta **non è determinabile** dal testo, confrontandolo con un riferimento semplice e senza addestramento, p(UNKNOWN).

Non è un nuovo rilevatore. I dati dello Step 1 e dello Step 2 non ne giustificano uno: le sonde non generalizzano e nessun metodo pubblicato provato supera p(UNKNOWN). Il contributo che regge è il metodo di valutazione, e la libreria lo rende riutilizzabile.

**Destinatari:** ricercatori che sviluppano o usano metodi di incertezza (LM-Polygraph, sonde sugli stati interni, giudici, answerability) e vogliono sapere che cosa fanno questi metodi sull'indeterminatezza logica.

## 2. Che cosa contiene la versione 0.1

| Parte | Contenuto | Da dove viene |
|---|---|---|
| **Dati del benchmark** | (a) Storie logiche con coppie minime B/C: 200 storie × AND, OR, IMPLIES × POS/NOT, formati prosa (P−S) e simbolico (S−S), come nel Test M. (b) Passaggi di testo sintetici del Test C: famiglie DUE, CONF, LOG e RIM come controllo di dominio, 800 coppie. Ogni insieme è congelato, con SHA-256 e scheda dei dati. | generatore delle storie del Test U2 (cella 3), `gen_testC.py` e `sel_testC.py` (C-gen-3, C-sel-8) |
| **Generatori** | Gli stessi generatori, deterministici con seme, per creare insiemi nuovi (per esempio per una replica preregistrata) con i controlli già usati: risolutore logico, analizzatore inverso, controllo dei token e del limite di lunghezza. | come sopra |
| **Riferimento p(UNKNOWN)** | Probabilità del primo token di «UNKNOWN» (varianti di maiuscole e spazio) al primo passo di generazione, con il chat template del modello e thinking disattivato per Qwen. Esecuzione con `transformers`, greedy, batch 1. Restituisce anche la risposta generata e se è finita. | `tm_comune.predict_reference` |
| **Metriche** | W (coppie vinte da C, pareggi a mezzo punto, media per storia o passaggio), IC con bootstrap per storia, ΔW sulle coppie valide comuni con margine 1 − W_rif, D (RIM), AUROC per passaggio, analisi per famiglia e H, copertura e scarti. | `tc_analisi.py`, notebook B cella 10 |
| **Protocollo di validazione** | Un documento e una funzione che produce la «scheda» di un metodo: controllo positivo dichiarato dall'utente, copertura, W e ΔW con IC, verdetti con le soglie fissate, regola dei 3 su 4, analisi per famiglia, formule di lettura. | protocolli U, M, C |
| **Avvisi automatici** (nuovi, dalle lezioni dello Step 2) | La scheda segnala: soffitto del riferimento (margine sotto la soglia di ΔW), classi di HC4 sbilanciate per famiglia, famiglie con W opposti, punteggi quasi costanti (sonda collassata), accuratezza su B sotto 0.80 per famiglia. | `Risultati_testC.md` §4, `Risultati_testM_B.md` |
| **Esempi** | Notebook Colab: (1) p(UNKNOWN) su un modello open-weights; (2) valutare un proprio metodo dai punteggi in CSV; (3) riprodurre le tabelle del Test M e del Test C dai dati grezzi. | nuovi, su codice esistente |

## 3. Che cosa NON contiene

- Sonde addestrate, pesi o nuovi rilevatori.
- Reimplementazioni di metodi altrui. LM-Polygraph, SIRIN e le sonde di Obeso restano librerie esterne. La libreria offre solo **script di esempio** che le chiamano nei loro ambienti fissati (quelli del Test M), fuori dalle dipendenze.
- Il classificatore delle risposte del Test C come strumento affidabile. Con concordanza 0.68 entra al massimo come modulo **sperimentale**, con l'avvertenza (decisione 10.4).
- I dati di SQuAD (insieme naturale): vedi licenze, sezione 8.

## 4. Come si usa (bozza dell'interfaccia)

Il metodo da valutare è una funzione che riceve le righe (prompt, risposta, metadati) e restituisce un punteggio per riga: **più alto vuol dire più incerto**. In alternativa l'utente carica un CSV con `row_id, punteggio`.

```python
import nome_libreria as nl

dati = nl.carica("storie_PS")                      # insieme congelato, SHA verificato
rif = nl.p_unknown(dati, modello="Qwen/Qwen3-8B")   # riferimento, su GPU
mio = nl.punteggi_da_csv("mio_metodo.csv")         # oppure una funzione Python

scheda = nl.valuta(dati, mio, riferimento=rif,
                   controllo_positivo=0.82,         # AUROC del metodo sul suo dominio, dichiarata
                   soglie=nl.SOGLIE_TEST_M)
print(scheda.verdetti())       # HM1, HM2, per famiglia, avvisi
scheda.salva("scheda_mio_metodo/")   # JSON + tabelle + impronta dei dati e del codice
```

`nl.riassumi([scheda_qwen, scheda_mistral, ...])` applica la regola dei 3 su 4 e scrive le formule di lettura preregistrate.

## 5. Struttura della repository

```
<nome>/
  README.md               scopo, installazione, esempio minimo, risultati di riferimento, limiti
  pyproject.toml          dipendenze di base: numpy, pandas; extra [hf]: torch, transformers
  src/<nome>/
    dati.py               caricamento e verifica SHA degli insiemi
    generatori/           storie logiche, passaggi del Test C, risolutore, controlli
    riferimento.py        p(UNKNOWN)
    metriche.py           W, ΔW, D, AUROC per passaggio, bootstrap per gruppo
    protocollo.py         soglie, verdetti, regola dei 3 su 4, formule, avvisi
    scheda.py             esportazione e impronte
    sperimentale/         classificatore delle risposte (se approvato)
  dati/                   insiemi congelati (JSONL) + schede dei dati + SHA256SUMS
  risultati_riferimento/  W e ΔW pubblicati dei Test M e C (per i test di regressione)
  docs/                   protocollo di validazione, metodo, limiti, glossario
  esempi/                 notebook Colab; script per LM-Polygraph, SIRIN, Obeso
  tests/                  test unitari + riproduzione numerica dei Test M e C
  NOTICE                  attribuzioni (modelli, dataset, librerie esterne)
```

## 6. Criterio di accettazione della v0.1

La libreria è pronta quando, **dai punteggi grezzi già archiviati** (ZIP dei completi in `Step2_uscite/`), riproduce senza GPU:
- tutti i W e ΔW del Test M (notebook A e B) e del Test C, con stime puntuali identiche e IC entro ±0.01 (stesso criterio del ricalcolo indipendente);
- gli insiemi di dati congelati, rigenerati dai generatori con lo stesso SHA-256.

Poi una prova su Colab: p(UNKNOWN) di un modello su P−S deve coincidere con il Test U2 (scarto ≤ 1e-6 nello stesso ambiente).

## 7. Piano di lavoro

Ogni passo è una pull request che Simona rivede prima di passare al successivo.

1. Scheletro, metriche e protocollo, con i test di riproduzione sui dati archiviati (solo CPU).
2. Dati congelati e generatori, con la verifica degli SHA.
3. Riferimento p(UNKNOWN) e notebook Colab di esempio; prova su Colab di Simona.
4. Scheda, avvisi automatici e documentazione del protocollo.
5. Script di esempio per i metodi esterni e README finale.

Stima di lavoro mio: i passi 1–2 sono i più lunghi (portare il codice dai notebook in moduli testati). Ore di Colab: solo la prova del passo 3, circa 15–20 minuti per modello.

## 8. Licenze

**Della repository.** Privata, nessuna licenza aperta per ora (decisione del 10 novembre). Nel README e in un file `LICENSE`: «Copyright © 2026 [titolare, da indicare]. Tutti i diritti riservati.» Accesso solo a Giuseppe Aceto. Zenodo/DOI dopo.

**Di terzi.** La libreria non distribuisce pesi di modelli né codice di terzi.

| Componente | Licenza | Stato | Conseguenza |
|---|---|---|---|
| Qwen3-8B, Qwen3-4B, Mistral-Nemo-Instruct-2407, OLMo-2-7B-Instruct | Apache 2.0 | nota di Simona | citazione in NOTICE |
| Llama-3.1-8B-Instruct | Llama 3.1 Community License | nota di Simona | se la repository contiene risposte o punteggi di Llama: «Built with Llama», copia della licenza, Acceptable Use Policy |
| LM-Polygraph 0.7.0 | MIT | **verificato** (metadati del pacchetto) | solo negli esempi; citazione |
| SIRIN (commit ef3bed1) | Apache 2.0 | **verificato** (LICENSE) | solo negli esempi; citazione |
| Sonde di Obeso et al. (hallucination-probes) | Apache 2.0 | **verificato** (LICENSE della repository) | solo negli esempi; citazione |
| SQuAD 2.0 | CC BY-SA 4.0 | da verificare | ridistribuire coppie derivate obbliga a CC BY-SA, in conflitto con «nessuna licenza aperta». Proposta: nessun dato SQuAD nella repository, solo lo script che ricostruisce l'insieme naturale dagli ID |
| TriviaQA, LongFact, DeBERTa-large-mnli | da verificare | da verificare | servono solo ai controlli positivi negli esempi; non si ridistribuiscono |

Le storie logiche e i passaggi del Test C sono generati da noi con entità inventate: nessun vincolo di terzi.

## 9. Che cosa dice il README sui risultati

Solo quello che regge, con le formule del Riepilogo dello Step 2: p(UNKNOWN) non è superata da nessun metodo pubblicato provato su questi dati; dipendenza forte da famiglia e forma; HC4 non ancora misurabile. Con i limiti: 4 modelli 7–12B, inglese, testi da template.

## 10. Decisioni per Simona

1. **Nome della libreria.** Proposte: `bcpairs` (coppie B/C), `undecidable-bench`, `indet` (indeterminatezza). Va bene anche un nome tuo.
2. **Lingua.** Proposta: codice, README e documentazione in inglese per i ricercatori; i protocolli originali in italiano dentro `docs/`.
3. **Insieme naturale (SQuAD).** Proposta: solo lo script di ricostruzione, nessun dato (sezione 8).
4. **Classificatore delle risposte del Test C.** Proposta: modulo `sperimentale/` con l'avvertenza della concordanza 0.68, oppure fuori dalla v0.1.
5. **Script per LM-Polygraph, SIRIN, Obeso.** Proposta: dentro `esempi/`, con gli ambienti fissati del Test M, non come dipendenze.
6. **Repository.** Questa sessione non può creare repository. Va creata da te su GitHub: privata, vuota, senza README né licenza, con il nome scelto al punto 1. Poi me lo dici e la collego io. Dopo il primo commit inviti Giuseppe Aceto come collaboratore (Settings → Collaborators).