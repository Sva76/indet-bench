# Note al notebook `IndetBench_modelli_nuovi_v1.ipynb` (N-notebook-1)

14 novembre 2026. Bozza per la revisione di Simona prima del lancio.

## 1. Scopo e statuto dei risultati

Il notebook verifica su modelli di famiglie nuove il risultato principale dei Test U/U2: p(UNKNOWN) ordina C sopra B sulle 800 coppie congelate in prosa (set PN, P−S). I risultati sui modelli nuovi sono **esplorativi**. Non sono una validazione indipendente del metodo, che richiederebbe altri autori, altro codice e un protocollo registrato altrove. Un W alto non dimostra da solo la validità del metodo. Va letto insieme alle baseline dalle uscite e ai controlli sugli artefatti (sezione 4).

Il notebook usa solo le 800 coppie originali. Le 240 coppie (`data/smol_stat_v01_frozen.jsonl`) restano fuori: sono un lavoro separato e non ancora validato.

## 2. Che cosa resta identico al Test U2

- **Prompt.** Sono quelli del file congelato `M_Original_4800_righe.json.gz`. `load_frozen` controlla lo SHA-256 `906c01bf…` e `export_rows("PN")` li copia senza modificarli.
- **Inferenza.** Si usa `hf_runner.score_pairs` al commit `c086e65`, con le stesse impostazioni del Test U2: bfloat16, attenzione eager, batch 1, risposta greedy di 8 token, solo il messaggio utente nel chat template. Per Qwen il ragionamento è spento (`enable_thinking=False`). La probabilità del primo token è sommata sulle 6 varianti di scrittura di ogni etichetta, senza rinormalizzazione.
- **Esclusione per lunghezza.** Una coppia in cui B e C hanno un numero di token diverso viene esclusa per intero, come nella cella 4 del Test U2. Con un tokenizer nuovo può succedere, perché B e C differiscono solo per «true» e «false».
- **Analisi.** La fa `original_benchmark.report` al commit fissato: W con IC95 (2000 ricampionamenti delle storie, seme 20261108), regola HU1/HI1 (CONFIRMED se W ≥ 0.60 e il limite inferiore è sopra 0.5), soglia di competenza vincolante della PR #3 (≥ 0.50 sui B complessivamente e separatamente su gold YES e gold NO, altrimenti NOT EVALUABLE) e W per famiglia, solo descrittivo.

## 3. Modelli e revisioni (fissati prima dei dati)

| Chiave | Modello | Revisione | Licenza | Nota |
|---|---|---|---|---|
| qwen_controllo | Qwen/Qwen3-8B | b968826d9c46dd6066d109eabc6255188de91218 | Apache-2.0 | controllo positivo, è il modello originale |
| gemma2_9b | google/gemma-2-9b-it | 11c9b309abf73637e4b6f9a3fa1e92e615547819 | Gemma Terms of Use | gated: bisogna accettare la licenza su HF |
| yi15_9b | 01-ai/Yi-1.5-9B-Chat | 1a0fc698cf883c4f5c325f026ca79f0ebd9955a5 | Apache-2.0 | |
| falcon3_7b | tiiuae/Falcon3-7B-Instruct | 1e57a0ecd176c7c139f289c60a74e57f887c3dfb | TII Falcon License 2.0 | |
| phi4 | microsoft/phi-4 | 2db69c1c3e91a05d2c64a3185acfbaf36f744e25 | MIT | 14B, come Mistral-Nemo 12B negli originali |

Gli SHA sono stati letti dall'API di Hugging Face il 14 novembre. Il notebook li ricontrolla con `HfApi.model_info` prima di scaricare i pesi. Le licenze vanno ricontrollate prima di citarle nel README.

**Escluso:** IBM Granite-3.3-8B-Instruct. Il suo chat template inserisce la data del giorno (`strftime_now`), quindi il prompt cambierebbe a ogni data di lancio. Il notebook ferma come NON MISURABILE qualsiasi modello con un template di questo tipo, o senza template.

## 4. Rapporto: tre livelli e anomalie

Per ogni modello `esito.json` e `rapporto.txt` separano tre livelli:

1. **Funziona tecnicamente?** Revisione verificata, template ed etichette controllati, coppie valide e coppie escluse per lunghezza, risposte non leggibili (ALTRO), quota di righe con massa YES+NO+UNKNOWN sotto 0.90, controllo positivo Qwen.
2. **Misura ciò che intendiamo?** Soglia di competenza, W per famiglia, per variante (POS/NOT), per posizione (prima/ultima) e per famiglia × variante. Poi W a parità di risposta generata: nessuna delle due risposte UNKNOWN, entrambe UNKNOWN, C senza UNKNOWN. Infine W della lunghezza del prompt, che vale 0.5 per costruzione dopo l'esclusione.
3. **Aggiunge rispetto alle baseline?** W e AUROC di p(UNKNOWN) a confronto con p(UNKNOWN) normalizzata, meno la p massima normalizzata, l'entropia normalizzata e la risposta generata UNKNOWN (0/1). Il confronto è **descrittivo**: per i modelli nuovi non c'è un test preregistrato di superiorità sulle baseline. Se lo vuoi, va fissato prima del completo (per esempio ΔW con IC appaiato, come HM2).

**Anomalie.** Il notebook elenca in `anomalie.csv` ciò che segnala in automatico: coppie escluse per lunghezza, ALTRO > 5%, massa bassa > 5% delle righe, un'etichetta mai generata, soglia di competenza non superata, differenza di W fra famiglie ≥ 0.20 (soglia descrittiva del Test M), una baseline che eguaglia o supera p(UNKNOWN), Qwen non allineato. Ogni anomalia nasce **DA CLASSIFICARE**, con le categorie possibili indicate (comportamento del modello, problema tecnico, limite del protocollo, evidenza scientifica). Le colonne vuote per la causa ipotizzata, i controlli effettuati e ciò che resta incerto vanno compilate a mano. Il notebook non attribuisce cause.

## 5. Regole fissate qui, da confermare prima del completo

1. **Controllo positivo.** Qwen3-8B deve riprodurre 24 valori archiviati di p(UNKNOWN) del Test U2 (storie V2001–V2003, B e C) entro 1e-3. Nel completo deve anche ridare W 0.975 entro 0.005, come nella regola di allineamento del Test U2. Se fallisce, il rapporto dice che i valori dei modelli nuovi non sono confrontabili con i resoconti finché la causa non è chiarita. Gli altri modelli girano comunque.
2. **Copertura minima: 760 coppie valide su 800**, come nel Test M. Sotto questa soglia l'esito è DESCRITTIVO. La soglia di competenza si calcola sui B delle coppie tenute.
3. **Massa bassa.** Si segnala cautela se più del 5% delle righe ha massa < 0.90, come nel Test U2.
4. **Adattamento tecnico.** Il tokenizer restituisce solo `input_ids` e `attention_mask`. Alcuni tokenizer producono anche `token_type_ids`, che `generate()` rifiuta per i modelli causali. Il calcolo non cambia e il valore originale viene registrato in `esito.json`. Questo punto è emerso nella prova a secco con un tokenizer finto.

## 6. Controlli fatti prima della consegna (CPU, senza GPU)

- **Prova e completo con un modello Llama finto** (casuale, minuscolo): tutte le celle girano. Ci sono checkpoint ogni 50 righe, ZIP per modello e ZIP finale. Quando si rilancia, il modello già completato viene saltato e i blocchi mancanti vengono ricalcolati. Il W calcolato a parte dal `punteggi.csv` coincide.
- **Analisi del notebook sui punteggi archiviati del Test U2 (4 modelli originali, PN):** W 0.975, 0.7825, 0.6937 e 0.7462, identici al rapporto del Test U2. Gli IC differiscono al massimo di 0.004, come già documentato per `report`. Le accuratezze sui B e per gold coincidono con la tabella della PR #3, l'esito è CONFIRMED per tutti e 4, e il W dell'entropia coincide con il Test U2.
- **Template con `strftime_now` o assente:** il modello viene fermato come NON MISURABILE.

Non verificato: il comportamento reale dei 5 modelli su GPU e le versioni di transformers in Colab. Il controllo positivo Qwen serve a questo.

## 7. Prima del lancio

- **Secrets di Colab** con «Accesso al notebook» attivo: `GH_TOKEN` (token GitHub fine-grained, sola lettura dei contenuti di `Sva76/indet-bench`) e `HF_TOKEN`. Per Gemma bisogna accettare la licenza sulla pagina del modello.
- **Commit fissato `c086e65`.** Si trova sul ramo della PR #3. Se quel ramo viene riscritto, va aggiornato `REPO_COMMIT` con una nuova versione del notebook.
- **Tempi.** Inferenza di 1600 righe per modello: stimo 10–20 minuti su A100, più il download dei pesi (circa 16–30 GB per modello). È una stima, non una misura.
