# Step 1, riepilogo (da rivedere)

Progetto: indeterminatezza logica negli LLM, verso un metodo e una libreria Python (ispirazione: lm-polygraph).
Modelli: Qwen3-8B e Mistral-Nemo-Instruct-2407 su tutti i test; OLMo-2-7B-Instruct solo sul test 4; Llama 3.1 8B non ancora.
Dettagli e numeri completi nei file `Risultati_test*` di questa cartella.

## In una frase
Negli stati interni c'è un segnale leggibile dell'indeterminatezza logica dentro le formulazioni su cui la sonda viene addestrata. Il vantaggio di usarlo in un rilevatore, rispetto alle probabilità di uscita, non si è dimostrato su formulazioni nuove, nemmeno addestrando la sonda su più formulazioni (test 7). Il segnale più robusto e trasferibile è p(UNKNOWN), la probabilità che il modello si astenga, anche quando non lo fa.

## Che cosa abbiamo distinto
- **A:** tutti i valori sono singoli.
- **B:** un dato ha due valori, ma la risposta resta determinata.
- **C:** i due valori portano a risposte opposte, quindi la risposta corretta è UNKNOWN.

Dal test 5 in poi B e C sono **coppie minime**: stessa storia, stessa riga incerta, cambia solo il valore di un'altra variabile. In ogni storia ci sono due versioni della regola, con e senza NOT, così il valore di quella variabile da solo non predice l'etichetta.

## Risultati per test
| Test | Domanda | Risultato |
|---|---|---|
| 4 + diagnostica | Il rilevatore SQuAD riconosce i casi C? | No. Funziona su SQuAD (H4a confermata su 3 modelli), ma sulle storie non separa C da B (AUROC 0.46–0.57). Il punteggio sale quando una variabile ha due valori ("x = a or b"): B > A nel 100% delle coppie su Mistral, 90% su Qwen, 53% su OLMo. Su Qwen è legato anche alla lunghezza del prompt (Spearman +0.49…+0.62). I modelli non rispondono mai UNKNOWN sui C (0/60). |
| 5 | A parità di storia, gli stati separano C da B meglio delle uscite? | La sonda separa C da B: W 0.975 su Qwen, 0.983 su Mistral. Batte la regressione unica sulle uscite (ΔW +0.142 su Qwen, +0.083 su Mistral), ma una regressione per famiglia e variante arriva a 120/120 senza stati. Su Qwen il guadagno viene da OR NOT. Posizione: confermata su Qwen, non conclusiva su Mistral. Polarità: Qwen risponde sempre NO alla domanda negata. |
| 6 | La sonda trasferisce a formulazioni nuove (operatori nuovi, prosa)? | Su operatori nuovi no: W 0.50 su Qwen e 0.44 su Mistral, con il segno che si inverte per operatore e, su Mistral, per posizione. Sulla prosa Qwen guadagna +0.168 sulla baseline per cella (quasi tutto da OR NOT), Mistral +0.005. p(UNKNOWN) grezza dà 0.901 e 0.828, e su Mistral batte la combinazione con gli stati (−0.138). In dominio le uscite ricalibrate arrivano a 0.99 e la sonda non aggiunge nulla. |
| 7 (esplorativo) | Addestrare su più formulazioni rende la sonda stabile e utile? | No: nessun giro passa su entrambi i modelli, e il criterio per il test 8 non è soddisfatto. Unico successo: Qwen, ADD + V1 → prosa (0.985, contro 0.920 di U2); vale per la varietà, non per la quantità, ma non si replica su Mistral. Altrove la sonda resta al caso a tutti gli strati, con celle a segno invertito. Le direzioni dei vari addestramenti non coincidono (coseno 0.1–0.4). p(UNKNOWN) grezza è il riferimento più forte in 4 giri su 6. |

## Le domande iniziali
| Domanda | Stato |
|---|---|
| Quali pattern fanno scattare l'allarme | Per il rilevatore SQuAD: una variabile con due valori ("o"). Non è isolato come parola singola; il controllo è proposto sotto. |
| Incertezza all'inizio della domanda | La posizione della riga incerta conta poco su Qwen (H5c confermata), è non conclusiva su Mistral, e nel test 6 su Mistral inverte il segno della sonda in alcune celle. |
| Bidirezionalità | Non valutabile: nessuna formulazione negata viene eseguita (Qwen risponde NO, Mistral YES). |
| Campione piccolo o effetto reale | L'effetto in dominio è reale (permutazione completa, bootstrap per storia). Il vantaggio sulle uscite non regge al cambio di formulazione. |
| Bias e falle matematiche | Corretti lungo la strada: standardizzazione solo su dev, bootstrap per storia, permutazione che rifà tutta la procedura, scelta dello strato con le etichette permutate, baseline per cella, p(UNKNOWN) grezza come riferimento. |
| Llama e altri open-weights | Non ancora. Regola fissata: un modello entra nei test successivi solo se conferma H5a. |
| Allucinazioni | Non ancora: è il punto C. |

## Che cosa significa per la libreria
1. **p(UNKNOWN) come segnale.** La probabilità della risposta UNKNOWN contiene l'indeterminatezza anche quando il modello non la pronuncia. Sui numerici (V3) ordina tutte le coppie in entrambi i modelli, mentre UNKNOWN viene detto nello 0–1% dei casi C. Cautele: in V3 B e C differiscono nei numeri; e W misura l'ordine dentro la coppia, non una soglia fissa.
2. **Le sonde vanno validate come rilevatori**, non solo come classificatori in dominio: coppie minime, baseline sulle uscite forti e ricalibrate, prova su formulazioni lasciate fuori, stabilità del segno per cella. Questo protocollo è esso stesso un contributo metodologico.
3. **Una sonda "universale" sullo stato finale non è giustificata.** Nemmeno un addestramento più vario la rende trasferibile in modo affidabile (test 7). Se la libreria offre sonde, deve offrire anche la procedura per validarle.
4. **Benchmark di astensione.** Nei formati simbolici i modelli non dicono quasi mai UNKNOWN quando dovrebbero, ma p(UNKNOWN) ordina bene i casi: il modello "sa" ma non lo dice. È un problema misurabile, utile anche a chi sviluppa i modelli.

## Controlli aperti proposti
- **La "o":** inserire "or" in storie in cui non crea due valori (per esempio in un fatto irrilevante, o in un nome) e vedere se il rilevatore SQuAD sale lo stesso. Richiede inferenza breve (circa 15 minuti per modello).
- **Polarità:** cercare una formulazione negata che i modelli eseguano (lo screening attuale fallisce su entrambi).
- **OLMo e Llama:** solo sulle uscite (benchmark di astensione), insieme ai due controlli precedenti, in un unico notebook sui 4 modelli.

## Passo successivo proposto
Il notebook sulle uscite per i 4 modelli; poi il punto C (allucinazioni con contesto, RAG/SQuAD), con lo stesso protocollo di validazione.