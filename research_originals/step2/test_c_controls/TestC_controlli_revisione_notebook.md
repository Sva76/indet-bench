# Test C · verifica del notebook di controllo

Data: 13 novembre 2026. Notebook esaminato: `TestC_controlli_v1.ipynb`. Notebook revisionato: `TestC_controlli_v1_revisionato.ipynb` (`VERSIONE = C-controlli-1a`).

## Esito

**Idoneo a essere lanciato come controllo supplementare su Colab**, utilizzando la copia revisionata. Questo è un controllo statico e di ricalcolo CPU: **non costituisce un test GPU end-to-end** di LM-Polygraph, SemanticEntropy o PTrue.

### Verifiche eseguite

- ZIP interno `testC_completo_risultati.zip` del completo caricato: impronta SHA-256 `cc89298c7372e6f52bd9db495678d036769ba0b4f3f085b32d0cbe3bd63fe1a3`, uguale a quella bloccata nel notebook. Lo ZIP esterno `completo-20261113T082301Z-1-001.zip` ha invece un'altra impronta e **non va sostituito al file interno** nel percorso configurato.
- Sorgenti Python del notebook revisionato compilate staticamente, notebook JSON/nbformat valido.
- Ricalcolo indipendente degli esiti del completo, con gli stessi dati, criteri e `N_BOOT=2000`: **38/38 voci identiche** a `esiti_C.json`.
- R3 su risultati reali con bootstrap ridotto per controllo funzionale: **20 casi LOG scelti**, cinque per modello, 20 passaggi distinti; nessuna risposta del modello o risposta attesa visibile nel foglio di rilettura.
- Foglio `campione_classificazione_Simona.xlsx`: 100 risposte da classificare, categorie con menu a tendina, chiave automatica non presente nel file.

### Correzioni nella copia revisionata

1. **TriviaQA con identificativi duplicati:** l'abbinamento fra testi, lunghezze e giudizio corretto/errato avviene per posizione; la vecchia versione sovrascriveva alcune corrispondenze in un dizionario indicizzato per `row_id`.
2. **Gate della riproduzione:** se 38/38 non coincide, l'analisi non prosegue.
3. **Troncamento:** se la rigenerazione non conserva il prefisso originario, non viene utilizzata per cambiare la categoria della risposta; il caso resta segnalato come non confrontabile.
4. **Rilettura LOG:** le risposte attese e generate dal modello sono escluse dal foglio da compilare per ridurre il condizionamento. Restano nei dati originali del completo.
5. Cambio etichetta versione da `C-controlli-1` a `C-controlli-1a`, per distinguere la procedura revisionata dall'originale.

### Valutazione delle regole

- **R1:** approvata come criterio conservativo per il Test C, che può invalidare controlli precedenti ma non promuovere nuovi metodi alla conferma preregistrata. La soglia 0,70 resta quella fissata.
- **R2:** approvata come analisi di sensibilità e non come modifica retroattiva del completo.
- **R3:** soglia **3/20** approvata **solo per segnalare un possibile problema da approfondire**. Un esito 0–2/20 non dimostra statisticamente l'assenza di difetti LOG.

### Prima del lancio

- Drive: `MyDrive/testC_parziali/completo/testC_completo_risultati.zip` deve avere lo SHA-256 indicato sopra. È **lo ZIP interno**, non il file esportato esterno.
- Drive: `MyDrive/testM_parziali/completo/dati/triviaqa.json` deve essere presente e coincidere con l'impronta fissata nel notebook (`d102809d…`). Non è stato possibile verificarne la presenza su Drive da questa sessione.
- Google Colab: A100, secret `HF_TOKEN` abilitato, `AVVIA_GPU=True`, eseguire tutte le celle.
- Dopo il run: verificare 4/4 lavori `ESEGUITO`, 38/38 riproduzioni, nessuna voce nella sezione `ERRORI NELL'ANALISI`, registrare i casi senza prefisso uguale e il conteggio di risposte ancora troncate a 96 token.
- Conservare la revisione manuale delle 100 risposte distinta dal codice di generazione; non aprire la chiave prima di completarla.
