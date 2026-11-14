# Step 1, riepilogo (v3, approvato l'8 novembre)

Progetto: indeterminatezza logica negli LLM, verso un metodo e una libreria Python (ispirazione: lm-polygraph).
Modelli: Qwen3-8B e Mistral-Nemo-Instruct-2407 su tutti i test; OLMo-2-7B-Instruct solo sul test 4; Llama 3.1 8B non ancora.
Dettagli e numeri completi nei file `Risultati_test*` di questa cartella e in `test7_risultati/`.

## In breve
Una sonda sugli stati interni distingue bene le coppie B/C nelle condizioni del test 5. Il test 7 è esplorativo perché le formulazioni lasciate fuori dall'addestramento della sonda erano già state esaminate nel test 6. In questo test il rilevatore con stati supera il criterio rispetto alle baseline sulle uscite in un solo giro su sei, con Qwen sulla prosa. Il criterio per avviare il test 8 resta quindi non raggiunto. Le coppie B/C e il protocollo di trasferimento costituiscono un metodo riutilizzabile per valutare altri rilevatori.

Tra le misure sulle sole uscite, p(UNKNOWN) grezza (la probabilità della risposta UNKNOWN, senza addestramento) è la migliore baseline in 4 giri su 6 del test 7.

## Che cosa abbiamo distinto
- **A:** tutti i valori sono singoli.
- **B:** un dato ha due valori, ma la risposta resta determinata.
- **C:** i due valori portano a risposte opposte, quindi la risposta corretta è UNKNOWN.

Dal test 5 in poi B e C sono **coppie minime**: stessa storia, stessa riga incerta, cambia solo il valore di un'altra variabile. In ogni storia ci sono due versioni della regola, con e senza NOT, così il valore di quella variabile da solo non predice l'etichetta.

## Risultati per test
| Test | Domanda | Risultato |
|---|---|---|
| 4 + diagnostica | Il rilevatore SQuAD riconosce i casi C? | No. Funziona su SQuAD (H4a confermata su 3 modelli), ma sulle storie non separa C da B (AUROC 0.46–0.57). Il punteggio sale quando una variabile ha due valori ("x = a or b"): B > A nel 100% delle coppie su Mistral, 90% su Qwen, 53% su OLMo. Su Qwen è legato anche alla lunghezza del prompt (Spearman +0.49…+0.62). I modelli non rispondono mai UNKNOWN sui C (0/60). |
| 5 | A parità di storia, gli stati separano C da B meglio delle uscite? | La sonda da sola separa C da B: W 0.975 su Qwen, 0.983 su Mistral (H5a). La regressione con gli stati batte la regressione unica sulle sole uscite (H5b): ΔW +0.142 su Qwen (0.825 → 0.967) e +0.083 su Mistral (0.900 → 0.983). Su Qwen il guadagno viene da OR NOT. In un controllo esplorativo fatto dopo la run, una regressione sulle uscite per famiglia e variante ordina 120 coppie su 120 senza stati, su entrambi i modelli. Posizione: confermata su Qwen, non conclusiva su Mistral. Polarità: vedi sotto. |
| 6 | La sonda trasferisce a formulazioni nuove (operatori nuovi, prosa)? | Senza ricalibrazione, su operatori nuovi no: W 0.50 su Qwen e 0.44 su Mistral, con il segno che si inverte per operatore e, su Mistral, per posizione. Sulla prosa Qwen guadagna +0.168 sulla baseline per cella (quasi tutto da OR NOT), Mistral +0.005. p(UNKNOWN) grezza dà 0.901 e 0.828. Su Mistral p(UNKNOWN) (0.828) batte U + stati (0.690; H6e, ΔW −0.138). B2 + stati è un altro confronto e arriva a 0.868, sopra p(UNKNOWN) di +0.040 [−0.005, +0.085], quindi non conclusivo. Controllo esplorativo con ricalibrazione in dominio: su Qwen V1, aggiungere il punteggio della sonda addestrata su ADD alla baseline per cella ricalibrata porta W da 0.795 a 0.968; su Mistral le uscite ricalibrate arrivano già a 0.99. |
| 7 (esplorativo) | Addestrare su più formulazioni rende la sonda stabile e utile? | Nessun giro passa su entrambi i modelli, e il criterio per il test 8 non è soddisfatto. Unico giro che passa: Qwen, ADD + V1 → prosa (0.985, contro 0.920 di U2); non si replica su Mistral (0.599, contro 0.828 di p(UNKNOWN)). Negli altri giri la sonda allo strato scelto è vicina al caso, con celle a segno invertito. p(UNKNOWN) grezza è il riferimento più forte in 4 giri su 6. Descrittivi sotto. |

### Test 7, descrittivi (da leggere con cautela)
- **Sostituzione ADD → V1.** A parità di 120 storie di addestramento, sostituire metà delle ADD con V1 porta la sonda di Qwen su V2 da 0.812 a 0.979, e abbassa quella di Mistral da 0.690 a 0.597 in media (estrazioni molto variabili, 0.449–0.756). Il confronto misura l'effetto di quella sostituzione; il beneficio della varietà in generale resta da isolare.
- **Strato per strato.** Il segnale varia con modello, giro e strato. Escluso Qwen G1, il valore più alto è 0.700 (Mistral G1, strato 20; 0.609 allo strato scelto); Qwen G3 arriva a 0.604 allo strato 24. Su G2 il massimo è 0.53 in entrambi i modelli.
- **Coseno tra le direzioni.** Anche qui dipende da modello, coppia di giri e strato. Spesso è tra 0.1 e 0.4. Tra il test 6 (solo ADD) e G3 (V1 + V2, nessuna storia in comune) è circa 0. Valori più alti dove gli addestramenti condividono dati: Mistral G2~G3 0.6–0.75 (condividono V2), Qwen test 6~G1 fino a 0.68 (condividono ADD). Allo strato 36 di Qwen i coseni sono vicini a +1 o −1, con segni alternati. Un'ipotesi è che poche dimensioni con deviazione standard quasi nulla dominino la direzione riportata nello spazio originale; va verificata prima di attribuire il risultato a un artefatto.
- **Fuori dai giri, con la sonda di G1.** V3 (numerici): sonda 0.967 su Qwen e 1.000 su Mistral; p(UNKNOWN) 1.000 su entrambi. POL "granted": la sonda supera p(UNKNOWN) in entrambi i modelli (Qwen 0.890 contro 0.740, Mistral 0.860 contro 0.520).

## Le domande iniziali
| Domanda | Stato |
|---|---|
| Quali pattern fanno scattare l'allarme | Per il rilevatore SQuAD: una variabile con due valori ("o"). Non è isolato come parola singola; il controllo è proposto sotto. |
| Incertezza all'inizio della domanda | La posizione della riga incerta conta poco su Qwen (H5c confermata), è non conclusiva su Mistral, e nel test 6 su Mistral inverte il segno della sonda in alcune celle. |
| Bidirezionalità | Non ancora valutabile in modo affidabile. Nel test 5 l'esito formale di H5d su Qwen è non confermata (0.483 e 0.508); la risposta fissa NO sui casi B/C con domanda negata ne limita l'interpretazione. Mistral supera formalmente H5d (0.725 e 0.833), ma le sue risposte sono fortemente sbilanciate verso YES (874 dei 960 prompt B/C con domanda negata). Nel test 6 nessuna variante negata supera lo screening in entrambi i modelli, quindi H6d è non valutabile. |
| Campione piccolo o effetto reale | L'effetto in dominio è reale: bootstrap per storia, e per H5a una permutazione che ripete tutta la procedura (scelta dello strato, CV annidata, sonda). Per i confronti con le uscite (H5b, test 6, test 7) la permutazione è in modo "sonda": si scambiano le etichette solo per riaddestrare la sonda, mentre le regressioni sulle uscite conservano le etichette vere. Il vantaggio sulle uscite non regge al cambio di formulazione. |
| Bias e falle matematiche | Corretti lungo la strada: standardizzazione solo su dev, bootstrap per storia, scelta dello strato rifatta con le etichette permutate, baseline per cella, p(UNKNOWN) grezza come riferimento. |
| Llama e altri open-weights | Non ancora. Regola fissata: un modello entra nei test successivi solo se conferma H5a. |
| Allucinazioni | Non ancora: è il punto C. |

## Che cosa significa per la libreria
1. **p(UNKNOWN) come segnale dalle uscite.** È la migliore baseline sulle sole uscite in 4 giri su 6 del test 7. Su V3 ordina tutte le coppie B/C in entrambi i modelli, mentre i modelli generano UNKNOWN in 3 casi C su 240 (Qwen) e 0 su 240 (Mistral). È una differenza osservabile tra il punteggio e la risposta generata. Cautele: in V3 B e C differiscono nei numeri; W misura l'ordine dentro la coppia, non una soglia fissa; su POL "granted" la sonda fa meglio di p(UNKNOWN).
2. **Le sonde vanno validate come rilevatori**, non solo come classificatori in dominio: coppie minime, baseline sulle uscite forti e ricalibrate, prova su formulazioni lasciate fuori, stabilità del segno per cella. Questo protocollo è esso stesso un contributo metodologico.
3. **Una sonda "universale" sullo stato finale non è giustificata da questi dati.** Nel test 7 l'addestramento su più formulazioni non l'ha resa stabilmente trasferibile. Se la libreria offre sonde, deve offrire anche la procedura per validarle.
4. **Benchmark di astensione.** Nei formati simbolici i modelli non generano quasi mai UNKNOWN quando dovrebbero, ma p(UNKNOWN) ordina bene i casi. È un problema misurabile, utile anche a chi sviluppa i modelli.

## Controlli aperti proposti
- **La "o":** inserire "or" in storie in cui non crea due valori (per esempio in un fatto irrilevante, o in un nome) e vedere se il rilevatore SQuAD sale lo stesso. Richiede inferenza breve (circa 15 minuti per modello).
- **Polarità:** cercare una formulazione negata che i modelli eseguano davvero (lo screening attuale fallisce su entrambi).
- **OLMo e Llama:** solo sulle uscite (benchmark di astensione), insieme ai due controlli precedenti, in un unico notebook sui 4 modelli.

## Passo successivo proposto
Il notebook sulle uscite per i 4 modelli; poi il punto C (allucinazioni con contesto, RAG/SQuAD), con lo stesso protocollo di validazione.

## Confronto con metodi esistenti (aggiunto l'8 novembre)
Il test 7 ha trovato un vantaggio rispetto alla migliore baseline sulle uscite in uno solo dei sei giri. È una base concreta per proporre un benchmark Python riutilizzabile. Il valore di un nuovo rilevatore resta invece da dimostrare. Il confronto più informativo è far girare sulle stesse coppie B/C metodi già pubblicati:
- una sonda già pubblicata sugli stati interni;
- i rilevatori di SIRIN (Sber AI Lab, open source, Apache 2.0): sonde white-box, giudici solo testo e stime di incertezza tramite LM-Polygraph. SIRIN include anche la verifica dell'"answerability" (se il contesto basta per rispondere), che è molto vicina alla distinzione tra B e C.

Così si può mostrare a un ricercatore che cosa le coppie B/C rivelano sui metodi che ha già a disposizione. Da fare dopo il Test U, insieme al punto C.
Fonti: [SIRIN, arXiv 2608.00033](https://arxiv.org/pdf/2608.00033), [codice](https://github.com/sb-ai-lab/SIRIN).
