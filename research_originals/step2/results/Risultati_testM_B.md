# Test M, notebook B: risultati (M2 e M2-senzaℓ2, 4 modelli, 11 novembre)

Protocollo: `Protocollo_testM_metodi_v2.md` e `Nota_M2_configurazione_v2_2.md` (approvata l'11 novembre). Notebook: `TestM_B_M2_v4_1.ipynb` (versione M-B-notebook-4; la v4_1 corregge solo l'esportazione), modalità completo, 4 modelli su 4. GPU NVIDIA A100-SXM4-80GB, sessione da 167.1 GB, avvio 13:03 e fine 16:57 UTC (circa 3.9 ore di Colab; M2 per modello da 51 a 65 minuti).
Dati: `testM_risultati/` (esiti_B.json, tabella_B.csv, tabella_famiglie_B.csv, rapporto_B.txt e testM_B_risultati_completo.zip, con log, ambiente, dati, uscite e sonde salvate di ogni lavoro). Tabelle generate dallo ZIP: `strumenti_resoconto_B/tabelle_B_completo.md`.
Dimensione: **1000 + 200 esempi per modello (riserva)**. La riserva deriva dalla regola sulla RAM (nota §2.6 e appendice), non da una scelta sui risultati.
Stato: **rivisto da Simona l'11 novembre** (versione 2: esiti HM0/HM1/HM2 invariati; correzioni su HM1, HM2 nel simbolico, epoche di Qwen e analisi POS/NOT). Lo schema di questo resoconto è stato scritto prima di vedere i risultati (`Risultati_testM_B_schema.md`); le formule di lettura sono quelle preregistrate.

## In breve

1. **Controllo positivo (HM0).** M2 originale lo supera in 3 modelli su 4 (Mistral 0.909, OLMo 0.911, Llama 0.931). Su Qwen non lo supera: 0.499. M2-senzaℓ2 lo supera in 4 su 4 (Qwen 0.881, Mistral 0.925, OLMo 0.912, Llama 0.937). Per M2 su Qwen: **NON VALUTABILE**, «risultato sull'implementazione SIRIN e sulla configurazione adottata». Il collasso della sonda originale di Qwen visto nella diagnostica a 2000 + 400 si ripete a 1000 + 200.
2. **M2 originale (analisi principale): HM1 confermata in 1 modello su 3 valutabili (Mistral, W 0.646 [0.606, 0.686]); HM2 in 0.** Su OLMo e Llama M2 «non ha superato il criterio HM1 in questo test» (W 0.506 e 0.497, IC che includono 0.5). Il criterio generale dei 3 su 4 non è raggiunto, quindi non si può scrivere che M2 «riconosce l'indeterminatezza logica in prosa»; questo non dimostra che il segnale sia assente, e resta la conferma su Mistral. M2 non «fa meglio di p(UNKNOWN)»: nel confronto principale P−S, ΔW è negativo in tutti e 3 i modelli valutabili, con l'IC interamente sotto 0 (da −0.13 a −0.24).
3. **M2-senzaℓ2 (secondaria preregistrata): HM1 confermata in 1 modello su 4 (Mistral, W 0.611 [0.570, 0.652]); HM2 in 0.** Su Qwen la variante «funziona sul suo dominio ma non riconosce l'indeterminatezza logica delle coppie B/C»: W 0.450 [0.415, 0.487], quindi assegna punteggi di «senza risposta» più bassi ai casi C che ai B. Su OLMo e Llama «non ha superato il criterio HM1 in questo test». Anche qui il criterio generale non è raggiunto, senza che questo dimostri l'assenza del segnale. Nel confronto principale P−S, ΔW è negativo in tutti e 4 i modelli con l'IC sotto 0 (da −0.17 a −0.53); nel simbolico (S−S, descrittivo) ci sono alcuni vantaggi, per esempio Mistral +0.045 [0.006, 0.084]. Questi esiti affiancano quelli di M2 e non li sostituiscono.
4. **Per famiglia (secondaria, IC non corretti).** Con il criterio nominale, solo M2-senzaℓ2 su OR raggiunge i 3 su 4 (HM1_f in 4 su 4): «M2-senzaℓ2 riconosce l'indeterminatezza sulla famiglia OR» (criterio nominale). M2 originale su OR arriva a 2 su 3 valutabili (Mistral, Llama). Su AND e IMPLIES nessuno dei due metodi va oltre 1 modello. HM2_f è confermata solo su OR, in 2 modelli per ciascun metodo (Mistral e OLMo, dove p(UNKNOWN) su OR è debole). H ≥ 0.20 in 6 celle su 8, quindi «forti differenze tra famiglie» (descrittivo). Il caso più netto è Llama: W_f su AND 0.004 (M2) e 0.007 (variante), su OR 0.963 e 0.910.
5. **Confronto con il notebook A (descrittivo).** Sulle stesse 800 coppie P−S, M2 e la variante restano sotto p(UNKNOWN) di `env_sirin` in ogni modello (riferimento 0.698–0.980). Restano sotto anche al giudice M3 (0.693) in tutti i modelli e alla sonda M4-LoRA su Llama (0.823). In sintesi, nessuna delle sonde di answerability di SIRIN addestrate su SQuAD separa le coppie meglio della probabilità di UNKNOWN del modello.

### Formule applicate

Sono le formule dello schema, senza modifiche: HM0 non superato → NON VALUTABILE («risultato sull'implementazione SIRIN e sulla configurazione adottata» per M2 su Qwen); HM1 NON CONFERMATA → «funziona sul suo dominio ma non riconosce l'indeterminatezza logica delle coppie B/C» (M2-senzaℓ2 su Qwen); HM1 NON CONCLUSIVA → «non ha superato il criterio HM1 in questo test» (OLMo e Llama, entrambi i metodi). Le frasi «riconosce l'indeterminatezza logica in prosa» e «fa meglio di p(UNKNOWN)» non si applicano a nessuno dei due metodi. La variante si cita come «M2-senzaℓ2», variante della configurazione di SIRIN, non metodo pubblicato. Il risultato dell'ablation (0.941 con 2000 + 400 su Qwen) non si dà per acquisito: con 1000 + 200 la variante su Qwen ha HM0 0.881 e AUROC di validazione 0.925.

## Controlli tecnici

| Controllo | Esito |
|---|---|
| Lavori | 10 su 10 ESEGUITI con l'impronta attesa (M2_dati, M2 per 4 modelli, installazione di `env_sirin`, 4 riferimenti riusati dal notebook A); nessun lavoro escluso, nessun errore di analisi, nessun metodo non eseguito |
| GPU | A100-SXM4-80GB per tutti i lavori |
| Decisione sulla RAM | **riserva**, sia nella prova sia in questa sessione (RAM 167.1 GB, limite 142.0 GB; Mistral proiezione piena 153.7 GB, riserva 77.4 GB) |
| Dati SQuAD | revisione `3ffb306f725f7d2ce8394bc1873b24868140c412`; bacino 130 297 su 130 319 (438 accorciate; escluse 22, tutte con risposta tagliata dall'accorciamento) |
| ID sha256 | addestramento `10966c4c815b…`, validazione `ca0f3def47b9…`, verifica `120067989e37…` (uguali alla prova e all'appendice della nota) |
| Confine dei token | 0 errori; massimo 512 token in addestramento e verifica (Llama, Qwen) |
| Controllo del segno | C > B = vittoria; punteggio di M2 = p(senza risposta); controllato su punteggi sintetici, NaN e ±infinito esclusi |
| Ricaricamento delle sonde | scarto massimo 0.0 su coppie, validazione e verifica, per entrambe le sonde e tutti e 4 i modelli (tolleranza 1e-6) |
| Epoca ricaricata | sempre la prima con F1 massimo |
| Copertura P−S | 800 coppie valide su 800 in ogni cella (minimo 760) |

| Riferimento p(UNKNOWN) di `env_sirin` | Origine | W P−S | W Test U2 | Risposte uguali a U2 | Scarto max sui 24 valori |
|---|---|---|---|---|---|
| Qwen | notebook A (riuso) | 0.980 | 0.975 | 0.986 | 0.060 |
| Mistral | notebook A (riuso) | 0.779 | 0.783 | 0.995 | 0.031 |
| OLMo | notebook A (riuso) | 0.698 | 0.694 | 0.986 | 0.024 |
| Llama | notebook A (riuso) | 0.738 | 0.746 | 0.990 | 0.028 |

Ho ricalcolato W e ΔW, P−S e S−S, dai punteggi grezzi dello ZIP con uno script separato (`tabelle_resoconto_B.py`, versione 2): **32 confronti eseguiti su 32 attesi, scarto massimo 0.0 dall'analisi del notebook.**

## Controllo positivo (HM0)

AUROC «senza risposta» contro «con risposta» sulle 400 domande di verifica (200 per classe), soglia 0.70.

| Modello | M2 | M2-senzaℓ2 | Domande nell'AUROC (M2 / variante) |
|---|---|---|---|
| Qwen | 0.499 NON SUPERATO | 0.881 SUPERATO | 400 / 400 |
| Mistral | 0.909 SUPERATO | 0.925 SUPERATO | 400 / 400 |
| OLMo | 0.911 SUPERATO | 0.912 SUPERATO | 400 / 400 |
| Llama | 0.931 SUPERATO | 0.937 SUPERATO | 400 / 400 |

Articolo di SIRIN, Qwen3-4B con un'altra configurazione: 0.879, descrittivo.

## Addestramento su SQuAD (validazione, 200 domande; descrittivo)

| Metodo | Modello | Epoche | F1 di validazione per epoca | Epoca scelta | AUROC validazione | Norma query / pesi (finale) |
|---|---|---|---|---|---|---|
| M2 | Qwen | 3 eseguite, 2 validate (l'arresto anticipato precede la terza validazione) | 0.667, 0.667 | 1 | 0.581 | 0.015 / 0.188 |
| M2-senzaℓ2 | Qwen | 5 | 0.592, 0.607, 0.638, 0.847, 0.854 | 5 | 0.925 | 9.735 / 5.796 |
| M2 | Mistral | 5 | 0.664, 0.671, 0.829, 0.862, 0.859 | 4 | 0.931 | 0.572 / 1.088 |
| M2-senzaℓ2 | Mistral | 5 | 0.804, 0.853, 0.864, 0.870, 0.866 | 4 | 0.931 | 1.782 / 2.511 |
| M2 | OLMo | 5 | 0.863, 0.853, 0.811, 0.808, 0.800 | 1 | 0.935 | 0.856 / 0.863 |
| M2-senzaℓ2 | OLMo | 5 | 0.845, 0.872, 0.897, 0.893, 0.893 | 3 | 0.937 | 1.498 / 1.404 |
| M2 | Llama | 5 | 0.667, 0.882, 0.882, 0.876, 0.876 | 2 | 0.946 | 0.888 / 1.090 |
| M2-senzaℓ2 | Llama | 5 | 0.860, 0.866, 0.878, 0.873, 0.872 | 3 | 0.955 | 2.683 / 2.086 |

Lo schema dell'originale su Qwen si ripete: F1 0.667 (il classificatore banale che dice sempre «senza risposta»), arresto anticipato, query quasi azzerata (0.015). Sulle coppie i suoi punteggi sono quasi costanti (media 0.515, deviazione standard 0.0005). Sugli altri modelli l'originale parte a volte dallo stesso F1 0.667 (Mistral e Llama alla prima epoca) e poi esce; la variante parte più in alto e ha norme finali maggiori. Da qui non si trae nessuna conclusione sulle coppie.

## Ipotesi preregistrate su P−S

W è la quota di coppie in cui il punteggio di C supera quello di B (pareggi a mezzo punto), mediata per storia, con IC al 95% su 2000 ricampionamenti delle storie (200 storie, 800 coppie). ΔW = W(metodo) − W(p(UNKNOWN) di `env_sirin`) sulle coppie comuni.

### M2 (principale)

| Modello | W [IC] | HM1 | ΔW [IC] | Margine 1 − W_rif | HM2 | Coppie comuni |
|---|---|---|---|---|---|---|
| Qwen | 0.450 [0.429, 0.470] | NON VALUTABILE (HM0) | −0.530 [−0.551, −0.510] | 0.020 | NON VALUTABILE (HM0) | 800 |
| Mistral | 0.646 [0.606, 0.686] | **CONFERMATA** | −0.133 [−0.183, −0.080] | 0.221 | NON CONFERMATA | 800 |
| OLMo | 0.506 [0.479, 0.534] | NON CONCLUSIVA | −0.191 [−0.235, −0.147] | 0.302 | NON CONFERMATA | 800 |
| Llama | 0.497 [0.443, 0.554] | NON CONCLUSIVA | −0.240 [−0.276, −0.205] | 0.262 | NON CONFERMATA | 800 |

### M2-senzaℓ2 (secondaria)

| Modello | W [IC] | HM1 | ΔW [IC] | Margine 1 − W_rif | HM2 | Coppie comuni |
|---|---|---|---|---|---|---|
| Qwen | 0.450 [0.415, 0.487] | NON CONFERMATA | −0.530 [−0.568, −0.491] | 0.020 | NON CONFERMATA | 800 |
| Mistral | 0.611 [0.570, 0.652] | **CONFERMATA** | −0.168 [−0.214, −0.119] | 0.221 | NON CONFERMATA | 800 |
| OLMo | 0.507 [0.464, 0.551] | NON CONCLUSIVA | −0.190 [−0.270, −0.107] | 0.302 | NON CONFERMATA | 800 |
| Llama | 0.490 [0.438, 0.544] | NON CONCLUSIVA | −0.247 [−0.284, −0.212] | 0.262 | NON CONFERMATA | 800 |

Conteggi per la lettura dei 3 su 4: **M2: HM1 1/3 valutabili, HM2 0/3** (Qwen NON VALUTABILE per HM0). **M2-senzaℓ2: HM1 1/4, HM2 0/4.** Su Qwen i due W P−S coincidono (0.450) per caso: i punteggi delle due sonde sono diversi (deviazione standard sulle coppie 0.0005 contro 0.045) e anche gli IC lo sono; il ricalcolo indipendente dà lo stesso valore. Per Qwen il margine possibile su p(UNKNOWN) è 0.020, sotto la soglia di +0.05, come previsto.

## Analisi per famiglia (secondaria preregistrata, nota §3; P−S, IC non corretti)

| Metodo | Modello | Famiglia | W_f [IC] | W_f rif | ΔW_f [IC] | HM1_f | HM2_f |
|---|---|---|---|---|---|---|---|
| M2 | Qwen | AND | 0.396 [0.358, 0.433] | 0.970 | −0.575 | NON VALUTABILE (HM0) | NON VALUTABILE (HM0) |
| M2 | Qwen | OR | 0.530 [0.511, 0.552] | 1.000 | −0.470 | NON VALUTABILE (HM0) | NON VALUTABILE (HM0) |
| M2 | Qwen | IMPLIES | 0.424 [0.390, 0.458] | 0.970 | −0.545 | NON VALUTABILE (HM0) | NON VALUTABILE (HM0) |
| M2 | Mistral | AND | 0.631 [0.578, 0.687] | 0.978 | −0.347 | CONFERMATA | NON CONFERMATA |
| M2 | Mistral | OR | 0.851 [0.799, 0.899] | 0.608 | +0.243 [0.194, 0.287] | CONFERMATA | CONFERMATA |
| M2 | Mistral | IMPLIES | 0.455 [0.394, 0.515] | 0.750 | −0.295 | NON CONCLUSIVA | NON CONFERMATA |
| M2 | OLMo | AND | 0.590 [0.541, 0.646] | 1.000 | −0.410 | NON CONCLUSIVA | NON CONFERMATA |
| M2 | OLMo | OR | 0.440 [0.399, 0.481] | 0.351 | +0.090 [0.030, 0.146] | NON CONFERMATA | CONFERMATA |
| M2 | OLMo | IMPLIES | 0.489 [0.447, 0.527] | 0.742 | −0.254 | NON CONCLUSIVA | NON CONFERMATA |
| M2 | Llama | AND | 0.004 [0.000, 0.011] | 0.433 | −0.429 | NON CONFERMATA | NON CONFERMATA |
| M2 | Llama | OR | 0.963 [0.933, 0.989] | 0.993 | −0.030 | CONFERMATA | NON CONFERMATA |
| M2 | Llama | IMPLIES | 0.527 [0.504, 0.553] | 0.788 | −0.261 | NON CONCLUSIVA | NON CONFERMATA |
| M2-senzaℓ2 | Qwen | AND | 0.291 [0.250, 0.336] | 0.970 | −0.679 | NON CONFERMATA | NON CONFERMATA |
| M2-senzaℓ2 | Qwen | OR | 0.724 [0.675, 0.772] | 1.000 | −0.276 | CONFERMATA | NON CONFERMATA |
| M2-senzaℓ2 | Qwen | IMPLIES | 0.333 [0.295, 0.375] | 0.970 | −0.636 | NON CONFERMATA | NON CONFERMATA |
| M2-senzaℓ2 | Mistral | AND | 0.750 [0.705, 0.799] | 0.978 | −0.228 | CONFERMATA | NON CONFERMATA |
| M2-senzaℓ2 | Mistral | OR | 0.769 [0.716, 0.817] | 0.608 | +0.160 [0.123, 0.198] | CONFERMATA | CONFERMATA |
| M2-senzaℓ2 | Mistral | IMPLIES | 0.311 [0.258, 0.367] | 0.750 | −0.439 | NON CONFERMATA | NON CONFERMATA |
| M2-senzaℓ2 | OLMo | AND | 0.261 [0.209, 0.317] | 1.000 | −0.739 | NON CONFERMATA | NON CONFERMATA |
| M2-senzaℓ2 | OLMo | OR | 0.854 [0.806, 0.899] | 0.351 | +0.504 [0.437, 0.567] | CONFERMATA | CONFERMATA |
| M2-senzaℓ2 | OLMo | IMPLIES | 0.405 [0.364, 0.447] | 0.742 | −0.337 | NON CONFERMATA | NON CONFERMATA |
| M2-senzaℓ2 | Llama | AND | 0.007 [0.000, 0.019] | 0.433 | −0.425 | NON CONFERMATA | NON CONFERMATA |
| M2-senzaℓ2 | Llama | OR | 0.910 [0.873, 0.948] | 0.993 | −0.082 | CONFERMATA | NON CONFERMATA |
| M2-senzaℓ2 | Llama | IMPLIES | 0.553 [0.523, 0.583] | 0.788 | −0.235 | NON CONCLUSIVA | NON CONFERMATA |

Coppie valide per famiglia: AND 268/268, OR 268/268, IMPLIES 264/264 in ogni cella. Gli IC dei ΔW_f negativi sono tutti interamente sotto 0 (il più vicino a 0 è Llama OR per M2, −0.030 [−0.060, −0.004]); l'elenco completo è in `tabelle_B_completo.md`.

| Metodo | Modello | H P−S [IC] | H ≥ 0.20 (stima puntuale) | H S−S [IC] |
|---|---|---|---|---|
| M2 | Qwen | 0.134 [0.097, 0.179] | no | 0.015 [0.004, 0.034] |
| M2-senzaℓ2 | Qwen | 0.433 [0.373, 0.496] | sì | 0.060 [0.034, 0.093] |
| M2 | Mistral | 0.396 [0.317, 0.475] | sì | 0.183 [0.130, 0.232] |
| M2-senzaℓ2 | Mistral | 0.458 [0.397, 0.533] | sì | 0.356 [0.307, 0.405] |
| M2 | OLMo | 0.149 [0.086, 0.216] | no | 0.094 [0.034, 0.155] |
| M2-senzaℓ2 | OLMo | 0.593 [0.519, 0.660] | sì | 0.651 [0.590, 0.707] |
| M2 | Llama | 0.959 [0.929, 0.985] | sì | 0.497 [0.437, 0.557] |
| M2-senzaℓ2 | Llama | 0.903 [0.866, 0.937] | sì | 0.452 [0.392, 0.509] |

Conteggio nominale per famiglia (HM1_f / HM2_f, sui modelli valutabili):

| Famiglia | M2 (3 valutabili) | M2-senzaℓ2 (4 valutabili) |
|---|---|---|
| AND | 1 (Mistral) / 0 | 1 (Mistral) / 0 |
| OR | 2 (Mistral, Llama) / 2 (Mistral, OLMo) | **4** (tutti) / 2 (Mistral, OLMo) |
| IMPLIES | 0 / 0 | 0 / 0 |

## Descrittivi (non preregistrati)

**S−S.** Nel formato simbolico i due metodi restano vicini al caso: W da 0.496 a 0.595. ΔW su p(UNKNOWN) va da −0.136 (Qwen) a +0.050 (Mistral, M2, IC [−0.003, 0.103]); per M2-senzaℓ2 su Mistral +0.045 [0.006, 0.084]. Nel simbolico ci sono quindi alcuni vantaggi descrittivi sulle sonde rispetto a p(UNKNOWN) (Mistral con entrambe le sonde, Llama circa 0). Il riferimento qui è più debole (W_rif da 0.54 a 0.63) e i W delle sonde restano vicini al caso; non si tratta di ipotesi preregistrate.

**AUROC (tutti i casi, senza appaiamento).** C contro B su P−S: da 0.481 a 0.641 (massimo M2 su Mistral). C contro A+B su P−S: da 0.468 a 0.725 (massimo M2 su Qwen, la sonda collassata, quindi da non leggere come segnale). Su S−S, C contro A+B da 0.505 a 0.733.

**Confronto con il notebook A sulle stesse 800 coppie P−S.**

| Modello | p(UNKNOWN) `env_sirin` | M2 | M2-senzaℓ2 | M3 (giudice unico) | M4-LoRA | M4-lin |
|---|---|---|---|---|---|---|
| Qwen | 0.980 | 0.450 (NON VALUTABILE) | 0.450 | 0.693 | — | — |
| Mistral | 0.779 | 0.646 | 0.611 | 0.693 | — | — |
| OLMo | 0.698 | 0.506 | 0.507 | 0.693 | — | — |
| Llama | 0.738 | 0.497 | 0.490 | 0.693 | 0.823 | 0.481 |

M3 è un giudice unico (Qwen3-4B) che legge il prompt: lo stesso W vale per tutte le righe.

**Esplorativo, fatto dopo aver visto i risultati: varianti logicamente equivalenti.** Ogni famiglia ha due varianti, POS e NOT. NOT nega l'atomo nella regola («the scaffold is not reserved») e inverte il valore del fatto noto, quindi lo stato logico di B e di C resta lo stesso. Cambiano però due cose insieme: la polarità della regola e quale dei due casi contiene «It is false that». Un metodo che segue solo lo stato logico dovrebbe dare lo stesso W nelle due varianti; la trasformazione non isola invece una causa esclusivamente lessicale. W per cella (134 o 132 coppie, senza IC; script `strumenti_resoconto_B/esplorativo_variante_B.py`):

| Modello | Metodo | AND POS | AND NOT | OR POS | OR NOT | IMPLIES POS | IMPLIES NOT | media \|POS − NOT\| |
|---|---|---|---|---|---|---|---|---|
| Qwen | p(UNKNOWN) | 0.99 | 0.95 | 1.00 | 1.00 | 1.00 | 0.94 | 0.04 |
| Qwen | M2 | 0.03 | 0.76 | 1.00 | 0.06 | 0.85 | 0.00 | 0.84 |
| Qwen | M2-senzaℓ2 | 0.38 | 0.20 | 0.79 | 0.66 | 0.24 | 0.42 | 0.17 |
| Mistral | p(UNKNOWN) | 1.00 | 0.96 | 0.99 | 0.22 | 0.96 | 0.54 | 0.41 |
| Mistral | M2 | 0.50 | 0.76 | 1.00 | 0.70 | 0.67 | 0.23 | 0.33 |
| Mistral | M2-senzaℓ2 | 0.69 | 0.81 | 1.00 | 0.54 | 0.36 | 0.26 | 0.23 |
| OLMo | p(UNKNOWN) | 1.00 | 1.00 | 0.65 | 0.05 | 0.96 | 0.52 | 0.35 |
| OLMo | M2 | 0.75 | 0.43 | 0.28 | 0.60 | 0.48 | 0.50 | 0.23 |
| OLMo | M2-senzaℓ2 | 0.33 | 0.19 | 0.84 | 0.87 | 0.61 | 0.20 | 0.19 |
| Llama | p(UNKNOWN) | 0.63 | 0.23 | 1.00 | 0.99 | 0.76 | 0.82 | 0.16 |
| Llama | M2 | 0.00 | 0.01 | 1.00 | 0.93 | 0.97 | 0.08 | 0.32 |
| Llama | M2-senzaℓ2 | 0.00 | 0.01 | 1.00 | 0.82 | 0.93 | 0.17 | 0.32 |

Nelle celle AND NOT, OR POS e IMPLIES POS il caso C ha un «It is false that» in più di B; nelle altre tre ne ha uno in meno. Sulla sonda originale di Qwen, che è collassata, il segno della differenza C − B concorda con quello della differenza di «It is false that» nel 92.0% delle 800 coppie (per M2-senzaℓ2 su Qwen: 46.3%), ma su differenze di punteggio molto piccole (mediana 0.00006, massimo 0.00024): è un indizio, non una spiegazione. Gli altri metodi mostrano differenze grandi fra varianti equivalenti in quasi tutti i modelli; lo fa anche p(UNKNOWN) di Mistral e di OLMo (OR: 0.99 contro 0.22; 0.65 contro 0.05). Solo p(UNKNOWN) di Qwen è stabile (0.04). L'analisi documenta una sensibilità alla trasformazione, senza dimostrare che il modello o la sonda usino soltanto una scorciatoia. È coerente con quanto visto nello Step 1 (sonde sensibili alla forma), ma resta un'osservazione a posteriori, senza IC e senza regola fissata prima, separata dagli esiti preregistrati.

## Lettura

1. **Preregistrato: per le sonde di answerability di SIRIN addestrate su SQuAD 2.0 il criterio generale di HM1 (3 su 4) non è raggiunto, né nella configurazione originale né nella variante senza ℓ2.** Questo non dimostra l'assenza del segnale: HM1 è confermata su Mistral, con entrambe.
2. **Preregistrato: nel confronto principale P−S nessuna delle due fa meglio di p(UNKNOWN)** in nessun modello valutabile; tutti i ΔW su P−S sono negativi con l'IC sotto 0. Nel simbolico (S−S) ci sono alcuni vantaggi descrittivi.
3. **Sul controllo positivo: con la penalità ℓ2 fissa del trainer di SIRIN la sonda di Qwen collassa anche con 1000 + 200 esempi**, mentre M2-senzaℓ2 supera HM0 su Qwen (0.881). Sugli altri tre modelli le due configurazioni hanno HM0 simili (scarti da 0.001 a 0.016). È un risultato sull'implementazione SIRIN e sulla configurazione adottata, non sul metodo in astratto.
4. **Secondario (nominale, IC non corretti): M2-senzaℓ2 supera HM1_f su OR in 4 modelli su 4**, ma su AND e IMPLIES in al massimo 1. Le differenze tra famiglie sono forti (H ≥ 0.20 in 6 celle su 8; Llama AND contro OR: 0.004 contro 0.963).
5. **Esplorativo:** su varianti logicamente equivalenti (POS/NOT) i W cambiano molto, per le sonde e in parte per p(UNKNOWN) di Mistral e OLMo. Questo documenta una sensibilità alla trasformazione (polarità della regola e posizione del fatto falso insieme), non una causa solo lessicale né l'uso esclusivo di una scorciatoia. Per separare le due componenti servirebbe un confronto preregistrato.

## Limiti

- Riserva: 1000 + 200 esempi per modello invece di 2000 + 400, per la regola sulla RAM.
- M2-senzaℓ2 è stata definita dopo la diagnostica SQuAD su Qwen. Le sue regole sono preregistrate, ma la scelta della variante non è indipendente da quella diagnostica.
- Prima del completo abbiamo visto i punteggi della prova tecnica di **entrambe le sonde**, M2 e M2-senzaℓ2 (Qwen, 200 + 40 esempi SQuAD, 9 storie). Le 9 storie della prova sono **comprese nelle 200 del completo**. Nel completo i punteggi si ricalcolano e quelli della prova non si aggregano agli esiti, ma i casi sono condivisi. Il campione principale resta quello già fissato (200 storie, 800 coppie P−S).
- Due metodi per 4 modelli e 3 famiglie, con IC non corretti per la molteplicità.
- 4 modelli tra 7 e 12B, storie sintetiche di un solo tipo, solo inglese. Il confronto con l'articolo di SIRIN è solo descrittivo (modello, dati e configurazione diversi).
- L'analisi per variante POS/NOT è a posteriori: si riporta solo come descrittivo.

## Prossimo passo

Riepilogo unico del Test M (notebook A e B), poi il Test C (`Protocollo_testC_v3.md`; la selezione v3 è in attesa dei risultati, il notebook del Test C usa le sonde di questo completo, entrambe).
