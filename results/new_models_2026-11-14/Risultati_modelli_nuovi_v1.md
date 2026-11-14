# Risultati: p(UNKNOWN) su modelli di famiglie nuove (completo, N-notebook-3)

Versione v1, 14 novembre 2026, **approvata da Simona (18:56)**. Esecuzione: notebook `IndetBench_modelli_nuovi_v3.ipynb` (N-notebook-3), modalità **completo**, A100-SXM4-40GB, transformers 5.22.1, torch 2.14.1+cu130, repository al commit `c086e65`.

**Statuto.** Tutti i risultati sui modelli nuovi sono **esplorativi**. Non sono una validazione indipendente del metodo. Quando qui si scrive «CONFIRMED», si intende l'esito della regola HU1/HI1 applicata dal codice (W ≥ 0.60 e limite inferiore dell'IC95 > 0.5). Non è una conferma del metodo in senso generale. Metodo, soglie e prompt sono quelli fissati prima dei dati e non sono stati modificati dopo.

## Sintesi

- **Tecnica.** I cinque modelli hanno girato su 800 coppie su 800, con prompt identici fra i modelli e nessuna coppia esclusa per lunghezza. Qwen3-8B riproduce il Test U2 su tutte le 1600 righe. Il ricalcolo indipendente dai punteggi grezzi coincide con il report.
- **Yi-1.5-9B-Chat: problema tecnico.** Al primo token la probabilità totale di YES/NO/UNKNOWN è circa 2·10⁻⁶ (mediana), mentre le risposte generate sono etichette corrette al 99%. Il p(UNKNOWN) misurato quindi non è la quantità definita dal protocollo. **Decisione di Simona (14 nov, 18:51): Yi è NON VALUTABILE per motivo tecnico**, anche se il codice dà CONFIRMED (W 0.86). Il valore resta archiviato ma non entra nei risultati.
- **Gemma-2-9B, Falcon3-7B e Phi-4 (14B):** soglia di competenza superata e regola soddisfatta. I W sono 0.818 [0.788, 0.848], 0.931 [0.911, 0.950] e 0.944 [0.924, 0.963]. È un sostegno esplorativo al fatto che p(UNKNOWN) ordina C sopra B in prosa anche in tre famiglie nuove.
- **Rispetto alle baseline (descrittivo):** p(UNKNOWN) **non** aggiunge in modo generale rispetto a misure generiche di incertezza dalle stesse uscite. Falcon è leggermente sopra l'entropia (+0.031), Phi-4 è pari alla «meno p massima», Gemma è sotto l'entropia (−0.074). Non si può dire che p(UNKNOWN) sia superiore alle baseline.
- **Dipendenza dalla struttura delle coppie:** forte in alcuni modelli. Gemma ha W 0.59 su IMPLIES e 1.00 su AND. La variante NOT ha W più basso di POS in tutti i modelli.

## 1. Funziona tecnicamente?

| Controllo | Esito |
|---|---|
| Modalità e versione | `completo`, N-notebook-3, stesso commit e stessa GPU per tutti i 5 modelli |
| Controllo CPU dei 4 W del Test U2 (cella 4b) | superato 4/4: 0.975, 0.7825, 0.69375, 0.74625, con conteggi per gold identici |
| Qwen3-8B, controllo positivo | 24 valori con scarto 8·10⁻¹⁷. Sull'intero completo: **1600 righe su 1600** uguali al Test U2 (scarto massimo 3·10⁻²¹), risposte uguali 1600/1600, W 0.975 = Test U2 |
| Righe e coppie | 1600 righe per modello, nessun duplicato, row_id = benchmark congelato, 800 coppie valide per tutti |
| Identità delle coppie | stesse impronte dei prompt (dati `ba7ab202…`, benchmark `906c01bf…`) per i 5 modelli; 800 coppie comuni |
| Esclusioni per lunghezza | 0 per tutti i modelli: B e C hanno lo stesso numero di token in tutte le coppie |
| Tokenizer | nessun modello usava `token_type_ids`, quindi l'adattamento non ha avuto effetto; testi e tokenizzazione identici su 1600 prompt su 1600 |
| Risposte ALTRO | 0 per tutti |
| Massa YES+NO+UNKNOWN al primo token | Qwen 1.00, Gemma 1.00, Falcon 1.00 (mediana), Phi-4 0.99 (2.9% delle righe < 0.90, sotto la soglia di cautela del 5%), **Yi ≈ 2·10⁻⁶ (100% delle righe < 0.90)** |
| Ricalcolo indipendente (pandas, senza il codice di indetbench) | W, accuratezze e soglia identici al report per i 5 modelli; IC entro 0.003 (bootstrap diverso) |

### Yi-1.5-9B-Chat: anomalia tecnica

- **Fatti.** La massa sulle etichette al primo token ha mediana 2.2·10⁻⁶ e massimo 2.0·10⁻⁵. Le risposte generate però sono etichette leggibili (0 ALTRO) e corrette sui B al 99.1%. Il primo token generato non è quindi fra quelli usati per misurare p(YES), p(NO) e p(UNKNOWN). In più, gli ID delle etichette sono 3 per etichetta invece di 6: le varianti con e senza spazio iniziale finiscono sullo stesso primo token.
- **Causa ipotizzata (non verificata).** Il tokenizer di Yi (SentencePiece) aggiunge lo spazio iniziale quando codifica la parola isolata, quindi «YES» e « YES» danno lo stesso token «▁YES». Dopo `<|im_start|>assistant\n`, invece, il modello genera la forma senza spazio iniziale, che non è fra le 6 varianti. Le varianti sono la regola del Test U2: per i quattro modelli originali coprivano il token generato, e infatti lì la massa era ≈ 1.
- **Conseguenza.** Il W 0.86 di Yi è calcolato su probabilità residue di token che il modello non usa per rispondere. Non misura ciò che il protocollo intende.
- **Classificazione proposta:** problema tecnico (tokenizzazione delle etichette), emerso da un limite del protocollo: la massa bassa è solo una «cautela», non blocca il verdetto. Il notebook l'ha segnalata in automatico («massa bassa 100%» e «normalizzata diversa da p(UNKNOWN)»), ma il verdetto del codice non tiene conto della massa.
- **Controlli da fare** (diagnostici, senza toccare i risultati):
  1. stampare i token di `label_ids` di Yi e il primo token generato su una decina di righe;
  2. verificare quale token corrisponde a «YES» quando segue il prefisso dell'assistente.
- **Cosa resta incerto:** la causa precisa finché non si fa il controllo 1. Resta incerto anche se una correzione (per esempio, ricavare gli ID delle etichette dalla tokenizzazione del prompt completo seguito dall'etichetta) darebbe un W diverso. Una correzione sarebbe una variante del metodo decisa dopo i dati: andrebbe documentata come tale ed eseguita a parte, senza sostituire questo risultato.

## 2. Misura ciò che intendiamo?

| Modello | Accuratezza B | gold NO | gold YES | UNKNOWN su B | UNKNOWN su C | W, nessuna risposta UNKNOWN | W AND | W OR | W IMPLIES | W POS | W NOT |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B (controllo) | 1.000 | 1.000 | 1.000 | 0.0% | 25.3% | 0.964 | 0.963 | 0.996 | 0.966 | 0.995 | 0.955 |
| Gemma-2-9B-it | 0.945 | 1.000 | 0.917 | 1.8% | 24.9% | 0.807 | 1.000 | 0.858 | **0.591** | 0.863 | 0.773 |
| Falcon3-7B-Instruct | 0.961 | 1.000 | 0.942 | 1.1% | 28.0% | 0.913 | 0.993 | **0.806** | 0.996 | 1.000 | 0.863 |
| Phi-4 | 0.994 | 1.000 | 0.991 | 0.5% | 34.8% | 0.933 | 1.000 | 1.000 | 0.830 | 0.990 | 0.898 |
| Yi-1.5-9B-Chat (vedi §1) | 0.991 | 0.978 | 0.998 | 0.0% | 12.6% | 0.829 | 0.828 | 0.840 | 0.913 | 0.958 | 0.763 |

- **Soglia di competenza (vincolante):** superata da tutti, con margine ampio (minimo 0.917, Gemma su gold YES).
- **Non dipende solo dalla risposta generata.** Restringendo alle coppie in cui né B né C hanno risposta UNKNOWN, W resta alto: 0.81–0.96. Il segnale non è solo «il modello ha scritto UNKNOWN».
- **Lunghezza:** W 0.5 per costruzione, perché B e C hanno sempre la stessa lunghezza e nessuna coppia è stata esclusa.
- **Famiglie (descrittivo):** differenze ≥ 0.20 in Gemma (IMPLIES 0.59). Sono più piccole ma presenti in Falcon (OR 0.81) e Phi-4 (IMPLIES 0.83). La famiglia più debole cambia da modello a modello, quindi non c'è una famiglia «difficile» per tutti. Nei modelli originali la dipendenza dalla famiglia era già forte.
- **Variante NOT:** W più basso di POS in tutti e 5 i modelli (da −0.04 a −0.20). È coerente fra modelli ed è da tenere presente come possibile caratteristica delle coppie con negazione (limite del protocollo o comportamento dei modelli, da distinguere).

## 3. Aggiunge rispetto alle baseline? (solo descrittivo)

Le baseline indipendenti, calcolate dalle stesse uscite, sono: entropia normalizzata, meno p massima normalizzata, risposta generata UNKNOWN (0/1). ΔW = W di p(UNKNOWN) − W della migliore baseline indipendente, appaiato per storia, con IC95 bootstrap **descrittivo**. Non è un test preregistrato.

| Modello | W p(UNKNOWN) | entropia | meno p max | risposta UNKNOWN | ΔW sulla migliore [IC95 descrittivo] |
|---|---|---|---|---|---|
| Qwen3-8B (controllo) | 0.975 | 0.949 | 0.948 | 0.626 | +0.026 [+0.013, +0.041] (entropia) |
| Gemma-2-9B-it | 0.818 | 0.891 | 0.891 | 0.616 | **−0.074 [−0.099, −0.050]** (entropia) |
| Falcon3-7B-Instruct | 0.931 | 0.900 | 0.893 | 0.634 | +0.031 [+0.006, +0.056] (entropia) |
| Phi-4 | 0.944 | 0.939 | 0.944 | 0.671 | 0.000 [−0.018, +0.018] (meno p max) |
| Yi-1.5-9B-Chat (vedi §1) | 0.860 | 0.850 | 0.849 | 0.563 | non interpretabile |

La baseline «p(UNKNOWN) normalizzata» resta nel rapporto per trasparenza, secondo la decisione di Simona del 14 nov. Con massa ≈ 1 coincide con p(UNKNOWN): Qwen 0.975, Gemma 0.818, Falcon 0.931, Phi-4 0.944. Su Yi differisce (0.835 contro 0.860) proprio perché la massa non è ≈ 1.

**Lettura.** Nei tre modelli nuovi valutabili, p(UNKNOWN) separa C da B, ma un'incertezza generica sulle stesse uscite lo fa quasi altrettanto bene (Falcon, Phi-4) o meglio (Gemma). Questi dati non mostrano che p(UNKNOWN) contenga informazione specifica sull'indeterminatezza oltre all'incertezza generica della risposta.

## 4. Anomalie e classificazione proposta

| Modello | Anomalia (segnalazione automatica) | Categoria proposta | Causa ipotizzata | Prove | Controlli fatti | Cosa resta incerto |
|---|---|---|---|---|---|---|
| Yi | massa YES+NO+UNKNOWN < 0.90 nel 100% delle righe | **problema tecnico** (tokenizzazione delle etichette) | il token generato non è fra le varianti di etichetta (spazio iniziale di SentencePiece) | mediana 2·10⁻⁶; risposte corrette al 99%; 3 ID per etichetta invece di 6 | ricalcolo dai grezzi; distribuzione della massa | causa esatta (serve il controllo dei token); W con etichette corrette |
| Yi | p(UNKNOWN) normalizzata ≠ p(UNKNOWN) (0.835 contro 0.860) | conseguenza della precedente | massa sulle etichette ≈ 0 | come sopra | — | — |
| Gemma | W molto diverso fra famiglie (IMPLIES 0.59, AND 1.00) | comportamento del modello / limite del protocollo | da determinare | W per famiglia; accuratezza gold YES 0.917 | nessuna esclusione; soglia superata | se dipende dalla formulazione IMPLIES («in every case except one») o dal modello |
| Gemma | una baseline indipendente supera p(UNKNOWN) (entropia 0.891 contro 0.818) | **evidenza scientifica** (indebolisce la specificità di p(UNKNOWN)) | — | ΔW −0.074 [−0.099, −0.050] descrittivo | ricalcolo indipendente | non è un test preregistrato |
| Phi-4 | una baseline indipendente eguaglia p(UNKNOWN) (0.944 contro 0.944) | **evidenza scientifica** (nessun vantaggio) | — | ΔW 0.000 [−0.018, +0.018] | ricalcolo indipendente | — |
| tutti | W della variante NOT più basso di POS (non segnalato in automatico) | da classificare: limite del protocollo o comportamento | da determinare | 5 modelli su 5 | — | se è un effetto della negazione nella regola |

## 5. Cosa si può e non si può dire

- **Si può dire, come risultato esplorativo:** sul benchmark congelato in prosa (800 coppie), p(UNKNOWN) ordina C sopra B anche in Gemma-2-9B-it, Falcon3-7B-Instruct e Phi-4, tre famiglie diverse dalle quattro originali. Il controllo positivo Qwen3-8B riproduce il Test U2 esattamente, quindi l'ambiente non introduce differenze.
- **Non si può dire:**
  - che il metodo sia validato in modo indipendente;
  - che p(UNKNOWN) sia superiore alle baseline dalle uscite (in Gemma è inferiore);
  - che il risultato valga fuori dal formato in prosa o per le allucinazioni con contesto;
  - niente su Yi, che è NON VALUTABILE per motivo tecnico.
- **Incertezze generali:** una sola esecuzione per modello; un solo formato e un solo insieme di storie; dipendenza dalla famiglia e dalla variante; versioni Colab diverse da quelle originali (ininfluenti per Qwen, che coincide).

## 6. Decisioni per Simona

1. **Yi: deciso (Simona, 14 nov 18:51).** NON VALUTABILE per motivo tecnico. Resta facoltativa la cella diagnostica dei token (§1), utile solo se si vuole chiarire la causa o preparare una variante separata.
2. **Variante NOT: decisa (Simona, 14 nov 18:52).** La variante NOT dà un W più basso di POS in 5 modelli su 5. È registrata come **questione aperta emersa dai dati**, da studiare in futuro con un test dedicato e protocollo fissato prima. Non cambia nessun risultato di questo resoconto. Domanda da chiarire: l'effetto dipende dalla negazione nella regola (formulazione delle coppie, limite del protocollo) o dal modo in cui i modelli elaborano la negazione (comportamento del modello)?

File: dati `PHI/Step3_modelli_nuovi/completo_risultati/` (ZIP originale), ricalcolo `PHI/Step3_modelli_nuovi/ricalcolo_completo.py`.
