# Test U2: risultati (istruzione e formato, 4 modelli, 9 novembre)

Protocollo: `Protocollo_testU2_istruzione_v2.md`. Notebook: `TestU2_istruzione_4_modelli_v2.ipynb` (versione U2-v1-notebook-2), modalità completa, 4 modelli su 4. Le run usano transformers 5.22.1 e torch 2.14.1 su A100-SXM4-40GB.
Dati: `testU2_risultati/` (esiti.json, condizioni.csv, rapporto.txt, testU2_risultati.zip).

## In breve

1. **Il risultato in prosa del Test U non dipende dalla frase che spiega la riga incerta.** Senza la frase (P−S), p(UNKNOWN) separa C da B in **tutti e 4 i modelli** (HI1 4 su 4).
2. **La frase non migliora W in modo generale.** HI2 si conferma in 2 modelli su 4 (Mistral e Llama). In Qwen la frase abbassa W, da 0.975 a 0.914.
3. **Il template in prosa batte quello simbolico, anche senza la frase** (HI3 4 su 4). Il confronto riguarda però due template interi, perché cambiano anche l'istruzione di base e la domanda finale. Non si può attribuire la differenza alla sola notazione.
4. **La frase agisce soprattutto sulla risposta generata, non sull'ordinamento.** Con la frase i modelli dicono UNKNOWN molto più spesso, sia sui C sia sui B. L'accuratezza bilanciata della risposta generata sale in tutti e 4 i modelli. W di p(UNKNOWN), invece, cambia poco o in direzioni diverse.

Lettura preregistrata (riga 2 della tabella del protocollo): «In prosa p(UNKNOWN) supera il criterio anche senza la frase che spiega la riga incerta; un miglioramento dovuto alla frase non è confermato». Si aggiunge la lettura di HI3: «Il template in prosa senza spiegazione ottiene un W più alto del template simbolico senza spiegazione».

## Allineamento con il Test U

| Controllo | Esito |
|---|---|
| Hash dei 2400 prompt P+S uguale a V2 del Test U | superato |
| 24 valori di p(UNKNOWN) per modello (tolleranza 1e-3) | superato: scarto massimo ≤ 1.1e-16 |
| W di P+S uguale al Test U (tolleranza 0.005) | superato: 0.91375, 0.83375, 0.73625 e 0.83875, identici |
| Controllo esteso, fatto dopo: tutti i 2400 prompt P+S confrontati con V2 del Test U | p(UNKNOWN) identico (scarto 0) e risposta letta identica nel 100% dei casi, per tutti e 4 i modelli |
| Coppie scartate per lunghezza | 0 in tutte le condizioni |
| Massa sotto 0.90 / risposte illeggibili (ALTRO) | 0% / 0% |

## W di p(UNKNOWN) per condizione

W è la quota di coppie in cui p(UNKNOWN) di C supera quello di B, mediata per storia, con IC al 95% su 2000 ricampionamenti delle storie. Ogni cella ha 800 coppie e 200 storie.

| Modello | P+S (= V2 Test U) | **P−S** | S+S | S−S |
|---|---|---|---|---|
| Qwen | 0.914 [0.89, 0.93] | **0.975** [0.96, 0.99] | 0.686 [0.65, 0.72] | 0.630 [0.60, 0.66] |
| Mistral | 0.834 [0.80, 0.87] | **0.783** [0.75, 0.81] | 0.545 [0.51, 0.59] | 0.541 [0.49, 0.59] |
| OLMo | 0.736 [0.70, 0.78] | **0.694** [0.65, 0.74] | 0.561 [0.54, 0.59] | 0.584 [0.55, 0.62] |
| Llama | 0.839 [0.81, 0.86] | **0.746** [0.70, 0.79] | 0.530 [0.50, 0.56] | 0.539 [0.50, 0.58] |

S+S replica ADD del Test U su storie diverse, con valori molto vicini: Qwen 0.686 contro 0.688, Mistral 0.545 contro 0.542, OLMo 0.561 contro 0.548, Llama 0.530 contro 0.558. Il risultato debole del formato simbolico si conferma.

## Ipotesi preregistrate

I contrasti sono appaiati per `pair_key`: 800 coppie comuni in tutti i casi.

| Modello | HI1: W(P−S) | HI2: P+S − P−S | HI3: P−S − S−S |
|---|---|---|---|
| Qwen | 0.975 [0.964, 0.985] **CONF** | −0.061 [−0.081, −0.043] NON CONF | +0.345 [0.309, 0.381] **CONF** |
| Mistral | 0.783 [0.751, 0.811] **CONF** | +0.051 [0.025, 0.078] **CONF** | +0.241 [0.194, 0.288] **CONF** |
| OLMo | 0.694 [0.651, 0.735] **CONF** | +0.043 [0.023, 0.063] NC | +0.110 [0.061, 0.158] **CONF** |
| Llama | 0.746 [0.704, 0.785] **CONF** | +0.093 [0.064, 0.121] **CONF** | +0.208 [0.162, 0.251] **CONF** |
| **Conferme** | **4 su 4** | 2 su 4 | **4 su 4** |

HI2 di OLMo ha l'intervallo tutto sopra 0, ma la stima (+0.043) è sotto la soglia minima di 0.05, quindi resta NON CONCLUSIVA. HI2 di Mistral supera la soglia di poco (+0.051).

## Descrittivi

**La frase nei due formati.** In prosa la frase cambia W in modo diverso da modello a modello (vedi HI2). In simbolico non cambia quasi nulla: S+S − S−S vale +0.056 [0.03, 0.08] per Qwen, +0.004 per Mistral, −0.022 per OLMo e −0.009 per Llama. Gli ultimi tre hanno IC che comprendono 0. L'interazione vale −0.118 [−0.153, −0.084] per Qwen, +0.048 [0.016, 0.078] per Mistral, +0.065 [0.030, 0.099] per OLMo e +0.101 [0.066, 0.139] per Llama.

**Risposta generata.** Le tabelle riportano la quota di UNKNOWN e l'accuratezza bilanciata (BA) della risposta del modello, cioè la media fra la quota di UNKNOWN sui C e la quota di non-UNKNOWN su A e B.

| Modello | UNK su C: P+S → P−S | UNK su B: P+S → P−S | BA generata: P+S / P−S / S+S / S−S |
|---|---|---|---|
| Qwen | 83% → 25% | 29% → 0% | 0.83 / 0.63 / 0.50 / 0.51 |
| Mistral | 77% → 45% | 49% → 30% | 0.71 / 0.65 / 0.50 / 0.50 |
| OLMo | 4% → 1% | 0.25% → 0% | 0.52 / 0.51 / 0.50 / 0.50 |
| Llama | 95% → 34% | 79% → 5% | 0.72 / 0.66 / 0.50 / 0.50 |

In simbolico i modelli non rispondono quasi mai UNKNOWN, con o senza la frase (al massimo l'1.5% dei C, per Qwen in S−S). In prosa la frase raddoppia o triplica le astensioni, sia giuste sia sbagliate. Il caso di Llama è estremo: con la frase si astiene sul 79% dei B, senza la frase sul 5%. Per l'accuratezza sui casi determinati (A e B), la frase in prosa costa molto a Llama (0.93 contro 0.48) e a Qwen (0.96 contro 0.80).

**Falsa astensione sui B secondo la posizione della riga incerta** (riga incerta all'inizio / in fondo):

| Modello | P+S | P−S |
|---|---|---|
| Qwen | 10.5% / 46.8% | 0% / 0% |
| Mistral | 28% / 71% | 0.5% / 59% |
| Llama | 92.5% / 65% | 1.2% / 9.2% |
| OLMo | 0% / 0.5% | 0% / 0% |

Senza la frase l'effetto posizione scompare in Qwen e quasi in Llama. In Mistral resta forte: con la riga incerta in fondo si astiene sul 59% dei B anche senza la frase.

**W a parità di risposta in P−S** (coppie in cui il modello non risponde UNKNOWN né su B né su C): Qwen 0.964 (598 coppie), Mistral 0.750 (402), OLMo 0.692 (789), Llama 0.694 (512). Anche senza astensione esplicita, la probabilità di UNKNOWN ordina C sopra B.

**Misure alternative (entropia, con valori quasi identici per 1 − probabilità massima).** In P−S l'entropia funziona bene per Qwen (W 0.949) e discretamente per Llama (0.740). Per Mistral (0.466) e OLMo (0.615) resta inferiore a p(UNKNOWN). Con la frase (P+S) l'entropia peggiora molto in Qwen, Mistral e Llama (0.52, 0.30, 0.20), come già nel Test U. Quando la frase spinge i modelli a dire UNKNOWN con sicurezza, l'incertezza generica sull'uscita smette di essere informativa.

## Riserve

1. **HI3 confronta due template interi.** P−S e S−S differiscono per la notazione, ma anche per l'istruzione di base e per la domanda («given» contro «granted»). Il test dice che il template in prosa funziona meglio, non quale elemento del template conti.
2. **Le storie sono quelle di V2.** Le famiglie sono AND, OR e IMPLIES, con e senza NOT. Gli operatori di V1 e i numerici di V3 non sono stati provati in prosa.
3. **HI2 è al limite in due modelli.** Mistral passa la soglia di 0.05 per 0.001, mentre OLMo la manca con l'intervallo tutto positivo. La conclusione «la frase non migliora W in generale» regge, ma l'effetto della frase non è nullo in Mistral, OLMo e Llama: in questi tre modelli è piccolo e positivo.

## Cosa significa per la libreria e per il Test U

- **La riserva principale del Test U è risolta a favore del formato.** Il successo di V2 non veniva dalla frase che spiega la riga incerta: senza la frase, p(UNKNOWN) separa C da B in 4 modelli su 4. Il resoconto del Test U va aggiornato con questo risultato.
- **Il punteggio p(UNKNOWN) va separato dall'istruzione che autorizza l'astensione.** L'istruzione cambia molto quanto spesso il modello dice UNKNOWN e quante false astensioni fa, ma cambia poco la capacità del punteggio di ordinare C sopra B. Nella libreria conviene misurare il punteggio con un'istruzione neutra e trattare la frase come una scelta di comportamento, non di rilevazione.
- **Il formato simbolico resta debole** (W 0.53–0.69 con o senza frase), quindi la limitazione del Test U su ADD e V1 è confermata.

## Prossimi passi in lista

1. Confronto con i metodi esistenti sulle coppie B/C: una sonda pubblicata e i rilevatori di SIRIN (answerability, LM-Polygraph). Conviene usare P−S come formato principale e S−S come controllo.
2. Punto C: allucinazioni con contesto.
3. Step 3: protocollo e libreria su GitHub.
