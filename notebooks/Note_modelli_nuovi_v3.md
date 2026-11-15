# Note al notebook `IndetBench_modelli_nuovi_v3.ipynb` (N-notebook-3)

14 novembre 2026. La v2 recepisce le decisioni di Simona delle 09:19 (sezione 5). La v3 recepisce la decisione delle 15:38 sulla baseline «p(UNKNOWN) normalizzata» (sezione 5, punto 8), presa dopo la prova e prima di qualsiasi dato del completo. I tre sì autorizzano la preparazione della prova, non l'accettazione scientifica dei risultati.

## 1. Scopo e statuto dei risultati

Il notebook verifica su modelli di famiglie nuove il risultato principale dei Test U/U2: p(UNKNOWN) ordina C sopra B sulle 800 coppie congelate in prosa (set PN, P−S). I risultati sui modelli nuovi sono **esplorativi**. Non sono una validazione indipendente del metodo, che richiederebbe altri autori, altro codice e un protocollo registrato altrove. Un W alto non dimostra da solo la validità del metodo. Va letto insieme alle baseline dalle uscite e ai controlli sugli artefatti (sezione 4).

Il notebook usa solo le 800 coppie originali. Le 240 coppie (`data/smol_stat_v01_frozen.jsonl`) restano fuori: sono un lavoro separato e non ancora validato.

## 2. Che cosa resta identico al Test U2

- **Prompt.** Sono quelli del file congelato `M_Original_4800_righe.json.gz`. `load_frozen` controlla lo SHA-256 `906c01bf…` e `export_rows("PN")` li copia senza modificarli.
- **Inferenza.** Si usa `hf_runner.score_pairs` al commit `c086e65`, con le stesse impostazioni del Test U2: bfloat16, attenzione eager, batch 1, risposta greedy di 8 token, solo il messaggio utente nel chat template. Per Qwen il ragionamento è spento (`enable_thinking=False`). La probabilità del primo token è sommata sulle 6 varianti di scrittura di ogni etichetta, senza rinormalizzazione.
- **Esclusione per lunghezza.** Una coppia in cui B e C hanno un numero di token diverso viene esclusa per intero dall'analisi principale, come nella cella 4 del Test U2. Con un tokenizer nuovo può succedere, perché B e C differiscono solo per «true» e «false». Dalla v2 le coppie escluse vengono **misurate comunque**: restano in `punteggi.csv` (colonna `coppia_esclusa_lunghezza`) e in `scarti_lunghezza.csv`, così si può controllare la distorsione (sezione 5).
- **Analisi.** La fa `original_benchmark.report` al commit fissato: W con IC95 (2000 ricampionamenti delle storie, seme 20261108), regola HU1/HI1 (CONFIRMED se W ≥ 0.60 e il limite inferiore è sopra 0.5), soglia di competenza vincolante della PR #3 (≥ 0.50 sui B complessivamente e separatamente su gold YES e gold NO, altrimenti NOT EVALUABLE) e W per famiglia, solo descrittivo.

## 3. Modelli e revisioni (fissati prima dei dati)

| Chiave | Modello | Revisione | Licenza | Nota |
|---|---|---|---|---|
| qwen_controllo | Qwen/Qwen3-8B | b968826d9c46dd6066d109eabc6255188de91218 | Apache-2.0 | controllo positivo, è il modello originale |
| gemma2_9b | google/gemma-2-9b-it | 11c9b309abf73637e4b6f9a3fa1e92e615547819 | Gemma Terms of Use | gated: bisogna accettare la licenza su HF |
| yi15_9b | 01-ai/Yi-1.5-9B-Chat | 1a0fc698cf883c4f5c325f026ca79f0ebd9955a5 | Apache-2.0 | |
| falcon3_7b | tiiuae/Falcon3-7B-Instruct | 1e57a0ecd176c7c139f289c60a74e57f887c3dfb | TII Falcon-LLM License 2.0 | |
| phi4 | microsoft/phi-4 | 2db69c1c3e91a05d2c64a3185acfbaf36f744e25 | MIT | 14B, come Mistral-Nemo 12B negli originali |

Gli SHA sono stati letti dall'API di Hugging Face il 14 novembre. Il notebook li ricontrolla con `HfApi.model_info` prima di scaricare i pesi. Le licenze vanno ricontrollate prima di citarle nel README.

**Escluso:** IBM Granite-3.3-8B-Instruct. Il suo chat template inserisce la data del giorno (`strftime_now`), quindi il prompt cambierebbe a ogni data di lancio. Il notebook ferma come NON MISURABILE qualsiasi modello con un template di questo tipo, o senza template.

## 4. Rapporto: tre livelli e anomalie

Per ogni modello `esito.json` e `rapporto.txt` separano tre livelli:

1. **Funziona tecnicamente?** Revisione verificata, template ed etichette controllati, coppie valide e coppie escluse per lunghezza, risposte non leggibili (ALTRO), quota di righe con massa YES+NO+UNKNOWN sotto 0.90, controllo positivo Qwen.
2. **Misura ciò che intendiamo?** Soglia di competenza, W per famiglia, per variante (POS/NOT), per posizione (prima/ultima) e per famiglia × variante. Poi W a parità di risposta generata: nessuna delle due risposte UNKNOWN, entrambe UNKNOWN, C senza UNKNOWN. Infine W della lunghezza del prompt, che vale 0.5 per costruzione dopo l'esclusione.
3. **Aggiunge rispetto alle baseline?** W e AUROC di p(UNKNOWN) a confronto con p(UNKNOWN) normalizzata, meno la p massima normalizzata, l'entropia normalizzata e la risposta generata UNKNOWN (0/1). Il confronto è **descrittivo**: per i modelli nuovi non c'è un test preregistrato di superiorità sulle baseline. Se lo vuoi, va fissato prima del completo (per esempio ΔW con IC appaiato, come HM2).

**Anomalie.** Il notebook elenca in `anomalie.csv` ciò che segnala in automatico: coppie escluse per lunghezza, ALTRO > 5%, massa bassa > 5% delle righe, un'etichetta mai generata, soglia di competenza non superata, differenza di W fra famiglie ≥ 0.20 (soglia descrittiva del Test M), una baseline che eguaglia o supera p(UNKNOWN), Qwen non allineato. Ogni anomalia nasce **DA CLASSIFICARE**, con le categorie possibili indicate (comportamento del modello, problema tecnico, limite del protocollo, evidenza scientifica). Le colonne vuote per la causa ipotizzata, i controlli effettuati e ciò che resta incerto vanno compilate a mano. Il notebook non attribuisce cause.

## 5. Regole approvate da Simona (14 nov, 09:19) e verifiche aggiunte nella v2

1. **Copertura minima: 760 coppie valide su 800 (95%).** Sotto questa soglia l'esito è DESCRITTIVO. La soglia di competenza si calcola sui B delle coppie tenute. Per le coppie escluse la v2 aggiunge tre elementi:
   - l'**elenco** completo (`esclusioni.distorsione.elenco`, `scarti_lunghezza.csv`);
   - un **controllo di distorsione**, con la quota di escluse per famiglia, variante, posizione e gold dei B e il numero di storie coinvolte. Un gruppo con almeno 5 escluse e una quota più che doppia di quella complessiva diventa un'anomalia «esclusioni concentrate»;
   - una **sensibilità**, cioè il W calcolato anche includendo le coppie escluse. Uno scarto ≥ 0.02 dal W principale diventa un'anomalia. Il dato è solo descrittivo e non cambia l'esito.
2. **Confronto con le baseline solo descrittivo**, senza test di superiorità. Il rapporto non potrà dire che p(UNKNOWN) è statisticamente superiore alle baseline.
3. **Rimozione di `token_type_ids`, solo come adattamento tecnico.** Per ogni modello e su tutti i prompt, il notebook confronta il tokenizer adattato con uno caricato da zero alla stessa revisione: stesso testo dopo il chat template, `input_ids` e `attention_mask` identici, prompt congelato presente intatto nel testo passato al modello. Se un solo prompt differisce, il modello è NON MISURABILE. Per Qwen3-8B si registra se il suo tokenizer prevedeva `token_type_ids`; il controllo dei 24 valori del Test U2 si fa con il tokenizer adattato.
4. **Controllo su CPU dei 4 W del Test U2 (cella 4b), obbligatorio prima del completo.** Il notebook legge `testU2_risultati.zip` da MyDrive, controlla lo SHA-256 del `punteggi.csv` (`9701dce0…`) e ci applica la propria analisi. Deve ridare esattamente W 0.975, 0.7825, 0.69375 e 0.74625, i conteggi dei B corretti per gold della PR #3 e CONFIRMED per tutti e 4. In modalità completo, se il controllo non è superato, la cella 6 si ferma prima di caricare qualsiasi modello. Il risultato è salvato in `controllo_cpu_testU2.json`.
5. **Identità delle coppie B/C fra i modelli.** Ogni modello registra le impronte dei prompt congelati (dati e benchmark), quella dei testi effettivi passati al modello e quella dell'insieme delle coppie valide. Il riepilogo controlla che tutti i modelli abbiano ricevuto gli stessi prompt, conta le coppie valide comuni a tutti e riporta il W di ciascun modello su quelle coppie comuni (descrittivo).
6. **Token.** `GH_TOKEN` e `HF_TOKEN` si leggono solo dai Secrets. Il token GitHub passa a git solo come variabile d'ambiente del processo (intestazione HTTP): non compare nell'URL, negli argomenti, in `.git/config` o in `FETCH_HEAD`, che viene comunque cancellato. Ogni messaggio di errore passa da `nascondi()`, che toglie i token noti prima di stamparlo o salvarlo.
8. **Baseline «p(UNKNOWN) normalizzata» (decisione di Simona, 14 nov 15:38, prima dei dati del completo).** La baseline resta nel confronto e viene spiegata, non tolta. È p(UNKNOWN)/(p(YES)+p(NO)+p(UNKNOWN)). Quando la massa sulle tre risposte è circa 1, coincide con p(UNKNOWN): nella prova la massa minima era 0.997 per entrambi i modelli. Una parità con questa baseline è quindi attesa e **non è un'anomalia del metodo**. Per questo:
   - la segnalazione «una baseline eguaglia o supera p(UNKNOWN)» usa solo le baseline indipendenti (entropia, meno p massima, risposta UNKNOWN 0/1);
   - c'è una segnalazione propria quando la normalizzata differisce da p(UNKNOWN) di almeno 0.02 in W. In quel caso la massa fuori dalle tre risposte conta, ed è un fatto da classificare;
   - la stessa spiegazione è scritta nel rapporto (`NOTA_NORMALIZZATA`), così un lettore esterno trova il motivo accanto al numero.

   Origine: nella prova la regola v2 aveva segnalato per Qwen «1.000 contro 1.000» con questa baseline. È stata classificata come limite della regola di segnalazione, non come comportamento del modello. La regola cambia solo per questa baseline; i dati della prova restano archiviati come prodotti dalla v2.
7. **Altre regole (invariate dalla v1).** Controllo positivo Qwen3-8B: 24 valori entro 1e-3 e, nel completo, W 0.975 entro 0.005. Cautela se più del 5% delle righe ha massa < 0.90.

## 6. Controlli fatti prima della consegna (CPU, senza GPU)

- **Prova e completo con un modello Llama finto** (casuale, minuscolo): tutte le celle girano. Ci sono checkpoint ogni 50 righe, ZIP per modello e ZIP finale. Quando si rilancia, il modello già completato viene saltato.
- **Cella 4b sul vero `testU2_risultati.zip`:** SHA-256 corrispondente, W identici ai 4 attesi, conteggi per gold identici, 4/4 CONFIRMED.
- **Tokenizer finto che restituisce `token_type_ids`:** dopo la rimozione, 0 prompt su 1600 con tokenizzazione diversa. Con due istanze di tokenizer davvero diverse, il controllo le ha rilevate e ha fermato il modello come NON MISURABILE.
- **Esclusioni:** sui punteggi archiviati di Mistral ho reso 30 coppie IMPLIES/NOT di lunghezza diversa. Il notebook le ha escluse, ha segnalato la concentrazione (IMPLIES 30/264) e ha calcolato il W di sensibilità (0.795 senza le escluse, 0.7825 con tutte). Se tutte le coppie sono escluse, il modello è NON MISURABILE e non si arresta.
- **Template con `strftime_now` o assente:** il modello viene fermato come NON MISURABILE.

Non verificato: il comportamento reale dei 5 modelli su GPU e le versioni di transformers in Colab. Il controllo positivo Qwen serve a questo.

## 7. Esito della prova v2 (14 nov 15:16, A100-SXM4-40GB, transformers 5.22.1, torch 2.14.1)

- **Controllo Qwen3-8B:** 24 valori con scarto massimo 8e-17, risposte uguali 24 su 24.
- **Tokenizer:** nessuno dei due modelli usava `token_type_ids`. Tokenizzazione identica e prompt intatti su 72 prompt su 72.
- **Coppie:** nessuna esclusione per lunghezza, 36 coppie su 36, prompt identici fra i modelli.
- **Uscite:** nessuna risposta ALTRO, massa ≥ 0.997. Soglia di competenza superata da entrambi; Gemma ha 0.97 sui B.
- **Controllo CPU 4b:** non eseguito, perché `testU2_risultati.zip` non era in MyDrive. L'archivio caricato poi da Simona è quello atteso (SHA-256 dello ZIP `dbcd61fa…`, del `punteggi.csv` `9701dce0…`).
- **Anomalie della prova:** Qwen, parità con la normalizzata, è un limite della regola, corretto nella v3. Gemma, differenze fra famiglie e meno p massima sopra p(UNKNOWN), è un'evidenza possibile da valutare solo nel completo: 12 coppie per famiglia non bastano.

## 8. Prima del lancio

- **Archivio del Test U2** in MyDrive: `testU2_risultati.zip` (una copia sola; percorso in `ARCHIVIO_TEST_U2`).
- **Secrets di Colab** con «Accesso al notebook» attivo: `GH_TOKEN` (token GitHub fine-grained, sola lettura dei contenuti di `Sva76/indet-bench`) e `HF_TOKEN`. Per Gemma bisogna accettare la licenza sulla pagina del modello.
- **Commit fissato `c086e65`.** Si trova sul ramo della PR #3. Se quel ramo viene riscritto, va aggiornato `REPO_COMMIT` con una nuova versione del notebook.
- **Tempi.** Inferenza di 1600 righe per modello: stimo 10–20 minuti su A100, più il download dei pesi (circa 16–30 GB per modello). È una stima, non una misura.
