# Test U (uscite, 4 modelli): protocollo v2

Data: 8 novembre 2026. Stato: **scelte approvate da Simona (8 novembre), nessun dato ancora raccolto**. Notebook: `TestU_astensione_4_modelli_v3.ipynb`.
Riferimento: `PHI/Step1_verifica/Riepilogo_Step1.md` (v3, approvato).

## 1. Perché questo test
Lo Step 1 ha mostrato che le sonde sugli stati non trasferiscono in modo stabile, e che tra le misure sulle uscite p(UNKNOWN) grezza è il riferimento più forte in 4 giri su 6 del test 7. Per una libreria serve sapere **per quali formati e per quali modelli** p(UNKNOWN) funziona, su storie nuove e su modelli nuovi.

I dati già raccolti indicano che il segnale **non è uniforme**. Su Qwen e Mistral, nel test 6, p(UNKNOWN) grezza dà W 1.000 sui numerici (V3) e 0.90 e 0.83 sulla prosa (V2). Sugli operatori nuovi (V1) dà invece solo 0.52 e 0.64, e sul template simbolico (POL "granted") 0.74 e 0.52. Il test deve quindi misurare dove il segnale regge, senza dare per scontato che regga ovunque.

Il test ha tre parti:
1. **Benchmark di astensione** (principale, solo uscite).
2. **Controllo della "o"** (principale per la domanda sui pattern). Usa gli stati interni solo per ricostruire il rilevatore SQuAD del test 4, senza addestrare nulla sulle storie.
3. **Polarità** (secondaria, solo uscite): cercare una domanda negata che i modelli eseguano davvero.

## 2. Modelli
| Modello | Revisione | Note |
|---|---|---|
| Qwen/Qwen3-8B | b968826d9c46… (come nei test 4–7) | `enable_thinking=False` |
| mistralai/Mistral-Nemo-Instruct-2407 | 04d8a90549d2… (come nei test 4–7) | |
| allenai/OLMo-2-1124-7B-Instruct | 470b1fba1ae0… (come nel test 4) | nel test 4 girava su L4, qui su A100 |
| meta-llama/Llama-3.1-8B-Instruct | si fissa quella del giorno della run e si annota | serve accettare la licenza su Hugging Face e un token (ti do i passi quando ci arriviamo) |

Tutti in bf16 su A100, decodifica greedy, prompt con il template di chat del modello. La regola "un modello entra solo se conferma H5a" vale per i test sulle sonde. Qui non si addestra nessuna sonda, quindi entrano tutti e quattro.

Per Qwen e Mistral il test è una **replica su storie nuove**: i formati sono quelli del test 6, già esaminati. Per OLMo e Llama i formati sono nuovi.

## 3. Dati
Lo stesso generatore del test 6, con un **seme nuovo (20261120)**. Le storie sono quindi nuove, ma il formato è lo stesso. Le coppie B/C restano minime: stessa riga incerta su `a`, cambia solo `b`, con due versioni della regola (con e senza NOT) bilanciate in ogni storia.

| Insieme | Contenuto | Storie | Prompt |
|---|---|---|---|
| ADD | template simbolico, AND / OR / IMPLIES | 120 | 1440 |
| V1 | stesso template, operatori NOT(a AND b), NOT(a OR b), b IMPLIES a | 200 | 2400 |
| V2 | stessi operatori di ADD, tutto in prosa | 200 | 2400 |
| V3 | numerici (at least / at most), B e C differiscono nei numeri | 60 | 720 |
| O | controllo della "o", vedi §5 | 120 | 1440 |
| SCR | screening della polarità, solo A e B, 3 candidati | 60 | 720 |
| POL | template ADD, "granted" + il candidato scelto | 100 | fino a 1200 |
| SQuAD | le 600 domande di addestramento e le 400 di verifica del test 4 (stessa selezione) | | 1000 |

Prima dell'inferenza si controlla la lunghezza in token. In ADD, V1, V2, O e POL le coppie confrontate devono avere esattamente lo stesso numero di token; le coppie che non lo rispettano si scartano e si contano, come nel test 6.

Per ogni prompt si salvano la risposta generata (8 token, greedy), la risposta letta (YES / NO / UNKNOWN / ALTRO) e la massa di probabilità sul primo token delle tre etichette (stesse varianti di scrittura dei test precedenti). Se la massa totale è sotto 0.90 per più del 5% dei prompt di un modello, lo si segnala e quel modello si legge con cautela.

## 4. Parte 1: benchmark di astensione
### Misure (per modello × insieme)
- **Astensione generata:** quota di UNKNOWN generato sui C (sensibilità) e sui B (falsa astensione); accuratezza su A e B.
- **p(UNKNOWN) grezza:** W sulle coppie B/C (mediato per storia, come sempre) e AUROC C contro B. Nessun addestramento.
- **Scarto tra punteggio e risposta:** W di p(UNKNOWN) solo sulle coppie in cui il modello **non** ha generato UNKNOWN sul C. Misura quanto il punteggio ordina i casi anche quando il modello non si astiene.
- **Soglia trasferita:** si fissa una soglia τ su p(UNKNOWN) usando solo ADD (quella che massimizza l'accuratezza bilanciata tra C e A ∪ B) e la si applica senza cambiarla a V1, V2 e V3. Si confronta l'accuratezza bilanciata della regola "astieniti se p(UNKNOWN) > τ" con quella dell'astensione generata dal modello.
- **Descrittivi:** le stesse misure con probabilità massima ed entropia sulle tre etichette, per posizione e per famiglia × variante.

### Ipotesi preregistrate (ogni modello ha il suo esito)
- **HU1:** per ogni insieme ADD, V1 e V2, W(p(UNKNOWN)) > 0.5.
  CONFERMATA se il limite inferiore del bootstrap per storia (2000 ricampionamenti) è > 0.5 **e** W ≥ 0.60; NON CONFERMATA se il limite superiore è ≤ 0.5; altrimenti NON CONCLUSIVA. Su V3 è solo descrittiva, perché B e C differiscono nei numeri.
- **HU2:** su V1 e V2, ΔBA = BA(soglia da ADD) − BA(astensione generata) > 0.
  CONFERMATA se il limite inferiore del bootstrap è > 0 **e** ΔBA ≥ 0.05; NON CONFERMATA se il limite superiore è ≤ 0; altrimenti NON CONCLUSIVA.
- **Lettura per la libreria, fissata prima:** "p(UNKNOWN) è un segnale trasferibile nel formato F" si scrive solo se HU1 è confermata in F su almeno 3 modelli su 4. "Una soglia calibrata su un formato migliora l'astensione in un altro" si scrive solo se HU2 è confermata sullo stesso insieme su almeno 3 modelli su 4. Altrimenti si riporta il risultato per modello e formato, senza generalizzare.
- Per un punteggio non addestrato la permutazione delle etichette dentro la coppia equivale a girare il segno di ogni confronto. Si riporta come controllo (2000 giri, per storia), ma decide il bootstrap.
- Le ipotesi sono 4 modelli × (3 + 2) confronti. Non correggo per i confronti multipli, perché ogni esito si legge per modello e formato. La lettura per la libreria richiede però la concordanza di 3 modelli su 4.

## 5. Parte 2: controllo della "o"
### Il problema
Nel test 4 la "o" era la notazione stessa dei due valori ("x = false or true"). La parola e la presenza di due valori erano quindi confuse tra loro. Serve un disegno che le separi.

### Disegno (insieme O, template ADD, riga incerta in ultima posizione, domanda "granted")
In ogni prompt la riga della regola si chiude con una frase neutra: *"No other approval rule, written **and** unwritten, applies."* Nelle condizioni marcate "or" la frase diventa *"written **or** unwritten"*. Questa "or" non crea due valori.

| Condizione | Valori | Notazione dei due valori | Frase neutra |
|---|---|---|---|
| A_and | tutti singoli | | and |
| A_or | tutti singoli | | **or** |
| B_set | `a` ha due valori, risposta determinata | `a = false, true.` | and |
| B_or | come B_set | `a = false or true.` | and |
| C_set | `a` ha due valori, risposta UNKNOWN | `a = false, true.` | and |
| C_or | come C_set | `a = false or true.` | and |

L'istruzione dice già "Each listed value is allowed", quindi la lista con la virgola è coerente con il testo. "or" e "," sono di solito un solo token, quindi A_or/A_and e B_or/B_set hanno lo stesso numero di token. Lo si controlla per ogni modello, e le coppie diverse si scartano e si contano. Nella famiglia OR la regola contiene anche "OR" maiuscolo: la si riporta a parte.

### Rilevatore
È quello del test 4, ricostruito per ogni modello: direzione = media(senza risposta) − media(con risposta) sulle 600 domande SQuAD di addestramento, normalizzata, agli strati fissati nel test 4 (Qwen 23, 26, 30, 33; Mistral 12, 14, 17, 20, 23, 26; OLMo 11, 14, 17, 20, 23, 26; Llama con la stessa regola a frazioni usata per OLMo). Il punteggio è la proiezione sull'ultimo token, standardizzata strato per strato con media e deviazione standard delle 600 domande SQuAD, poi mediata sugli strati. Sulle storie non si addestra nulla.

### Ipotesi
- **HO1 (la parola):** W(A_or > A_and) sul punteggio del rilevatore, appaiato per storia × versione della regola. CONFERMATA ("il rilevatore reagisce alla parola 'or' anche senza due valori") se il limite inferiore del bootstrap è > 0.5 **e** W ≥ 0.60; NON CONFERMATA se il limite superiore è ≤ 0.5; altrimenti NON CONCLUSIVA. Un esito non confermato **non** prova l'assenza dell'effetto: dice solo che non lo rileviamo con questo campione.
- **HO2 (la notazione):** W(B_or > B_set), stessa regola. Chiede se, a parità di due valori, la parola nella notazione alza il punteggio.
- **Descrittivi:**
  - W(B_set > A_and) per i due valori senza la parola. Qui B_set ha 2 token in più, quindi c'è un possibile effetto della lunghezza, e su Qwen sappiamo che conta.
  - Le stesse tre misure su p(UNKNOWN).
  - Quota di UNKNOWN generato su C_set e su C_or: la notazione cambia l'astensione?
  - C contro B con il rilevatore (ripete il test 4 con coppie minime).

### Lettura fissata
- HO1 confermata: l'allarme è legato alla parola.
- HO1 non confermata con HO2 non confermata e W(B_set > A_and) alto: l'allarme è legato ai due valori, non alla parola.
- Gli altri casi si descrivono così come sono.

## 6. Parte 3: polarità (secondaria)
Nel test 6 nessuna domanda negata ha superato lo screening (P1 "Is approval refused?", P2 "Is approval not granted?", P3 con regola di rifiuto). Tre candidati nuovi, sul template ADD:
- **N1:** P1 con una definizione esplicita nella regola: *"Approval is refused exactly when it is not granted."*
- **N2:** N1 più un esempio svolto nell'istruzione, su una regola semplice con un solo valore per campo (nessun caso B o C).
- **N3:** come N1, con "denied" al posto di "refused".

**Screening (SCR, solo A e B, solo uscite):** vince il candidato con il minimo più alto tra l'accuratezza sui casi con risposta attesa YES e quella sui casi con risposta attesa NO, purché sia ≥ 0.90; a parità vince N1. È la stessa regola del test 6, applicata a ogni modello separatamente. Se nessun candidato passa, la polarità è NON VALUTABILE per quel modello.

**Se un candidato passa (POL):**
- **HP1:** W(p(UNKNOWN)) sulle coppie B/C con la domanda negata, con la stessa regola di HU1.
- **Descrittivo:** coerenza su A e B, cioè la quota di prompt in cui la risposta negata è l'inverso di quella "granted"; quota di UNKNOWN generato sui C.

È la versione "sulle uscite" della bidirezionalità: il segnale di astensione resta quando la risposta attesa si inverte?

## 7. Controlli di allineamento (prima delle ipotesi; se falliscono il notebook si ferma)
1. **Selezione SQuAD:** stessa impronta del test 4 (`5ac6e6e0…`).
2. **Rilevatore:** per Qwen, Mistral e OLMo, le proiezioni su 20 domande SQuAD fissate coincidono con quelle del test 4 (Pearson ≥ 0.999 per strato, valori scritti nel notebook: non serve caricare file). Spearman e differenza massima si riportano soltanto: su 20 punti basta lo scambio di due valori vicini per portare Spearman a 0.9985. Per OLMo la scheda è diversa (L4 → A100).
3. **H4a:** l'AUROC della direzione sulle 400 domande SQuAD di verifica è entro ±0.01 da quella del test 4.
4. **Uscite:** per Qwen e Mistral, 24 prompt del test 6 (rigenerati con il vecchio seme) riproducono p(UNKNOWN) entro 1e-3 (valori scritti nel notebook).
5. **Etichette:** i primi token di YES, NO e UNKNOWN non si sovrappongono. Per i tre modelli già usati coincidono con quelli del test 4.

## 8. Cosa non si può concludere
- W misura l'ordine dentro una coppia, non una soglia: per questo c'è HU2.
- Le storie sono sintetiche e in inglese. Un benchmark sulle storie non dice nulla, da solo, sulle allucinazioni con contesto (punto C).
- Un esito positivo sul rilevatore SQuAD in HO1 descrive questo rilevatore, non "gli stati interni" in generale.

## 9. Esecuzione su Colab
- Un solo notebook. I modelli girano uno dopo l'altro nella stessa sessione A100, e il modello si scarica dalla memoria tra uno e l'altro. **Dopo ogni modello i risultati si salvano su `MyDrive/testU_parziali/`**. Se la sessione cade, rilanciando si riparte dal modello successivo.
- Stati interni: solo per SQuAD e per l'insieme O, solo agli strati fissati e solo sull'ultimo token (pochi MB).
- **Tempo stimato:** 50–60 minuti di GPU per modello, quindi circa 4 ore per i quattro. L'analisi finale gira su CPU in 10–15 minuti. Si può lasciare in esecuzione in background (Colab Pro+).
- Llama richiede il token di Hugging Face nei Secrets di Colab (`HF_TOKEN`): se manca, il notebook salta Llama e lo dice, senza fermarsi.
- **Uscita:** `testU_risultati.zip` su Drive, con rapporto, esiti in JSON, tabella del benchmark (modello × insieme) e punteggi prompt per prompt.

## 10. Aggiunta facoltativa (descrittiva)
Una cella breve su CPU per la cautela sui coseni del test 7. Legge `test6_stati_Qwen3-8B.zip` da Drive e, allo strato 36, misura quanta parte della norma della direzione riportata nello spazio originale viene da dimensioni con deviazione standard molto piccola. Serve a verificare o scartare l'ipotesi dell'artefatto. Non decide nulla e si può togliere.

## Decisioni e precisazioni (8 novembre, prima della run)
1. **Soglie:** W ≥ 0.60 per HU1, HO1, HO2 e HP1; ΔBA ≥ 0.05 per HU2 (confermate da Simona).
2. **Lettura per la libreria:** almeno 3 modelli su 4 (confermata).
3. **Cella dei coseni (§10):** si tiene. Lettura fissata: l'ipotesi dell'artefatto è SOSTENUTA se allo strato 36 le 10 dimensioni con deviazione standard minima portano più del 90% della norma della direzione in ogni giro **e**, ricalcolati nello spazio standardizzato e senza quelle dimensioni, i coseni hanno |coseno| < 0.9 in tutte le coppie. È NON SOSTENUTA se la prima condizione non vale in nessun giro; altrimenti NON CHIARA. Se i coseni del test 7 non si riproducono (tolleranza 0.02) l'esito è NON VALUTABILE. La cella parte solo con `ESEGUI_COSENI = True`.
4. **HU2, intervallo:** bootstrap congiunto. In ogni replica si ricampionano le storie di ADD e si ricalcola la soglia, e si ricampionano in modo indipendente le storie di verifica. L'intervallo condizionato alla soglia fissa si riporta come descrittivo. A parità di accuratezza bilanciata su ADD si sceglie la soglia più alta.
5. **Insieme O:** si costruisce dalle storie di ADD (riga incerta in ultima posizione: 120 storie, 240 coppie) cambiando solo la frase neutra e la notazione. I confronti di HO1 e HO2 sono tutti dentro O.
6. **Esecuzione:** un prompt alla volta (nessun padding), come nei test 4–6, e versione di transformers già installata in Colab, registrata nel manifest. Circa 1 ora per modello.
7. **Descrittivo aggiunto:** astensione generata e mediana di p(UNKNOWN) per tipo × posizione della riga incerta. Nel test 6, su V2, l'astensione sui B è più alta con la riga incerta in fondo (Qwen 47% contro 14%, Mistral 70% contro 31%).
