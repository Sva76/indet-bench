# Risultati: p(UNKNOWN) su modelli più grandi (completo, N-notebook-4)

Versione v1.1, 15 novembre 2026. **Approvata da Simona (13:45) a condizione che le classificazioni siano oneste e sostenute dai dati**: in v1.1 ogni classificazione dice se è sostenuta dai dati o solo un'ipotesi, e una frase di §3 non sostenuta dai dati è stata tolta. Esecuzione: notebook `IndetBench_modelli_grandi_v4.ipynb` (N-notebook-4), modalità **completo**, A100-SXM4-80GB, transformers 5.22.1, torch 2.14.1+cu130, bitsandbytes 0.50.2, repository al commit `2aa1f62` (calcolo invariato rispetto a `c086e65`). Due sessioni: la prima ha calcolato Qwen3-8B, Qwen3-32B, OLMo-2-32B e Gemma-2-27B; Llama-3.3-70B è fallito con errore 403 (accesso gated non ancora concesso). La seconda sessione ha saltato i quattro modelli già completati e ha calcolato solo Llama. I `punteggi.csv` dei quattro modelli sono identici byte per byte nei due ZIP.

**Statuto.** I risultati sono **esplorativi**, come quelli del 14 novembre. Non sono una validazione indipendente del metodo. «CONFIRMED» è l'esito della regola HU1/HI1 applicata dal codice (W ≥ 0.60 e limite inferiore dell'IC95 > 0.5), non una conferma del metodo. Il confronto con il modello più piccolo della stessa famiglia è **descrittivo**: nessun test fra modelli è stato preregistrato. Metodo, soglie, prompt e regola sulla massa delle etichette sono quelli fissati prima dei dati.

## Sintesi

- **Tecnica.** I cinque modelli hanno girato su 800 coppie su 800, con prompt identici fra i modelli e nessuna esclusione per lunghezza. Qwen3-8B riproduce il Test U2 su tutte le 1600 righe. La regola sulla massa delle etichette è superata da tutti (mediana ≥ 0.999). Il ricalcolo indipendente dai punteggi grezzi coincide con il report.
- **Scala, a famiglia fissa (descrittivo).** OLMo passa da 0.694 (7B) a 0.886 (32B), Gemma da 0.818 (9B) a 0.870 (27B), Llama da 0.746 (8B, bf16) a 0.908 (70B in 4 bit). Qwen resta a 0.975, già vicino al massimo con l'8B.
- **Rispetto alle baseline (descrittivo):** nessuna superiorità generale. p(UNKNOWN) è sopra la migliore baseline indipendente in Qwen3-32B (+0.085) e Gemma-2-27B (+0.051), sotto in OLMo-2-32B (−0.034) e Llama-3.3-70B (−0.080).
- **Struttura delle coppie.** La debolezza di Gemma su IMPLIES resta con la scala (0.61). Anche Llama è più debole su IMPLIES (0.78). La variante NOT non è più sempre più debole di POS: in Qwen3-32B e Llama-70B è il contrario.

## 1. Funziona tecnicamente?

| Controllo | Esito |
|---|---|
| GPU e versione | A100-SXM4-80GB per tutti i modelli, N-notebook-4, stesso commit |
| Controllo CPU dei 4 W del Test U2 (cella 4b) | superato 4/4: 0.975, 0.7825, 0.69375, 0.74625, conteggi per gold identici |
| Qwen3-8B, controllo positivo | 24 valori con scarto 8·10⁻¹⁷. Sull'intero completo **1600 righe su 1600** uguali al Test U2 (scarto massimo 3·10⁻²¹), risposte uguali 1600/1600, W 0.975 = Test U2 |
| Revisioni | verificate per tutti: Qwen3-32B `9216db57`, OLMo-2-32B `b9602434`, Gemma-2-27B `aaf20e6b`, Llama-3.3-70B `6f6073b4` |
| Pesi | bfloat16 per Qwen, OLMo, Gemma; **Llama in nf4 4 bit** (bitsandbytes 0.50.2, calcolo bfloat16), registrato nel manifest |
| Righe e coppie | 1600 righe per modello, row_id = benchmark congelato, 800 coppie valide per tutti |
| Identità delle coppie | stesse impronte (dati `ba7ab202…`, benchmark `906c01bf…`) per i 5 modelli; 800 coppie comuni |
| Esclusioni per lunghezza | 0 per tutti |
| Tokenizer | `token_type_ids` non usati da nessun modello; testi e tokenizzazione identici su 1600 prompt su 1600 |
| Copertura delle etichette (regola nuova, 24 righe) | massa mediana: Qwen3-8B 1.000, Qwen3-32B 1.000, OLMo 0.999, Gemma 1.000, Llama 1.000; token più probabile fra le etichette nel 100% dei casi; nessun modello NON MISURABILE |
| Massa sull'insieme completo | mediana ≥ 0.999 per tutti. Righe con massa < 0.90: 0 per quattro modelli, **6 su 1600 per Llama (0.375%)**, sotto la soglia di cautela del 5% |
| Risposte ALTRO | 0 per quattro modelli, **2 per Llama** (vedi §4) |
| Ricalcolo indipendente (pandas, senza il codice di indetbench) | W, accuratezze e soglia identici al report per i 5 modelli; IC entro 0.003 (bootstrap diverso) |

## 2. Misura ciò che intendiamo?

| Modello | Acc. B | gold NO | gold YES | UNKNOWN su B | UNKNOWN su C | W, nessuna risposta UNKNOWN | W AND | W OR | W IMPLIES | W POS | W NOT | W prima | W ultima |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B (controllo) | 1.000 | 1.000 | 1.000 | 0.0% | 25.3% | 0.964 | 0.963 | 0.996 | 0.966 | 0.995 | 0.955 | 0.955 | 0.995 |
| Qwen3-32B | 0.995 | 0.985 | 1.000 | 0.0% | 24.4% | 0.969 | 1.000 | 1.000 | 0.924 | 0.950 | **1.000** | 0.975 | 0.975 |
| OLMo-2-32B-Instruct | 0.990 | 1.000 | 0.985 | 0.8% | 19.4% | 0.872 | **0.795** | 0.981 | 0.883 | 0.913 | 0.860 | 0.828 | 0.945 |
| Gemma-2-27B-it | 0.929 | 1.000 | 0.893 | 7.1% | 55.1% | 0.797 | 1.000 | 1.000 | **0.606** | 0.913 | 0.828 | 0.795 | 0.945 |
| Llama-3.3-70B (4 bit) | 1.000 | 1.000 | 1.000 | 0.0% | 27.8% | 0.882 | 1.000 | 0.944 | **0.777** | 0.858 | **0.958** | 0.835 | 0.980 |

- **Soglia di competenza (vincolante):** superata da tutti con margine ampio (minimo 0.893, Gemma su gold YES).
- **Non dipende solo dalla risposta generata.** Sulle coppie in cui né B né C hanno risposta UNKNOWN, W resta 0.80–0.97.
- **Lunghezza:** W 0.5 per costruzione, nessuna coppia esclusa.
- **Famiglie (descrittivo):** differenze ≥ 0.20 in Gemma (IMPLIES 0.61, come il 9B con 0.59) e in Llama (IMPLIES 0.78). In OLMo la famiglia più debole è AND (0.80). Come il 14 novembre, la famiglia più debole cambia da modello a modello.
- **Variante NOT:** più debole di POS in Qwen3-8B, OLMo e Gemma; **più forte** in Qwen3-32B (+0.050) e Llama-70B (+0.100). Il risultato del 14 novembre «NOT < POS in 5 modelli su 5» non si estende ai modelli grandi.
- **Posizione (descrittivo):** W più basso quando l'elemento indeterminato è nella prima posizione in OLMo, Gemma e Llama (da −0.12 a −0.15); pari in Qwen3-32B. Il 14 novembre l'effetto non aveva un segno costante (Falcon e Gemma-9B al contrario).
- **Gemma-2-27B risponde UNKNOWN molto più spesso**: 55% sui C (il 9B 25%) ma anche 7.1% sui B (il 9B 1.8%). Gold YES scende a 0.893.

### 2.1 Variante NOT: dati per la questione aperta (descrittivo)

Differenza W(NOT) − W(POS), appaiata per storia (ogni storia ha 2 coppie NOT e 2 POS), IC95 bootstrap sulle 200 storie (2000 ricampionamenti, seme 20261108). Ricalcolata dai punteggi grezzi del Test U2, del 14 e del 15 novembre.

| Famiglia | Modello piccolo: NOT − POS [IC95] | Modello grande: NOT − POS [IC95] |
|---|---|---|
| Qwen3 (stessa versione) | 8B: −0.040 [−0.060, −0.020] | 32B: **+0.050 [+0.027, +0.080]** |
| Llama (3.1 → 3.3, il 70B in 4 bit) | 3.1-8B: −0.118 [−0.178, −0.058] | 3.3-70B: **+0.100 [+0.058, +0.142]** |
| OLMo-2 (1124 → 0325) | 7B: −0.358 [−0.410, −0.302] | 32B: −0.052 [−0.100, −0.010] |
| Gemma-2 (stessa versione) | 9B: −0.090 [−0.142, −0.040] | 27B: −0.085 [−0.128, −0.045] |
| solo piccoli | Mistral-Nemo 12B −0.405 [−0.465, −0.348]; Falcon3-7B −0.138 [−0.178, −0.102]; Phi-4 14B −0.092 [−0.130, −0.060] | — |

**Che cosa dicono questi dati.**
- La generalizzazione del 14 novembre («NOT più debole di POS in tutti i modelli») **non regge**: in Qwen3-32B e Llama-3.3-70B la differenza è positiva, con IC95 che esclude 0.
- Fra modelli della stessa famiglia il segno si inverte con IC95 che escludono 0 da parti opposte (Qwen 8B/32B, Llama 8B/70B). Quindi il cambio di segno **non si spiega con il caso nel ricampionamento delle 200 storie**. Questo non dice niente su altre storie o altre formulazioni.
- Con la dimensione l'effetto si riduce in tre famiglie su quattro, ma non in Gemma (−0.090 e −0.085). In Qwen3-32B il segno positivo viene in parti uguali da NOT che sale (0.955 → 1.000, +0.045) e da POS che scende (0.995 → 0.950, −0.045). (Correzione del 15 nov dopo la revisione: la versione precedente attribuiva il segno soprattutto a POS.)

**Che cosa non dicono.**
- Non permettono di distinguere uno «scalino» (un cambio brusco oltre una certa dimensione) da un cambio graduale. Abbiamo **due punti per famiglia**, e due punti sono compatibili con entrambi.
- Non permettono di attribuire il cambio alla dimensione. In Llama e OLMo cambiano anche versione e dati di addestramento, e il Llama grande è quantizzato. Solo Qwen3 e Gemma-2 confrontano la stessa versione, e danno risultati diversi fra loro.
- «Più campioni» può voler dire due cose diverse. Più **coppie o storie**: il numero di coppie è lo stesso (800) a ogni scala, e gli IC sono già stretti abbastanza da separare i segni. Più **modelli**: è quello che manca per vedere la forma dell'andamento.

**Disegno che servirebbe (test dedicato, da preregistrare):** una serie di dimensioni della **stessa famiglia e versione**, per esempio Qwen3 0.6B, 1.7B, 4B, 8B, 14B e 32B, tutti Apache-2.0. Con questa curva si può vedere se il segno cambia in un punto (scalino) o gradualmente. Servirebbe anche un insieme di **storie nuove**, per verificare che l'andamento non dipenda dalle 200 storie congelate. Il criterio (per esempio NOT − POS per dimensione, con IC95, e la forma attesa di uno scalino) va fissato prima dei dati.

## 3. Aggiunge rispetto alle baseline? (solo descrittivo)

Baseline indipendenti dalle stesse uscite: entropia normalizzata, meno p massima normalizzata, risposta generata UNKNOWN (0/1). ΔW = W di p(UNKNOWN) − W della migliore baseline indipendente, appaiato per storia, IC95 bootstrap **descrittivo**, non un test preregistrato.

| Modello | W p(UNKNOWN) [IC95] | entropia | meno p max | risposta UNKNOWN | ΔW sulla migliore [IC95 descrittivo] | W modello piccolo stessa famiglia |
|---|---|---|---|---|---|---|
| Qwen3-8B (controllo) | 0.975 [0.964, 0.985] | 0.949 | 0.948 | 0.626 | +0.026 [+0.013, +0.041] (entropia) | — |
| Qwen3-32B | 0.975 [0.961, 0.988] | 0.890 | 0.890 | 0.622 | **+0.085 [+0.063, +0.109]** (entropia) | Qwen3-8B 0.975 (Test U2) |
| OLMo-2-32B-Instruct | 0.886 [0.861, 0.910] | 0.920 | 0.919 | 0.593 | **−0.034 [−0.051, −0.018]** (entropia) | OLMo-2-1124-7B 0.694 (Test U2) |
| Gemma-2-27B-it | 0.870 [0.839, 0.900] | 0.819 | 0.816 | 0.740 | **+0.051 [+0.024, +0.079]** (entropia) | Gemma-2-9B 0.818 (14 nov) |
| Llama-3.3-70B (4 bit) | 0.908 [0.889, 0.928] | 0.988 | 0.988 | 0.639 | **−0.080 [−0.100, −0.061]** (entropia) | Llama-3.1-8B 0.746 (Test U2, bf16) |

La «p(UNKNOWN) normalizzata» resta nel rapporto per trasparenza (decisione di Simona del 14 novembre). Con massa ≈ 1 coincide con p(UNKNOWN) per tutti e cinque: 0.975, 0.975, 0.886, 0.870, 0.908.

**Lettura.** Con la scala p(UNKNOWN) separa meglio C da B in tre famiglie su quattro, ma non diventa in modo generale migliore delle misure generiche di incertezza. Nei modelli grandi il segno di ΔW è diviso a metà (due positivi, due negativi). Questi dati non mostrano che p(UNKNOWN) contenga informazione specifica sull'indeterminatezza oltre all'incertezza generica della risposta. Con quattro modelli e una sola esecuzione ciascuno non si può dire da che cosa dipenda il segno di ΔW.

**Llama-70B, dove p(UNKNOWN) perde (descrittivo, controllato sui grezzi).** p(UNKNOWN) dà C ≤ B in 74 coppie su 800. In tutte e 74 il modello risponde NO al caso C con probabilità quasi 1 (p(UNKNOWN) mediana 2·10⁻¹²). In 64 di queste la «meno p massima» vince lo stesso, perché il modello è comunque un po' meno sicuro sul C (1 − p max mediana 3·10⁻⁶) che sul B (1·10⁻⁹). **Fatto:** in queste 74 coppie la poca probabilità che il modello non dà alla risposta scelta va a YES, non a UNKNOWN, e una parte del vantaggio delle baseline viene da differenze di probabilità molto piccole in risposte quasi certe. **Non verificato:** perché succeda (comportamento del modello o effetto della quantizzazione in 4 bit). Non sappiamo se a precisione piena queste differenze sarebbero uguali.

## 4. Anomalie e classificazione proposta

Per ogni anomalia la colonna «Base» dice se la categoria è **sostenuta dai dati** (le prove la determinano) oppure **non classificata** (più categorie restano possibili e i dati non permettono di scegliere). Le cause scritte come «ipotesi» non sono state verificate.

| Modello | Anomalia | Categoria | Base | Causa | Prove | Controlli fatti | Cosa resta incerto |
|---|---|---|---|---|---|---|---|
| Llama-70B | errore 403 nella prima sessione | **problema tecnico** (accesso), risolto | sostenuta dai dati | licenza gated non ancora concessa all'account del token (dal messaggio di errore) | messaggio di Hugging Face; dopo l'accesso il modello gira | rilancio; altri modelli saltati, punteggi identici | — |
| Llama-70B | una baseline indipendente supera p(UNKNOWN) (meno p max 0.988 contro 0.908) | **evidenza scientifica** (descrittiva): su questo modello p(UNKNOWN) non è la misura migliore | sostenuta dai dati (è una misura, non un'interpretazione) | ipotesi: comportamento del modello o quantizzazione 4 bit; non verificata | ΔW −0.080 [−0.100, −0.061]; 74 coppie perse, tutte con C = NO quasi certo | ricalcolo indipendente; analisi delle coppie perse (§3) | perché succeda; risultato a precisione piena; non è un test preregistrato |
| Llama-70B | W molto diverso fra famiglie (AND 1.00, IMPLIES 0.78) | non classificata: comportamento del modello o limite del protocollo | i dati non permettono di scegliere | non nota | W per famiglia | nessuna esclusione; soglia superata | se dipende dalla formulazione IMPLIES o dal modello |
| Llama-70B | 2 risposte ALTRO e 6 righe con massa < 0.90 (sotto la soglia di cautela del 5%, non segnalate in automatico) | **comportamento del modello** | sostenuta dai dati per la parte tecnica: prompt, tokenizer e revisione controllati senza difetti, e il testo generato è leggibile («MAYBE is not an option,») | perché il modello scriva questo testo non è noto | le 6 righe sono tutte casi C, variante NOT, posizione ultima; le 2 ALTRO hanno massa 0.47 e 0.41 | W senza le 6 coppie: 0.9075, invariato | il motivo del testo generato |
| OLMo-2-32B | una baseline indipendente supera p(UNKNOWN) (entropia 0.920 contro 0.886) | **evidenza scientifica** (descrittiva) | sostenuta dai dati (è una misura) | non nota | ΔW −0.034 [−0.051, −0.018] | ricalcolo indipendente | non è un test preregistrato |
| Gemma-2-27B | W molto diverso fra famiglie (AND e OR 1.00, IMPLIES 0.61) | non classificata: comportamento del modello o limite del protocollo | i dati non permettono di scegliere | non nota; lo stesso schema c'è nel 9B (0.59) | W per famiglia in due dimensioni del modello | nessuna esclusione; soglia superata | se dipende dalla formulazione IMPLIES («in every case except one») o dalla famiglia Gemma |
| tutti | variante NOT non coerente: più debole di POS in 3 modelli, più forte in 2 (non segnalato in automatico) | non classificata: limite del protocollo o comportamento del modello | i dati non permettono di scegliere | non nota | tabella §2 | — | entra nella questione aperta sulla negazione (decisione del 14 nov) |

## 5. Cosa si può e non si può dire

- **Si può dire, come risultato esplorativo:** sul benchmark congelato in prosa (800 coppie), p(UNKNOWN) ordina C sopra B anche nei modelli più grandi di quattro famiglie (Qwen3-32B, OLMo-2-32B, Gemma-2-27B, Llama-3.3-70B in 4 bit). Nelle tre famiglie in cui il modello piccolo non era già al massimo, il W del modello grande è più alto. Il controllo positivo riproduce il Test U2 esattamente.
- **Non si può dire:**
  - che il metodo sia validato in modo indipendente;
  - che p(UNKNOWN) sia superiore alle baseline dalle uscite (in OLMo-32B e Llama-70B è inferiore);
  - che la crescita di W sia un effetto della dimensione: i modelli piccoli e grandi differiscono anche per versione e dati di addestramento (es. OLMo-2-1124 contro OLMo-2-0325, Llama-3.1 contro 3.3), e non c'è un test fra modelli;
  - niente su Llama-70B a precisione piena: il risultato è «70B quantizzato in 4 bit»;
  - niente sui modelli reasoning (parte B, non eseguita).
- **Incertezze generali:** una sola esecuzione per modello; un solo formato e un solo insieme di storie; dipendenza dalla famiglia, dalla variante e dalla posizione.

## 6. Decisioni per Simona

1. **Approvazione: fatta** (Simona, 15 nov 13:45), con la condizione che le classificazioni siano oneste e sostenute dai dati; v1.1 applica la condizione (§4, §3).
2. **Variante NOT: decisa (Simona, 15 nov 13:48).** La regola «NOT più debole di POS» è falsificata dai modelli più grandi e non si usa più. Il dato è aggiunto alla questione aperta (§2.1). Resta aperta la domanda di Simona: serve un campione più ampio, oppure l'effetto NOT cambia con la scala, come uno scalino? I dati attuali non permettono di distinguere le due ipotesi; il disegno che servirebbe è in §2.1.
3. **Parte B (modelli reasoning): decisa (Simona, 15 nov 14:11).** Protocollo `Protocollo_parteB_reasoning_v1.md` approvato con le 5 scelte raccomandate; notebook `IndetBench_reasoning_v1.ipynb` (R-notebook-1).

File: dati `PHI/Step3_modelli_nuovi/modelli_grandi_risultati/indetbench_modelli_grandi_completo_20261115.zip` (SHA-256 `137024c3…`), ricalcolo `PHI/Step3_modelli_nuovi/modelli_grandi_risultati/ricalcolo_grandi.py`.
