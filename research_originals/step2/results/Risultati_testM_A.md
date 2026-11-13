# Test M, notebook A: risultati (M1, M3, M4, 4 modelli, 10 novembre)

Protocollo: `Protocollo_testM_metodi_v2.md`. Notebook: `TestM_A_metodi_v8.ipynb` (versione M-A-notebook-8), modalità completo, 4 modelli su 4. Tutti i lavori sono ESEGUITI su NVIDIA A100-SXM4-80GB, nella stessa sessione (avvio 13:38, fine 20:08 UTC).
Dati: `testM_risultati/` (esiti_A.json, tabella_A.csv, rapporto_A.txt e testM_A_risultati_completo.zip, che contiene log, ambienti, dati di input e uscite di ogni lavoro).
Stato: **bozza per la revisione di Simona**. M2 (notebook B) non è ancora eseguito, quindi questo non è il resoconto finale del Test M.

## In breve

1. **Nessun metodo di LM-Polygraph (M1) riconosce l'indeterminatezza logica secondo la regola dei 3 su 4.** Gli stimatori migliori, MeanTokenEntropy e SemanticEntropy, confermano HM1 in 2 modelli su 4 (Qwen e Llama). MSP e Perplexity non la confermano in nessun modello. PTrue passa HM0 solo su OLMo.
2. **Nessuno stimatore di M1 fa meglio di p(UNKNOWN).** HM2 non è confermata in nessuna delle 16 celle valutabili, e in tutte ΔW è negativo, con l'IC tutto sotto 0 (da −0.09 a −0.49).
3. **Su Mistral gli stimatori di M1 sono rovesciati.** W vale circa 0.30 per tutti e quattro gli stimatori valutabili, con l'IC tutto sotto 0.5: Mistral risulta *più sicuro* sui casi indeterminati che su quelli decidibili. Formula preregistrata: «funziona sul suo dominio ma non riconosce l'indeterminatezza logica delle coppie B/C».
4. **Il giudice zero-shot di SIRIN (M3) conferma HM1**: W 0.693 [0.648, 0.738]. Resta però sotto p(UNKNOWN) di tutti e 4 i modelli su P−S (ΔW descrittivo da −0.005 a −0.29).
5. **La sonda LoRA di Obeso et al. (M4-LoRA) conferma HM1 e HM2 su Llama**: W 0.823 [0.792, 0.851], ΔW +0.086 [+0.039, +0.135] rispetto a p(UNKNOWN) di Llama. È l'unico metodo del notebook A che fa meglio di p(UNKNOWN) in una cella. Vale per un solo modello e, per protocollo, non si generalizza. La sonda lineare (M4-lin) è al caso (0.481, NON CONCLUSIVA).
6. **Descrittivo, non preregistrato: i risultati dipendono molto dall'operatore logico.** Quasi tutti i metodi, p(UNKNOWN) compresa, sono vicini a 1 su una famiglia (AND, OR o IMPLIES) e sotto 0.5 su un'altra. Il vantaggio di M4-LoRA viene tutto dalla famiglia AND, dove p(UNKNOWN) di Llama fallisce (sezione «Descrittivi»).

## Controlli tecnici

| Controllo | Esito |
|---|---|
| Lavori | 10 su 10 ESEGUITI con l'impronta attesa, nessun lavoro escluso, nessun errore di analisi |
| GPU | stessa famiglia per tutti i lavori (A100-SXM4-80GB) |
| Riferimento p(UNKNOWN) in `env_m1` | scarto massimo dal Test U2 ≤ 1.1e-16 sui 24 valori, risposte uguali al Test U2 nel 100% dei 2400 prompt P−S, W identico al Test U2 per tutti e 4 i modelli |
| Riferimento in `env_sirin` | scarto massimo 0.024–0.060, risposte uguali 98.6–99.5%, W entro 0.009 dal Test U2 (descrittivo, versione di transformers richiesta da SIRIN) |
| Riferimento in `env_obeso` (Llama) | scarto massimo 0.028, risposte uguali 99.0%, W 0.7375 (Test U2 0.746) |
| Token di LM-Polygraph diversi dal riferimento | 0 su 4800 per ogni modello |
| Risposta greedy di LM-Polygraph uguale al riferimento | 98.5–99.2% |
| Copertura su P−S | 800 coppie valide su 800 in ogni cella, nessuno scarto (minimo richiesto 760) |
| M3 | prefisso senza thinking (`<think>\n\n</think>`), come corretto nella v6 |
| M4 HM0 | LongFact test annotato, codice degli autori, batch 4, Llama alla revisione `0e9e39f` (uguale a quella del protocollo) |

Ho ricalcolato a mano dalle uscite grezze il W di M4-lin, M4-LoRA, M1-MSP e p(UNKNOWN) per tutti e 4 i modelli, e coincide con l'analisi del notebook.

## Controlli positivi (HM0, soglia 0.70)

| Metodo | Qwen | Mistral | OLMo | Llama |
|---|---|---|---|---|
| M1-MSP | 0.819 | 0.835 | 0.779 | 0.867 |
| M1-Perplexity | 0.815 | 0.846 | 0.778 | 0.857 |
| M1-MeanTokenEntropy | 0.830 | 0.865 | 0.812 | 0.871 |
| M1-SemanticEntropy | 0.815 | 0.839 | 0.802 | 0.846 |
| M1-PTrue | **0.284** | **0.402** | 0.704 | **0.351** |

M1: AUROC tra risposta errata e corretta su 400 domande TriviaQA. PTrue non passa su Qwen, Mistral e Llama, quindi lì è NON VALUTABILE. Il valore basso è coerente con la prova (log p(True) molto negativo): è il comportamento della libreria pubblicata, che non abbiamo modificato.

M3: AUROC tra domande senza e con risposta su 400 SQuAD 2.0 di verifica, **0.805**.

M4 (AUC span-max su LongFact test, codice degli autori): **M4-lin 0.848**, **M4-LoRA 0.890**. Per la LoRA gli autori riportano 0.890 sullo stesso test, quindi il loro risultato è replicato. Per la lineare la cartella riporta solo HealthBench (0.849), un altro dataset.

## Ipotesi preregistrate su P−S

W è la quota di coppie in cui il punteggio di incertezza di C supera quello di B, mediata per storia, con IC al 95% su 2000 ricampionamenti delle storie (200 storie, 800 coppie). ΔW è W(metodo) − W(p(UNKNOWN)) sulle stesse 800 coppie, nello stesso ambiente.

### M1 (LM-Polygraph)

| Stimatore | Modello | W [IC] | HM1 | ΔW [IC] | HM2 |
|---|---|---|---|---|---|
| MSP | Qwen | 0.565 [0.516, 0.616] | NC | −0.410 [−0.459, −0.361] | NON CONF |
| | Mistral | 0.305 [0.278, 0.335] | NON CONF | −0.478 [−0.510, −0.443] | NON CONF |
| | OLMo | 0.575 [0.520, 0.630] | NC | −0.119 [−0.149, −0.090] | NON CONF |
| | Llama | 0.568 [0.529, 0.606] | NC | −0.179 [−0.215, −0.140] | NON CONF |
| Perplexity | Qwen | 0.565 [0.516, 0.616] | NC | −0.410 | NON CONF |
| | Mistral | 0.307 [0.280, 0.336] | NON CONF | −0.475 | NON CONF |
| | OLMo | 0.575 [0.520, 0.630] | NC | −0.119 | NON CONF |
| | Llama | 0.564 [0.525, 0.604] | NC | −0.183 | NON CONF |
| MeanTokenEntropy | Qwen | 0.669 [0.621, 0.715] | **CONF** | −0.306 [−0.353, −0.260] | NON CONF |
| | Mistral | 0.297 [0.270, 0.323] | NON CONF | −0.485 | NON CONF |
| | OLMo | 0.574 [0.516, 0.629] | NC | −0.120 | NON CONF |
| | Llama | 0.641 [0.609, 0.676] | **CONF** | −0.105 [−0.144, −0.064] | NON CONF |
| SemanticEntropy | Qwen | 0.625 [0.586, 0.668] | **CONF** | −0.350 [−0.389, −0.309] | NON CONF |
| | Mistral | 0.323 [0.290, 0.356] | NON CONF | −0.460 | NON CONF |
| | OLMo | 0.549 [0.499, 0.601] | NC | −0.145 | NON CONF |
| | Llama | 0.656 [0.626, 0.686] | **CONF** | −0.090 [−0.133, −0.046] | NON CONF |
| PTrue | OLMo | 0.562 [0.521, 0.604] | NC | −0.131 [−0.206, −0.055] | NON CONF |
| | Qwen, Mistral, Llama | NON VALUTABILE (HM0) | | | |

Conferme per la lettura della libreria (almeno 3 su 4): HM1 2 su 4 per MeanTokenEntropy e SemanticEntropy, 0 su 4 per MSP e Perplexity, 0 su 1 per PTrue. HM2 0 su 4 per tutti. Il limite di Qwen per HM2 (margine massimo +0.025) non conta qui, perché ΔW è negativo in ogni modello.

Per lo stimatore, MSP e Perplexity danno lo stesso W su Qwen e OLMo. Con risposte di pochi token i due punteggi ordinano le righe quasi allo stesso modo.

### M3 (giudice zero-shot Qwen3-4B, SIRIN)

| Formato | W [IC] | HM1 |
|---|---|---|
| P−S | 0.693 [0.648, 0.738] | **CONFERMATA** |
| S−S (descrittivo) | 0.638 [0.591, 0.683] | |

ΔW descrittivo rispetto a p(UNKNOWN) di ciascun modello, ricalcolato in `env_sirin`:

| Riferimento | P−S | S−S |
|---|---|---|
| Qwen (W 0.980 / 0.633) | −0.288 [−0.333, −0.241] | +0.006 [−0.030, +0.041] |
| Mistral (0.779 / 0.545) | −0.086 [−0.153, −0.017] | +0.093 [0.000, +0.183] |
| OLMo (0.698 / 0.589) | −0.005 [−0.084, +0.080] | +0.049 [−0.019, +0.113] |
| Llama (0.738 / 0.544) | −0.045 [−0.078, −0.011] | +0.094 [+0.060, +0.129] |

In prosa il giudice non supera p(UNKNOWN) di nessun modello. Nel formato simbolico (S−S) supera Llama, e Mistral al limite. Questo è descrittivo: il giudice è un modello diverso da quello che risponde. Alla soglia 0.5 il giudice segna «senza risposta» il 35% dei C, ma anche il 23% dei B e lo 0.5% degli A.

### M4 (sonde di Obeso et al., solo Llama)

| Sonda | W [IC] | HM1 | ΔW [IC] | HM2 | W S−S (descrittivo) |
|---|---|---|---|---|---|
| M4-lin | 0.481 [0.447, 0.514] | NC | −0.257 [−0.302, −0.210] | NON CONF | 0.579 [0.546, 0.610] |
| M4-LoRA | 0.823 [0.792, 0.851] | **CONF** | **+0.086 [+0.039, +0.135]** | **CONF** | 0.550 [0.510, 0.590] |

Riferimento: p(UNKNOWN) di Llama in `env_obeso`, W 0.7375, margine massimo 0.262. Per protocollo, M4 vale solo per Llama e non si generalizza. La cartella della LoRA si chiama λ = 0.05, ma la sua configurazione di addestramento dice λ_KL = 0.5.

Formulazioni: per M4-lin quella preregistrata, «non ha superato il criterio HM1 in questo test». Per un esito confermato il protocollo non prevede una frase. Propongo: «su Llama, unico modello provato, M4-LoRA conferma HM1 e HM2 in questo test».

## Descrittivi (non preregistrati)

**W per famiglia, su P−S.** Queste misure non erano previste dal protocollo. Le riporto perché cambiano la lettura dei W complessivi. Circa 265 coppie per famiglia, senza IC.

| Metodo | Modello | AND | IMPLIES | OR |
|---|---|---|---|---|
| p(UNKNOWN) (`env_m1`) | Qwen | 0.963 | 0.966 | 0.996 |
| | Mistral | 0.978 | 0.761 | 0.608 |
| | OLMo | 1.000 | 0.727 | 0.354 |
| | Llama | 0.448 | 0.792 | 1.000 |
| M1-MeanTokenEntropy | Qwen | 0.243 | 0.780 | 0.985 |
| | Mistral | 0.448 | 0.295 | 0.149 |
| | OLMo | 0.993 | 0.640 | 0.090 |
| | Llama | 0.526 | 0.689 | 0.709 |
| M1-SemanticEntropy | Qwen | 0.381 | 0.633 | 0.862 |
| | Llama | 0.586 | 0.655 | 0.728 |
| M3 giudice | — | 0.310 | 0.775 | 0.994 |
| M4-LoRA | Llama | 0.901 | 0.655 | 0.910 |

- Solo p(UNKNOWN) di Qwen è alto su tutte e tre le famiglie. Negli altri casi un metodo può essere quasi perfetto su una famiglia e sotto il caso su un'altra, e il W complessivo è una media di comportamenti opposti.
- Il vantaggio di M4-LoRA su Llama viene dalla famiglia AND: +0.47 rispetto a p(UNKNOWN) di `env_obeso` (0.433). Su IMPLIES (−0.13) e OR (−0.08) la sonda fa peggio di p(UNKNOWN). Ricorda il Test 6, dove il vantaggio degli stati interni veniva tutto da un solo sottoinsieme (OR NOT).
- Il giudice M3 è quasi perfetto su OR (0.994) e sotto il caso su AND (0.310).

**Perché M1 è rovesciato su Mistral.** Su P−S Mistral risponde UNKNOWN al 45% dei C e al 30% dei B, e quando dice UNKNOWN è molto sicuro. MSP medio: 0.32 sui C con UNKNOWN e 0.45 sui B con UNKNOWN, contro 0.81 sui C e 1.58 sui B con altre risposte. Gli stimatori di M1 misurano quanto il modello è sicuro della risposta che genera, non se la risposta è «non si può sapere». Una astensione sicura conta quindi come bassa incertezza. È una mia interpretazione dai valori medi, non un test. Va nella stessa direzione l'AUROC descrittivo di M1 su SQuAD per Mistral (0.27–0.37): anche lì Mistral è più sicuro sulle domande senza risposta.

**Risposta generata su P−S** (risposta greedy di LM-Polygraph, uguale al riferimento nel 98–99% dei casi): UNKNOWN sui C / sui B. Qwen 25% / 0%, Mistral 45% / 30%, OLMo 1% / 0%, Llama 34% / 5%.

## Lettura

- I metodi di LM-Polygraph passano i loro controlli positivi su TriviaQA (0.78–0.87, tranne PTrue) ma non separano in modo stabile le coppie B/C, e in nessun modello fanno meglio di p(UNKNOWN). Su Mistral sono rovesciati.
- Il giudice di SIRIN riconosce l'indeterminatezza (HM1 confermata), ma in prosa resta sotto p(UNKNOWN) del modello che risponde.
- La sonda LoRA di Obeso et al. è l'unico metodo che batte p(UNKNOWN), su Llama. Il vantaggio viene da una sola famiglia logica, e la stessa sonda sul formato simbolico scende a 0.55.
- p(UNKNOWN) resta il segnale più robusto fra quelli provati, coerente con lo Step 1 e il Test U2. Però anche p(UNKNOWN) dipende molto dall'operatore logico in 3 modelli su 4.

## Limiti

- 4 modelli tra 7 e 12B, storie sintetiche di un solo tipo, solo inglese.
- M4 su un solo modello.
- M2 (sonda answerability di SIRIN) manca: arriva con il notebook B.
- Le analisi per famiglia sono a posteriori e senza IC. Prima di usarle in una conclusione servirebbe un'analisi preregistrata.
- Il confronto di M3 con p(UNKNOWN) è descrittivo per costruzione.

## Prossimo passo

Dopo la revisione di Simona: la nota di protocollo con la configurazione esatta di M2, poi il notebook B. Se Simona lo approva, si potrebbe preregistrare per il notebook B anche l'analisi per famiglia (W per AND, IMPLIES, OR con IC), da applicare a tutti i metodi.