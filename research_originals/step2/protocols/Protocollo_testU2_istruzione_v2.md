# Test U2 (istruzione e formato, 4 modelli): protocollo v2

Data: 9 novembre 2026. Stato: **v2 dopo la revisione di Simona, nessun dato raccolto**. Notebook: `TestU2_istruzione_4_modelli_v2.ipynb` (versione U2-v1-notebook-2).

Modifiche rispetto alla bozza v1: appaiamento per `pair_key` nei contrasti (§5); HI3 descritta come confronto fra due template (§5); lettura con quattro casi, perché HI1 e HI2 possono confermarsi insieme (§5).
Riferimenti: `Protocollo_testU_v2.md`, `Risultati_testU.md` (v2).

## 1. Perché questo test
Nel Test U, p(UNKNOWN) separa C da B in tutti e 4 i modelli solo in V2. È l'unico risultato che supera la regola dei 3 su 4. Però V2 cambia due cose rispetto ad ADD:
1. **il formato**: regola e fatti sono scritti in prosa invece che in notazione simbolica;
2. **l'istruzione**: contiene una frase che spiega la riga incerta, «When a fact says that something may be true or false, either case is possible and you are not told which».

Il Test U non può dire quale delle due conta. Prima di portare il risultato nella libreria serve separarle.

Anche l'istruzione simbolica di ADD contiene una spiegazione della riga con due valori: «Each listed value is allowed; one actual value per field is chosen independently from its allowed values». In questo test ogni formato tiene la propria frase di spiegazione, e il fattore è la presenza o l'assenza di quella frase.

## 2. Disegno: 2 × 2 sulle stesse storie
Le storie sono le **200 storie V2 del Test U**, rigenerate con lo stesso generatore e lo stesso seme (20261120): stesse famiglie (AND, OR, IMPLIES), stesse varianti (con e senza NOT), stessi nomi, stessi valori, stesse posizioni della riga incerta. Cambiano solo il formato e l'istruzione.

| Condizione | Formato | Spiegazione della riga incerta | Istruzione |
|---|---|---|---|
| **P+S** (= V2 del Test U) | prosa | sì | `Read the short policy and the facts below. When a fact says that something may be true or false, either case is possible and you are not told which. Answer with a single word on the first line: YES, NO or UNKNOWN.` |
| **P−S** | prosa | no | `Read the short policy and the facts below. Answer with a single word on the first line: YES, NO or UNKNOWN.` |
| **S+S** | simbolico (come ADD) | sì | l'istruzione di ADD: `Use only the supplied fictional policy and facts. Each listed value is allowed; one actual value per field is chosen independently from its allowed values. Return exactly one of YES, NO, UNKNOWN on the first line, with no explanation.` |
| **S−S** | simbolico | no | `Use only the supplied fictional policy and facts. Return exactly one of YES, NO, UNKNOWN on the first line, with no explanation.` |

In prosa la regola, i fatti e la domanda sono identici a V2 (`Policy: …`, `Facts: …`, «Is approval given?»). In simbolico sono identici ad ADD (`[R1]`, `[R2]`, `x = false or true.`, «Is approval granted?»). In tutte e quattro le condizioni UNKNOWN resta fra le risposte ammesse: si toglie solo la frase che spiega cosa significa la riga con due valori.

Ogni condizione ha 200 storie × 2 varianti × 3 tipi (A, B, C) × 2 posizioni = 2400 prompt, quindi 9600 per modello. Come nel Test U, le coppie B/C con lunghezze in token diverse si scartano e si contano.

## 3. Modelli e condizioni di esecuzione
Gli stessi del Test U, con le stesse revisioni: Qwen3-8B (`enable_thinking=False`), Mistral-Nemo-Instruct-2407, OLMo-2-1124-7B-Instruct e Llama-3.1-8B-Instruct (0e9e39f2). Si usano bf16, attention eager, decodifica greedy con 8 token e batch 1, con la versione di transformers installata in Colab. Le misure sono quelle del Test U: risposta generata, risposta letta, p(YES), p(NO), p(UNKNOWN) sul primo token e massa totale. Non servono gli stati interni né SQuAD.

Tempo stimato: circa 45–60 minuti per modello, cioè 3–4 ore per tutti e 4.

## 4. Controllo di allineamento (prima di ogni esito)
La condizione P+S coincide con V2 del Test U. Si verificano tre cose:
1. **Prompt identici:** l'hash dei 2400 prompt di P+S coincide con quello dei prompt V2 del Test U (valore scritto nel notebook).
2. **Valori identici:** per ogni modello, 24 valori di p(UNKNOWN) di V2 presi dal Test U (scritti nel notebook) si riproducono entro 1e-3.
3. **Stesso W:** il W di p(UNKNOWN) su P+S coincide con quello del Test U entro 0.005 (0.914, 0.834, 0.736, 0.839).

Se un controllo fallisce per un modello, quel modello si riporta come NON VALUTABILE e non entra nei conteggi.

## 5. Ipotesi preregistrate (ogni modello ha il suo esito)
W è la misura del Test U: la quota di coppie B/C in cui p(UNKNOWN) di C supera quello di B (pareggi a 0.5), mediata per storia, con IC al 95% da 2000 ricampionamenti delle storie.

- **HI1 (principale): la prosa senza spiegazione basta.** Su P−S, W > 0.5.
  CONFERMATA se il limite inferiore è > 0.5 **e** W ≥ 0.60; NON CONFERMATA se il limite superiore è ≤ 0.5; altrimenti NON CONCLUSIVA.
- **HI2: la spiegazione aiuta in prosa.** ΔW = W(P+S) − W(P−S) > 0.
  CONFERMATA se il limite inferiore è > 0 **e** ΔW ≥ 0.05; NON CONFERMATA se il limite superiore è ≤ 0; altrimenti NON CONCLUSIVA.
- **HI3: confronto fra i due template senza spiegazione.** ΔW = W(P−S) − W(S−S) > 0, con gli stessi criteri di HI2. P−S e S−S non differiscono solo per la notazione: cambiano anche l'istruzione di base e la domanda finale («given» contro «granted»). HI3 confronta quindi due template interi.

**Appaiamento nei contrasti (HI2, HI3 e descrittivi).** Le coppie B/C con lunghezze in token diverse si scartano separatamente in ogni condizione. Per non confrontare varianti o posizioni diverse della stessa storia, ogni contrasto usa solo le coppie con la stessa `pair_key` (stessa storia, variante e posizione) presenti in entrambi i bracci. L'interazione usa le coppie presenti in tutte e quattro le condizioni. La differenza si calcola coppia per coppia, poi si media per storia e si ricampionano le storie. Il W di ciascuna condizione (HI1 e il controllo di allineamento di P+S) resta calcolato su tutte le coppie valide di quella condizione.

**Lettura per la libreria, fissata prima (almeno 3 conferme su 4 modelli valutabili):**

| Esito | Cosa si scrive |
|---|---|
| HI1 e HI2 confermate in ≥ 3 | «In prosa p(UNKNOWN) supera il criterio anche senza la frase che spiega la riga incerta, e la frase migliora comunque W». |
| HI1 in ≥ 3, HI2 no | «In prosa p(UNKNOWN) supera il criterio anche senza la frase che spiega la riga incerta; un miglioramento dovuto alla frase non è confermato». |
| HI2 in ≥ 3, HI1 no | «La frase migliora W, mentre P−S resta sotto il criterio di conferma». Nella libreria l'istruzione va documentata come parte del metodo. |
| HI1 e HI2 non in ≥ 3 | Si riporta modello per modello, senza generalizzare. |

HI3 si legge a parte. Se è confermata in ≥ 3 si scrive: «il template in prosa senza spiegazione ottiene un W più alto del template simbolico senza spiegazione». Non si attribuisce la differenza alla sola notazione.

## 6. Descrittivi (non decidono nulla)
- W e AUROC su S+S e S−S. S+S è una replica di ADD su storie nuove.
- Interazione: (P+S − P−S) − (S+S − S−S), con IC, sulle coppie presenti in tutte e quattro le condizioni.
- UNKNOWN generato sui C e sui B per condizione, e falsa astensione sui B secondo la posizione della riga incerta.
- W a parità di risposta, cioè sulle coppie con UNKNOWN su entrambi e su quelle senza UNKNOWN su entrambi, come nella v2 del resoconto del Test U.
- Accuratezza su A e B per condizione.
- Entropia e (1 − probabilità massima) come misure alternative.

## 7. Cosa non fa questo test
- Non tocca V1, V3, il controllo della «o» o la polarità.
- Non separa il formato dalla domanda («given» in prosa, «granted» in simbolico): fanno parte del formato, come nel Test U.
- La frase di spiegazione non è identica fra prosa e simbolico, perché ognuna è scritta nel linguaggio del proprio formato. HI2 e HI3 restano interpretabili. L'interazione invece va letta con questa riserva.