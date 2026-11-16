# Risultati: p(UNKNOWN) con il ragionamento acceso (parte B, completo, R-notebook-2)

Versione v2 (bozza da rivedere), 16 novembre 2026: aggiunge Phi-4-reasoning, completato nel rilancio dello stesso giorno. Esecuzione: notebook R-notebook-2 (`IndetBench_reasoning_v2.ipynb`; per la ripresa di Phi-4 `IndetBench_reasoning_v2_1.ipynb`, che cambia solo la gestione della memoria), modalità **completo**, **A100-SXM4-40GB**, transformers 5.22.1, torch 2.14.1+cu130, repository al commit `2aa1f62`. Protocollo: `Protocollo_parteB_reasoning_v1.md`, con la modifica della pipeline di misura del §8 (approvata il 15 novembre alle 18:15). Archivi in `completo_parte_B/`: `indetbench_reasoning_completo_20261116.zip` (Qwen3-8B, R1) e `indetbench_reasoning_completo_phi4_20261116.zip` (rilancio con Phi-4).

**Statuto.** I risultati sono **esplorativi**: non sono una validazione indipendente del metodo. «CONFIRMED» è l'esito della regola HR1 applicata dal codice (W ≥ 0.60 e limite inferiore dell'IC95 > 0.5), non una conferma del metodo. Un W più alto con il ragionamento non dimostra che il metodo funzioni meglio, e uno più basso non lo smentisce. Metodo, soglie, prompt e regola sulla massa sono quelli fissati prima dei dati.

**Che cosa manca.**
- **Qwen3-32B** non è stato eseguito: in bfloat16 richiede la A100-SXM4-80GB (§3 e §8 del protocollo), che Colab non assegna. HR2 secondaria resta quindi senza dati.

## Sintesi

- **Tecnica.** Qwen3-8B, Phi-4-reasoning e R1-Distill-Llama-8B hanno girato su 800 coppie su 800, senza esclusioni per lunghezza. Tutti i ragionamenti si sono chiusi da soli entro il budget, tranne 4 di Phi-4 su 1600. Phi-4 è stato ripreso dopo l'errore di memoria: le 1152 righe già misurate sono identiche nel risultato finale (scarto 0) e nella ripresa non c'è stato nessun nuovo errore di memoria. Il controllo della pipeline è superato (scarto 8·10⁻¹⁷, 24/24). Qwen3-8B senza ragionamento riproduce il Test U2 su **1600 righe su 1600**. Il ricalcolo indipendente di W dai `punteggi.csv` dà le stesse stime del report.
- **Qwen3-8B (principale).** Con il ragionamento acceso W = **1.000** [1.000, 1.000], senza ragionamento 0.975. HR2: ΔW = **+0.025** [0.015, 0.036], l'IC95 esclude 0, quindi secondo la regola «il ragionamento cambia W». È anche il massimo aumento possibile partendo da 0.975 (limite dichiarato prima dei dati, §3 del protocollo).
- **Da dove viene il segnale in Qwen3-8B acceso.** Dopo il ragionamento Qwen risponde UNKNOWN a 795 casi C su 800 e a 0 casi B su 800. La risposta generata da sola (UNKNOWN sì/no) dà già W 0.997. Con il ragionamento il segnale sta nella risposta esplicita, e p(UNKNOWN) non aggiunge nulla di misurabile rispetto alla risposta: è un effetto tetto.
- **Phi-4-reasoning (descrittivo).** W = **0.995** [0.990, 0.999], CONFIRMED. Come Qwen, dopo il ragionamento risponde UNKNOWN a 793 casi C su 800 e a nessun B. La risposta generata da sola arriva a 0.996, cioè **eguaglia p(UNKNOWN)**. La piccola differenza (0.0006) viene tutta da 7 casi C in cui il modello comincia con un avviso («Disclaimer: …») invece che con l'etichetta. È di nuovo un effetto tetto: il segnale sta nella risposta esplicita. Phi-4 senza ragionamento (14 novembre, pesi diversi) aveva W 0.944.
- **R1-Distill-Llama-8B (descrittivo).** W = **0.9225** [0.900, 0.944], CONFIRMED, sopra la migliore baseline indipendente (risposta UNKNOWN 0/1, W 0.787). Ci sono però due limiti. La massa sulle etichette è più bassa (mediana 0.837, 75.8% delle righe sotto 0.9), e 89 risposte su 1600 non sono leggibili come YES/NO/UNKNOWN. Inoltre le singole risposte dipendono molto dal campionamento: solo il 69–72% delle risposte coincide fra semi diversi, mentre il W per seme resta stabile (0.925–0.95).

## 1. Funziona tecnicamente?

| Controllo | Qwen3-8B | Phi-4-reasoning | R1-Distill-Llama-8B |
|---|---|---|---|
| GPU e versione | A100-SXM4-40GB, R-notebook-2, commit `2aa1f62` | stessa (ripresa con v2_1, stessa impronta) | stessa |
| Revisione | verificata (`b968826d`) | verificata (`1de18ec9`) | verificata |
| Controllo della pipeline (§5.1) | superato: scarto 8.3·10⁻¹⁷, risposte 24/24 | (si fa solo su Qwen) | (si fa solo su Qwen) |
| Ragionamento spento contro il Test U2 | **1600/1600** righe, scarto massimo 1.1·10⁻¹⁶, risposte uguali 1600/1600 | non previsto | non previsto |
| Controllo CPU dei 4 W del Test U2 | superato | superato (rilancio) | — |
| Tokenizer e prompt | 1600/1600 intatti in tutte e due le condizioni | 1600/1600 intatti (messaggio di sistema Microsoft del template, dichiarato) | 1600/1600 intatti |
| Coppie valide, esclusioni per lunghezza | 800, 0 | 800, 0 | 800, 0 |
| Chiusura del ragionamento | 1600/1600 chiusi da soli | 1596/1600 da soli, **4 al budget** (3 B, 1 C); coppie chiuse 796 ≥ 760, sensibilità solo chiuse W 0.995 | 1600/1600 chiusi da soli |
| Lunghezza del ragionamento (mediana B / C, massimo) | 251 / 303 token, massimo 3457 | 445 / 534.5 token, massimo 4096 | 303 / 354.5 token, massimo 2416 |
| Posizione della risposta dopo `</think>` | primo token non vuoto (1600/1600) | subito, posizione 0 (1600/1600) | primo token non vuoto (1600/1600) |
| Massa YES+NO+UNKNOWN (mediana su tutte le righe) | 1.000 | 1.000 (24 righe di controllo 1.000) | **0.837** (24 righe di controllo 0.855; regola ≥ 0.5 superata) |
| Righe con massa < 0.9 / < 0.5 | 0 / 0 | 27 (1.7%) / 14 | **75.8%** / 147 righe (9.2%) |
| Risposte ALTRO | 0 | 14 (7 B, 7 C) | **89** (25 B, 64 C) |
| Tempo | acceso 4605 s, spento 562 s | acceso 12 311 s (prima sessione, 1152 righe) + 4709 s (ripresa) | acceso 3184 s |
| Ripresa dopo l'errore di memoria | — | 1152 righe già misurate identiche nel risultato finale (scarto 0, risposte 1152/1152), manifest identico, 0 misure ripetute per memoria | — |

**Ricalcolo indipendente.** Ho ricalcolato W dai `punteggi.csv` con uno script separato da quello del notebook (`ricalcolo_parteB.py`, nella stessa cartella). Il W è definito come la media, sulle 200 storie, della quota di coppie con punteggio C > B (pareggio = 0.5). Le stime coincidono con il report: Qwen acceso 1.0000, spento 0.9750; Phi-4-reasoning 0.9950 [0.990, 0.999]; R1 0.9225. Gli IC95 differiscono al terzo decimale (per R1 0.901–0.944 contro 0.900–0.944), perché i due bootstrap usano generatori casuali diversi.

## 2. Misura ciò che intendiamo?

### Qwen3-8B

| | spento | acceso |
|---|---|---|
| W (IC95) | 0.975 [0.964, 0.985] | 1.000 [1.000, 1.000] |
| acc. sui B (NO / YES) | 1.000 (1.000 / 1.000) | 1.000 (1.000 / 1.000) |
| W per famiglia (AND / IMPLIES / OR) | 0.963 / 0.966 / 0.996 | 1.000 / 1.000 / 1.000 |
| W per variante (NOT / POS) | 0.955 / 0.995 | 1.000 / 1.000 |
| W per posizione (prima / ultima) | 0.955 / 0.995 | 1.000 / 1.000 |
| W con C senza risposta UNKNOWN | 0.964 (598 coppie) | 1.000 (**5 coppie**, 4 storie) |

Come cambiano le risposte dallo spento all'acceso:
- Sui B non cambia nulla: 800 su 800 restano corrette (268 NO, 532 YES).
- Sui C, 593 risposte diventano UNKNOWN (466 da YES, 127 da NO). Le 202 che erano già UNKNOWN restano tali. Solo 5 restano YES (3 erano YES e 2 erano NO).

**Lettura.** Il ragionamento porta Qwen a dichiarare l'indeterminatezza quasi sempre, e solo sui C. Il W = 1.000 è quindi quello che ci si aspetta quando la risposta stessa separa C e B. Il controllo «a parità di risposta», cioè W sulle coppie in cui il C non riceve UNKNOWN, ha solo 5 coppie: **non è valutabile**. Per questo con il ragionamento acceso non si può dire se p(UNKNOWN) contenga informazione oltre alla risposta.

### Phi-4-reasoning

| | acceso |
|---|---|
| W (IC95) | 0.995 [0.990, 0.999] |
| acc. sui B (NO / YES) | 0.991 (0.993 / 0.991), soglia di competenza superata |
| W per famiglia (AND / IMPLIES / OR) | 0.996 / 0.992 / 0.996 |
| W per variante (NOT / POS) | 0.995 / 0.995 |
| W per posizione (prima / ultima) | 1.000 / 0.990 |
| Risposte sui C | 793 UNKNOWN, 7 ALTRO, 0 YES, 0 NO |
| Risposte sui B | 0 UNKNOWN, 527 YES, 266 NO, 7 ALTRO |
| W con C senza risposta UNKNOWN | 0.43 (**7 coppie**, 7 storie) |

**Lettura.**
- Il quadro è lo stesso di Qwen3-8B acceso: dopo il ragionamento la risposta esplicita separa C e B quasi perfettamente. Il controllo a parità di risposta ha solo 7 coppie: **non è valutabile**.
- Le 4 coppie su 800 in cui il C non supera il B sono tutte coppie con il C in ALTRO, cioè con un avviso al posto dell'etichetta e massa vicina a 0 (§4, A3). Le altre 796 coppie sono ordinate correttamente.
- Rispetto a Phi-4 senza ragionamento (14 novembre: W 0.944, IMPLIES 0.83) il W sale e la debolezza su IMPLIES sparisce. Il confronto è solo descrittivo: i pesi sono diversi (Phi-4-reasoning è Phi-4 addestrato in più), quindi non misura l'effetto del ragionamento a pesi fissi.

### R1-Distill-Llama-8B

| | acceso |
|---|---|
| W (IC95) | 0.9225 [0.900, 0.944] |
| acc. sui B (NO / YES) | 0.955 (0.907 / 0.979), soglia di competenza superata |
| W per famiglia (AND / IMPLIES / OR) | **0.847** / 0.932 / 0.989 |
| W per variante (NOT / POS) | 0.9075 / 0.9375 |
| W per posizione (prima / ultima) | 0.9175 / 0.9275 |
| Risposte sui C | 468 UNKNOWN, 109 YES, 159 NO, 64 ALTRO |
| Risposte sui B | 9 UNKNOWN, 521 YES, 245 NO, 25 ALTRO |
| W con C senza risposta UNKNOWN | 0.844 [0.800, 0.887] (332 coppie, 172 storie) |
| W con nessuna delle due risposte UNKNOWN | 0.854 [0.810, 0.897] (327 coppie) |

**Lettura.**
- R1 risponde UNKNOWN a 468 C su 800 (59%) e a 9 B su 800. La separazione C/B quindi non è tutta nella risposta.
- Il controllo a parità di risposta è valutabile qui (332 coppie). Anche quando il C non riceve UNKNOWN, p(UNKNOWN) è più alta sul C che sul B nell'84% dei confronti. I valori in gioco però sono piccoli. Sulle risposte YES la mediana di p(UNKNOWN) è 3.8·10⁻⁵ sui C contro 1.9·10⁻⁶ sui B. Sulle risposte NO è 1.2·10⁻⁴ contro 4.3·10⁻⁵. È un ordinamento fra probabilità molto basse. Che questo ordinamento abbia un significato pratico non è stabilito da questi dati.
- AND è la famiglia più debole (0.847). Il pattern somiglia a quello del Test M, dove molti metodi dipendevano fortemente dalla famiglia, ma qui è solo descrittivo.

## 3. Aggiunge rispetto alle baseline? (descrittivo)

| Baseline dalle stesse uscite | Qwen3-8B spento | Qwen3-8B acceso | Phi-4-reasoning | R1 acceso |
|---|---|---|---|---|
| **p(UNKNOWN)** | **0.975** | **1.000** | **0.995** | **0.9225** |
| risposta generata UNKNOWN (0/1) | 0.626 | 0.997 | **0.996** | 0.787 |
| entropia normalizzata | 0.949 | 0.990 | 0.029 | 0.694 |
| meno p massima normalizzata | 0.9475 | 0.990 | 0.029 | 0.694 |
| lunghezza del ragionamento in token | — | 0.696 | 0.609 | 0.660 |
| ragionamento troncato (0/1) | — | 0.5 | 0.499 | 0.5 |
| lunghezza del prompt | 0.5 | 0.5 | 0.5 | 0.5 |
| p(UNKNOWN) normalizzata (non indipendente) | 0.975 | 1.000 | 1.000 | 0.916 |

- In Qwen3-8B acceso la risposta generata da sola arriva a 0.997, e la differenza da p(UNKNOWN) (+0.003) è dentro il tetto. Non c'è margine per mostrare un vantaggio.
- In Phi-4-reasoning la risposta generata **eguaglia** p(UNKNOWN) (0.996 contro 0.995): il codice lo segnala come anomalia (§4, A4). La differenza di 0.0006 equivale a mezza coppia su 800 e viene dai 7 C in ALTRO: lì la risposta 0/1 pareggia con il B (0 contro 0) in 4 coppie dove p(UNKNOWN) perde, e perde in 3 dove p(UNKNOWN) vince. p(UNKNOWN) normalizzata, che toglie l'effetto della massa, arriva a 1.000.
- In Phi-4-reasoning entropia e «meno p massima» sono **rovesciate** (0.029): il modello è più sicuro sui C (UNKNOWN con probabilità ≈ 1) che sui B. È lo stesso fenomeno visto per Mistral nel Test M. Un'incertezza generica qui va nella direzione opposta all'indeterminatezza.
- In R1 p(UNKNOWN) è sopra la migliore baseline indipendente di +0.136 (contro la risposta UNKNOWN 0/1).
- La lunghezza del ragionamento separa un poco C e B in tutti e due i modelli (0.66–0.70): sui C si ragiona più a lungo. Resta però molto sotto p(UNKNOWN).
- Il confronto non è un test di superiorità: per i modelli nuovi non ce n'è uno preregistrato.

## 4. Ripetibilità e anomalie

### Ripetibilità (prime 20 storie, 160 righe, due semi in più)

| | Qwen3-8B acceso | Phi-4-reasoning | R1 |
|---|---|---|---|
| W per seme (20261108 / 09 / 10) | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 0.9875 | 0.925 / 0.95 / 0.95 |
| Risposte uguali al seme principale | 158/160 e 157/160 | 160/160 e 158/160 | **111/160 e 115/160** |
| Dove cambiano le risposte | — | — | 44 e 40 sui C, 5 e 5 sui B |

Il W aggregato di R1 è stabile fra i semi, ma circa una risposta su tre cambia con il ragionamento campionato. Le risposte cambiano quasi solo sui C, in tutte le direzioni (NO→UNKNOWN, UNKNOWN→YES, UNKNOWN→ALTRO…). La misura è condizionata al ragionamento campionato (§2 del protocollo): per R1 questa dipendenza è forte sulla singola storia, debole sul W.

### Anomalie (classificate nelle quattro categorie)

**A1. R1: 89 risposte non leggibili (ALTRO), 25 sui B e 64 sui C.**
- Categoria: **comportamento del modello (formato della risposta)**, sostenuta dai dati.
- Tutte le 89 risposte cominciano con «The» e sono una frase di spiegazione invece di un'etichetta (per esempio «The policy requires both the harbor to…»).
- I controlli tecnici sono superati: template ed etichette controllati, prompt intatti 1600/1600, revisione verificata, risposta al primo token dopo `</think>` in 1600 righe su 1600. La stessa pipeline dà massa 1.000 a Qwen3-8B.
- Resta aperto se un prompt adattato a R1 produrrebbe etichette. Non è stato provato, per scelta: i prompt sono congelati e identici fra i modelli. È un **limite del protocollo**, dichiarato.
- Effetto su W: senza le coppie con una risposta ALTRO, W = 0.926 (713 coppie, 199 storie) contro 0.9225 su tutte. È una sensibilità descrittiva, non un'analisi preregistrata.

**A2. R1: massa sulle etichette bassa al primo token (mediana 0.837; 75.8% delle righe sotto 0.9; 147 righe sotto 0.5).**
- Categoria: **comportamento del modello (formato della risposta)**, sostenuta dai dati per le righe ALTRO (massa mediana 0.33). È plausibile anche per le altre, ma non dimostrato: anche senza le ALTRO la mediana resta 0.848. Il notebook non salva quali token prendono la massa mancante, quindi non posso dire che sia sempre «The».
- La regola tecnica (mediana ≥ 0.5) è superata, quindi il modello è misurabile.
- Con massa bassa p(UNKNOWN) e p(UNKNOWN) normalizzata possono divergere. Qui divergono poco (0.9225 contro 0.916).
- Le sole coppie in cui tutte e due le righe hanno massa ≥ 0.9 sono 54 (W 1.000). Sono una selezione di casi in cui il modello risponde con un'etichetta netta: **non è interpretabile** come stima del W.

**A3. Phi-4-reasoning: 14 risposte non leggibili (ALTRO), 7 B e 7 C.**
- Categoria: **comportamento del modello (formato della risposta)**, sostenuta dai dati. Tutte e 14 cominciano con un avviso («Disclaimer: This response is provided for informational purposes only…») al posto dell'etichetta; la massa sulle etichette in queste righe è fra 0 e 0.42.
- I controlli tecnici sono superati, e nelle altre 1586 righe l'etichetta arriva subito dopo `</think>`. L'avviso è uno stile che il modello produce da sé. Che dipenda dal messaggio di sistema Microsoft del template è possibile ma non provato.
- Effetto: sono le 4 coppie su 800 in cui p(UNKNOWN) non ordina il C sopra il B (§2).

**A4. Phi-4-reasoning: una baseline indipendente eguaglia p(UNKNOWN)** (risposta generata UNKNOWN 0/1: 0.996 contro 0.995). Il codice propone «evidenza scientifica» come categoria possibile.
- Classificazione: **evidenza scientifica, descrittiva**, sostenuta dai dati. Con il ragionamento acceso, in Phi-4-reasoning (come in Qwen3-8B) il segnale sull'indeterminatezza sta nella risposta esplicita. p(UNKNOWN) al primo token della risposta riproduce la risposta e non aggiunge informazione misurabile.
- Non è un problema tecnico: la differenza di 0.0006 è spiegata coppia per coppia dalle 7 risposte ALTRO sui C (§3).
- Limite: con un tetto a 0.995–0.996 nessuna misura può mostrare un vantaggio. Il dato dice che qui p(UNKNOWN) **non aggiunge**, non che sia peggiore.

**Qwen3-8B: nessuna anomalia segnalata dal codice.** Il W = 1.000 non è un'anomalia, ma un effetto tetto della risposta esplicita (§2), già previsto come limite prima dei dati.

## 5. Phi-4-reasoning: errore di memoria e ripresa

**Che cosa è successo.** A 1152 righe su 1600 la GPU ha esaurito la memoria: «Tried to allocate 2.92 GiB … 32.15 GiB allocated by PyTorch, 4.49 GiB reserved but unallocated».
- I 2.92 GiB corrispondono alla matrice di attenzione eager in float32 di una riga di circa 4400 token (40 teste), nella misura a batch 1.
- Non è un limite di capienza: le 3 righe arrivate al budget, lunghe fino a 4418 token, erano già state misurate senza errori.
- Categoria: **problema tecnico (gestione della memoria)**, sostenuta dai dati. La memoria della generazione a batch 8 resta riservata e frammentata (4.49 GiB) quando parte la misura eager.

**Correzione (notebook `IndetBench_reasoning_v2_1.ipynb`, solo memoria).** Nessun calcolo cambia (dettagli in `Note_reasoning_v2.md` §7):
1. allocatore `expandable_segments` impostato nella cella 1, prima di torch;
2. le uscite della generazione e la cache CUDA si liberano prima della misura;
3. dopo un OOM la stessa misura si ripete una volta, e la ripetizione è registrata in `esito.json`.

VERSIONE e manifest non cambiano, quindi la ripresa riusa i 36 blocchi salvati. In una prova a secco con OOM simulati, `punteggi.csv` è identico byte per byte a quello della v2.

**Esito della ripresa (16 novembre).** Phi-4 è ripartito dai 36 blocchi salvati e ha completato le 448 righe mancanti e le 320 di ripetibilità in 4709 s. Le 1152 righe della prima sessione sono identiche nel risultato finale (scarto 0, risposte 1152/1152), il manifest è identico e nessuna misura è stata ripetuta per memoria (`memoria_cuda`: 0). Qwen3-8B e R1 sono stati saltati come già completati, con gli stessi file.

## 6. Conclusioni (esplorative)

1. **Funziona tecnicamente:** sì, per Qwen3-8B, Phi-4-reasoning e R1. La pipeline riproduce il Test U2 esattamente; i ragionamenti si chiudono da soli tranne 4 su 1600 di Phi-4-reasoning (coppie chiuse 796, sopra la soglia di 760). La ripresa di Phi-4 dopo l'errore di memoria non ha cambiato nessun valore.
2. **Misura ciò che intendiamo:** con il ragionamento la separazione C/B resta alta in tutti e tre i modelli. In Qwen3-8B e in Phi-4-reasoning però passa quasi tutta alla risposta esplicita, quindi non si può separare il contributo di p(UNKNOWN) da quello della risposta. In R1 una parte della separazione resta anche a parità di risposta, ma su probabilità molto piccole.
3. **Aggiunge rispetto alle baseline:** in Qwen3-8B acceso e in Phi-4-reasoning no: la risposta generata arriva a 0.997 e 0.996, al livello di p(UNKNOWN). In Phi-4-reasoning le baseline di incertezza generica sono rovesciate. In R1 sì in modo descrittivo (+0.136 sulla risposta UNKNOWN), con i limiti di massa, di formato e di ripetibilità del §4.
4. HR2 (Qwen3-8B): il ragionamento cambia W (+0.025, IC95 esclude 0). L'aumento coincide con il massimo possibile, quindi il dato non dice quanto il ragionamento migliorerebbe senza tetto.
5. Lettura d'insieme (esplorativa): nei due modelli che, dopo il ragionamento, dichiarano quasi sempre l'indeterminatezza, p(UNKNOWN) coincide con la risposta. Solo in R1, che risponde UNKNOWN al 59% dei C, resta una separazione oltre la risposta, ma su probabilità molto piccole e con ripetibilità bassa. Qwen3-32B resta da fare (serve la A100 da 80 GB); senza di esso HR2 secondaria non ha dati.
