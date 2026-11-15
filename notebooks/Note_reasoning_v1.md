# Note al notebook `IndetBench_reasoning_v1.ipynb` (R-notebook-1)

15 novembre 2026. Il notebook esegue il **Protocollo parte B v1**, approvato da Simona alle 14:11 con le 5 scelte raccomandate. Queste note elencano i dettagli di attuazione che il protocollo non fissava. Li segnalo perché tu possa controllarli prima della prova. Nessuno cambia le regole del protocollo.

## 1. Che cosa resta identico alle parti precedenti

- Benchmark congelato, set PN, prompt invariati, `export_rows("PN")`.
- Repository al commit `2aa1f62`, con lo stesso calcolo di W, soglia e report di `c086e65`.
- `report` con soglia di competenza vincolante, baseline descrittive, tre livelli, anomalie DA CLASSIFICARE, controllo CPU dei 4 W del Test U2 obbligatorio prima del completo.
- Etichette: le stesse 6 varianti di `hr.token_label_ids`, senza rinormalizzare.

## 2. Dettagli di attuazione (da controllare)

1. **Risposta dopo `</think>` in modo greedy.** Il campionamento con i parametri degli autori riguarda solo il ragionamento. Dopo `</think>` la risposta (16 token) è greedy, come nel Test U2. La misura è al primo token generato che non sia solo spazio o a capo. Così, dato il ragionamento, la misura è deterministica.
2. **Qwen3-32B a batch 4, non 16.** Con 16 sequenze da circa 4300 token, la cache (circa 18 GB) più i pesi (circa 66 GB) supera gli 80 GB della GPU. Gli altri modelli usano batch 16. Il batch è registrato nel manifest.
3. **Fine del ragionamento senza `</think>`.** Se il modello termina (fine sequenza) senza chiudere il ragionamento, il notebook applica la stessa chiusura forzata del budget. La riga è marcata `fine senza </think>` e non conta fra le coppie «chiuse da sole».
4. **`</think>` deve essere un token singolo.** Se non lo è, la fine del ragionamento non si può identificare in modo sicuro e il modello è NON MISURABILE per motivo tecnico. Per Qwen3 è il token 151668.
5. **Seme.** Ogni batch usa il seme 20261108 più l'indice del batch, e l'ordine delle righe è fisso. Se la sessione cade, la ripresa rifà gli stessi batch con gli stessi semi. Sulla CPU, con il modello finto, la ripresa ha dato punteggi identici. Sulla GPU l'identità bit per bit non è garantita.
6. **Regola sulla massa.** La regola si controlla sulle 24 righe V2001–V2003 appena il primo blocco è salvato, e poi sull'insieme completo. Se non è superata, la condizione accesa è NON MISURABILE e si ferma. La condizione spenta di Qwen resta comunque analizzata.
7. **Condizione spenta contro il Test U2.** Oltre al controllo di pipeline sui 24 valori (regola §5.1), il notebook confronta tutte le 1600 righe spente di Qwen3-8B con il Test U2. Il confronto è solo descrittivo: scarto massimo e risposte uguali.
8. **Parametri di generazione.** I parametri vengono passati esplicitamente alla generazione, così prevalgono sulla `generation_config` del modello. Questa resta comunque registrata nell'esito.
9. **Ripetibilità nella prova.** Nella prova si ripetono solo 2 storie, per provare il codice. Nel completo si ripetono 20 storie, come da protocollo.
10. **Uscite.** I ragionamenti completi sono in `ragionamenti.csv`, i punteggi in `punteggi.csv` (con `chiusura`, `ragionamento_token`, `posizione_risposta`, `seme`, `batch`). HR2 e la ripetibilità sono in `esito.json` e in `rapporto.txt`.

## 3. Controlli fatti (CPU, modello finto)

- Il controllo CPU dei 4 W del Test U2 è superato.
- Il percorso completo della prova funziona: le condizioni spenta e accesa, la ripetibilità, HR2 e lo ZIP.
- Le chiusure registrate coprono tutti e tre i casi: naturale, budget e fine senza `</think>`.
- La regola sulla massa funziona: con massa mediana 0.108 la condizione accesa è NON MISURABILE e la spenta resta analizzata.
- Il controllo della pipeline funziona: nel completo, se non è superato, il notebook si ferma prima di generare.
- La regola di copertura funziona: con 208 coppie chiuse da sole il risultato diventa DESCRITTIVO.
- La ripresa dopo la cancellazione di un blocco dà punteggi identici.
- Anche Qwen3-32B, Phi-4-reasoning e R1-Distill girano nel modo di prova.

**Non provato:** i modelli veri sulla GPU. In particolare restano da vedere:
- il comportamento dei template di Phi-4-reasoning e R1-Distill;
- la lunghezza reale dei ragionamenti;
- i tempi.

Lo verificano la prova e il controllo della pipeline.

## 4. Prima del lancio

- Sessione **A100-SXM4-80GB** (controlla con `!nvidia-smi`) e `testU2_risultati.zip` in MyDrive.
- **Prova:** `MODALITA = "prova"`, `MODELLI = ["qwen3_8b"]`. Riporta il tempo misurato e la stima per il completo.
- **Completo**, solo dopo la verifica della prova: `["qwen3_8b", "qwen3_32b", "phi4_reasoning"]`, più `"r1_llama_8b"` se vuoi il modello facoltativo.
