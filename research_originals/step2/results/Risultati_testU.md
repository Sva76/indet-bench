# Test U: risultati (4 modelli, 8 novembre)

Protocollo: `Protocollo_testU_v2.md`. Notebook: `TestU_astensione_4_modelli_v3.ipynb` (versione U-v1-notebook-2), modalità completa, 4 modelli su 4.
Dati: `testU_risultati/` (esiti.json, benchmark.csv, rapporto.txt, una cartella per modello). Revisione Llama: 0e9e39f2.

## In breve

1. **p(UNKNOWN) separa C da B in tutti e 4 i modelli solo nel formato in prosa (V2).** È l'unico formato in cui la regola della libreria (3 conferme su 4) è soddisfatta. Su ADD e V1 il segnale si conferma in un solo modello per formato, e in V1 OLMo e Llama vanno nella direzione opposta.
2. **La soglia fissata su ADD non si trasferisce.** In nessun formato si arriva a 3 su 4. In prosa la soglia fa peggio della risposta del modello in 3 modelli su 4, perché in prosa quei modelli si astengono già da soli.
3. **Il rilevatore SQuAD non reagisce alla parola «o» in sé.** Una «o» neutra abbassa il punteggio in tutti e 4 i modelli (HO1 rovesciata). Ciò che lo fa salire è la presenza di due valori. Questo corregge in parte la lettura dello Step 1.
4. **Il controllo della polarità non è valutabile** per nessun modello: nessuna formulazione della domanda negata ha superato il filtro.

Tutti i controlli di allineamento sono superati, quindi i numeri sono confrontabili con i test precedenti.

## Controlli preliminari

| Controllo | Esito |
|---|---|
| p(UNKNOWN) dei 24 casi del test 6 (tolleranza 1e-3) | superato: scarto massimo 4.6e-10 per Qwen, 1.8e-7 per Mistral |
| Rilevatore SQuAD rispetto al test 4 (Pearson ≥ 0.999, ΔAUROC ≤ 0.01) | superato: Qwen e Mistral ≈ 1.0; OLMo 0.9993–0.9998, ΔAUROC ≤ 0.0012 |
| Rilevatore SQuAD di Llama (nuovo, senza riferimento) | AUROC 0.927 su SQuAD |
| Prompt con massa YES/NO/UNKNOWN sotto 0.90 | 0% |
| Coppie scartate | 0 in tutti gli insiemi |

## HU1: p(UNKNOWN) più alto su C che su B

W è la quota di coppie in cui C supera B (con i pareggi contati 0.5), media per storia, con IC al 95% da bootstrap sulle storie. Il criterio è CONFERMATA se il limite inferiore è sopra 0.5 e W ≥ 0.60.

| Modello | ADD | V1 (simbolico) | V2 (prosa) | V3 (descrittivo) |
|---|---|---|---|---|
| Qwen3-8B | **0.688** [0.64, 0.73] CONF | 0.529 [0.50, 0.56] NC | **0.914** [0.89, 0.93] CONF | 1.000 |
| Mistral-Nemo | 0.542 [0.49, 0.59] NC | **0.633** [0.60, 0.66] CONF | **0.834** [0.80, 0.87] CONF | 0.996 |
| OLMo-2-7B | 0.548 [0.52, 0.58] NC | 0.444 [0.41, 0.47] NON CONF | **0.736** [0.70, 0.78] CONF | 0.263 |
| Llama-3.1-8B | 0.558 [0.51, 0.60] NC | 0.405 [0.37, 0.44] NON CONF | **0.839** [0.81, 0.86] CONF | 0.754 |
| **Conferme** | 1 su 4 | 1 su 4 | **4 su 4** | non previsto |

In V1, OLMo e Llama hanno W sotto 0.5 con l'intervallo tutto sotto: il modello dà più probabilità a UNKNOWN sulla storia determinata che su quella indeterminata. In V3 OLMo è rovesciato allo stesso modo (0.26).

**Quanto del segnale in prosa viene dall'astensione esplicita.** Ricalcolando W solo sulle coppie in cui il modello non risponde UNKNOWN su C:

| Modello | W in V2 | W senza le coppie in cui C riceve UNKNOWN | quota di C con UNKNOWN |
|---|---|---|---|
| Qwen | 0.914 | 0.794 | 83% |
| Mistral | 0.834 | 0.589 | 77% |
| OLMo | 0.736 | 0.727 | 4% |
| Llama | 0.839 | 0.054 | 95% |

In Llama il segnale in prosa coincide con l'astensione esplicita. Nel 5% dei casi in cui Llama risponde su C, p(UNKNOWN) è più basso che sul B corrispondente, che spesso riceve UNKNOWN. Il caso di OLMo è l'opposto: il modello non si astiene quasi mai, ma la probabilità di UNKNOWN separa comunque C da B.

## HU2: soglia fissata su ADD e applicata agli altri formati

ΔBA è la balanced accuracy della regola «UNKNOWN se p(UNKNOWN) ≥ τ» meno quella della risposta generata dal modello. Il criterio è ΔBA ≥ 0.05 con il limite inferiore dell'IC sopra 0. L'IC viene dal bootstrap congiunto, che ristima τ su ADD a ogni replica.

| Modello | τ (da ADD) | V1: ΔBA [IC] | V2: ΔBA [IC] | V2: BA del modello | V3: ΔBA (descr.) |
|---|---|---|---|---|---|
| Qwen | 2.5e-10 | +0.047 [0.022, 0.065] NC | −0.293 [−0.31, −0.28] NON CONF | 0.83 | +0.47 |
| Mistral | 0.0036 | **+0.119** [0.106, 0.162] CONF | −0.180 [−0.20, −0.15] NON CONF | 0.71 | +0.49 |
| OLMo | 0.0028 | −0.013 [−0.026, 0.019] NC | **+0.157** [0.132, 0.197] CONF | 0.52 | −0.05 |
| Llama | 0.119 | +0.041 [0.021, 0.058] NC | −0.148 [−0.17, −0.13] NON CONF | 0.72 | +0.19 |
| **Conferme** | | 1 su 4 | 1 su 4 | | |

In V1 e V3 i modelli non rispondono mai UNKNOWN, quindi la loro BA è 0.5 e qualunque soglia sensata la migliora. In V3 il guadagno è grande (Qwen, Mistral), ma V3 è solo descrittivo e ha 60 storie. In V2 le soglie stimate su ADD sono molto basse (per Qwen quasi zero), perché su ADD p(UNKNOWN) è minuscolo anche sui C. Applicate alla prosa, classificano quasi tutto come UNKNOWN. La soglia aiuta solo dove il modello non si astiene già da sé (OLMo).

## Comportamento generato (descrittivo)

Quota di risposte UNKNOWN:

| Modello | C in ADD, V1, V3 | C in V2 | B in V2 |
|---|---|---|---|
| Qwen | ≈ 0 | 83% | 29% |
| Mistral | 0 | 77% | 49% |
| OLMo | 0 | 4% | 0.25% |
| Llama | 0 | 95% | 79% |

Astensione sbagliata sui B in V2, secondo la posizione della riga incerta (prima o ultima):

| Modello | riga incerta all'inizio | riga incerta in fondo |
|---|---|---|
| Qwen | 10.5% | 46.8% |
| Mistral | 28% | 71% |
| Llama | 92.5% | 65% |
| OLMo | ≈ 0 | ≈ 0 |

In Qwen e Mistral una riga incerta messa in fondo fa astenere il modello anche quando la storia è determinata. Llama va nella direzione opposta e si astiene comunque sulla gran parte dei B. La posizione è un descrittivo aggiunto, non un'ipotesi preregistrata.

**Misure alternative senza addestramento.** In prosa, entropia e (1 − probabilità massima) sono molto peggiori di p(UNKNOWN) in tre modelli (W 0.52 per Qwen, 0.33 per Mistral, 0.18 per Llama) e un po' peggiori in OLMo (0.67 contro 0.74). Su ADD sono simili (Mistral 0.49–0.50, OLMo 0.53) o di poco migliori (Qwen 0.72, Llama 0.62). La quantità che porta il segnale è la probabilità della risposta di astensione, non l'incertezza generica sull'uscita.

## Controllo della «o» (insieme O, 120 storie, 240 coppie)

Il punteggio è quello del rilevatore SQuAD ricostruito per ciascun modello. Valori W per coppia (preregistrati: HO1 e HO2).

| Confronto | Qwen | Mistral | OLMo | Llama |
|---|---|---|---|---|
| HO1: A con «o» neutra > A con «e» | 0.32 NON CONF | 0.15 NON CONF | 0.22 NON CONF | 0.28 NON CONF |
| HO2: B scritto «false or true» > B scritto «false, true» | 0.12 NON CONF | **0.60 CONF** | **1.00 CONF** | 0.36 NON CONF |
| Due valori senza «o» (B_set > A_and), descrittivo | 0.96 | 1.00 | 0.55 | 1.00 |
| Rilevatore, C contro B nell'insieme O | 0.43–0.65 in tutti i modelli | | | |

Lettura secondo le regole fissate nel protocollo:
- **Qwen e Llama:** l'allarme dipende dalla presenza di due valori, non dalla parola. Scrivere la «or» fra i valori lo abbassa.
- **Mistral:** contano i due valori e, in misura minore, la parola nella notazione.
- **OLMo:** conta solo la parola nella notazione, non i due valori.
- **In tutti e 4 i modelli** una «o» neutra nella frase di chiusura abbassa il punteggio. p(UNKNOWN) va nella stessa direzione (W 0.18–0.38), tranne in Qwen dove è quasi neutra (0.47).

Il confronto «due valori senza o» ha due token in più nel B, quindi va letto con la riserva della lunghezza (lo Step 1 aveva trovato in Qwen un bias di lunghezza del prompt). Il rilevatore non distingue C da B nemmeno in questo insieme. Sui C dell'insieme O, sia nella forma con la virgola sia in quella con «or», nessun modello genera UNKNOWN. p(UNKNOWN) separa C da B in questo insieme solo in Qwen (0.77), come su ADD.

**Rispetto allo Step 1:** la frase «il rilevatore SQuAD scatta sulla "o" nella regola» va precisata. In Qwen (e ora in Llama) reagisce alla presenza di due valori; in Mistral e OLMo la parola nella notazione conta. In nessun modello reagisce a una «o» qualunque.

## Polarità (domanda negata)

NON VALUTABILE per tutti e 4 i modelli. Nessun candidato ha raggiunto min(acc_YES, acc_NO) ≥ 0.90.
- Con la definizione (N1, N3) le risposte pendono verso YES. In Llama, Mistral e OLMo è quasi sempre YES (per esempio Llama N1: acc_YES 0.96, acc_NO 0.02); in Qwen in modo meno netto (N1: 0.65 e 0.14).
- Con l'esempio svolto (N2), Qwen e OLMo rispondono sempre NO.

I modelli non seguono la domanda negata in modo affidabile in questo formato, quindi la bidirezionalità resta non verificata.

## Riserve

1. **Istruzione diversa in V2.** L'istruzione della prosa dice esplicitamente che «either case is possible and you are not told which». Il successo in V2 non si può attribuire alla prosa in sé: può dipendere dall'istruzione che autorizza l'astensione. Per separare le due cose servirebbe la prosa con l'istruzione degli altri formati.
2. **V1 ha accuratezza bassa sulle storie determinate** (OLMo A/B 0.50/0.48, Mistral 0.63/0.63). Dove il modello non risolve nemmeno i B, è poco sensato chiedere che riconosca i C.
3. **Analisi post hoc condizionata a B corretto** (con il rischio di selezione). W è molto più alto quando il modello risponde bene al B: Mistral ADD 0.665 contro 0.005, Mistral V1 0.81 contro 0.44, Qwen V1 0.63 contro 0.32. Indica che il segnale c'è soprattutto dove il modello capisce la storia. È esplorativo, non preregistrato.
4. **Le soglie di Qwen e Mistral sono minuscole** (dell'ordine di 1e-10 e 1e-3), quindi la regola su ADD è sensibile a piccole variazioni di calibrazione.

## Cosa significa per la libreria

- **p(UNKNOWN) è una misura utile ma condizionata al formato.** Funziona su 4 modelli quando il prompt rende l'astensione una risposta legittima (V2). Sui formati logici compatti (ADD, V1) non regge come misura generale. Va documentata così, con il formato come parte del metodo.
- **Le soglie non si trasferiscono tra formati.** La libreria deve calibrarle per formato (o per dominio), e il benchmark deve riportare la BA della risposta del modello accanto a quella della soglia.
- **L'astensione generata e p(UNKNOWN) non sono la stessa cosa.** In Llama coincidono, in OLMo p(UNKNOWN) porta un segnale che il modello non esprime. Conviene riportarle separate.
- **Falsi allarmi dovuti alla posizione.** In Qwen e Mistral una riga incerta in fondo fa astenere il modello anche sulle storie determinate. Il benchmark deve bilanciare la posizione.
- **Rilevatori addestrati su SQuAD:** reagiscono alla forma (due valori, notazione), non all'indeterminatezza, e non distinguono C da B. Il protocollo di validazione delle sonde deve includere un insieme di controllo come O.

## Prossimi passi già in lista

1. Confronto con i metodi esistenti sulle coppie B/C: una sonda pubblicata e i rilevatori di SIRIN (answerability, LM-Polygraph).
2. Punto C: allucinazioni con contesto.
3. Facoltativo: cella 11 (coseni del test 7, solo CPU).
4. Possibile controllo aggiuntivo suggerito da questi dati: V2 con l'istruzione degli altri formati, per separare prosa e istruzione.