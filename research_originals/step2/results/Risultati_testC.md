# Test C: allucinazioni con contesto · resoconto del completo (bozza v2)

13 novembre 2026. Protocollo: `Protocollo_testC_v3.md`.

**v2 (13 novembre, pomeriggio).** Aggiunti i controlli dopo il completo: concordanza del classificatore, HC0 di M1 con la generazione naturale, troncamento, LOG e rilettura di Simona (§4.3–§4.6). Nessun esito preregistrato cambia.

**Esecuzione**
- Notebook `C-notebook-3-Csel8`.
- Selezione `C-sel-8`, con regole naturali `C-nat-7`. SHA dello ZIP `aaad5c5e…`.
- 2398 righe per modello:
  - 800 coppie sintetiche;
  - 399 coppie naturali. DUE-nat ha 199 coppie su 200, deficit dichiarato.
- Dati: `testC_completo_risultati/`.
- Ricalcolo indipendente: `strumenti_resoconto_C/ricalcolo.py`. I file sono elencati in §8.

**Legenda delle sigle**

| Sigla | Significato |
|---|---|
| CONF | CONFERMATA |
| NON CONF | NON CONFERMATA |
| NON CONCL | NON CONCLUSIVA |
| NV | NON VALUTABILE |

I paragrafi marcati **[esplorativo, post hoc]** sono analisi decise dopo aver visto i dati. Non sono preregistrate e non cambiano nessun esito.

---

## 0. In breve

1. **L'esecuzione è integra.**
   - 14 lavori su 14 sono ESEGUITI.
   - La copertura è 600/600 coppie per HC1 e HC2, e 200/200 su RIM.
   - Il ricaricamento delle sonde M2 ha scarto 0.0 per tutti i modelli e le varianti.
   - L'allineamento con il Test U2 è ≤ 1e-16 in `env_m1`.
   - Il mio ricalcolo, scritto senza importare `tc_analisi`, riproduce **tutte** le stime puntuali dei 41 confronti metodo × modello. Gli IC coincidono entro ±0.01, con un seme diverso. Anche i conteggi di HC4 coincidono.
   - Tutti i verdetti seguono le soglie del protocollo.
2. **Esiti preregistrati.**
   - **HC2: 0 su tutto.** Nessun metodo esistente batte il riferimento p(UNKNOWN) sul primo token. È lo stesso risultato del Test M, ora su passaggi di testo.
   - **HC1** è confermata per M1-MSP, M1-SemanticEntropy, M2-senzaℓ2 (4/4), M1-Perplexity e M1-MeanTokenEntropy (3/4) e per M2 (3 su 3 valutabili). Per M3 (giudice unico) è confermata. M4-LoRA è confermata su Llama.
   - **HC3** non è confermata da nessun metodo con la regola dei 3 su 4.
   - **HC4 entro B** è **NON VALUTABILE ovunque**. Nessun modello dà risposte errate sui B sintetici non astenuti (0 casi in 4 modelli).
   - **HC4 entro C** è confermata secondo la regola per M2 (3/3), M2-senzaℓ2 (3/4) e M3 (4/4 generatori).
3. **Due problemi di interpretazione, trovati controllando i dati.** Il secondo cambia il modo in cui si legge HC4.
   - **Soffitto del riferimento.** p(UNKNOWN) ha W fra 0.94 e 0.98, quindi il margine 1 − W è 0.017–0.066.
     - Con la soglia fissa +0.05, **HC2 era raggiungibile solo per Qwen**. Per gli altri 3 modelli era impossibile per costruzione.
     - Allo stesso modo HC3 (D ≥ 0.10) era impossibile per ogni metodo con W > 0.90.
     - «HC2 non confermata» va quindi letto come «nessun metodo supera il riferimento», non come prova che il margine non ci sia.
   - **HC4 entro C è confusa con la famiglia** [esplorativo, post hoc].
     - Le risposte supportate vengono quasi tutte da DUE («1821 or 1823»). Quelle non supportate vengono quasi tutte da LOG e CONF.
     - **Dentro la stessa famiglia**, i metodi che leggono il prompt (riferimento, M2, M3) sono vicini al caso o sotto: AUROC 0.30–0.69.
     - Le conferme di HC4 per M2, M2-senzaℓ2 e M3 riflettono quindi soprattutto «i prompt LOG e CONF sembrano meno rispondibili dei DUE», non la discriminazione del supporto. La formula «discrimina il supporto fra le risposte non astenute» **non è sostenuta** per questi metodi.
4. **Comportamento dei modelli.**
   - Sui B sintetici i modelli non sbagliano mai: si astengono o rispondono giusto.
   - Sui C:
     - di RIM si astengono (92–100%);
     - di DUE riportano le due alternative (68–96%);
     - di CONF si astengono per lo più. Fa eccezione OLMo, che sceglie un valore nel 42% dei casi.
   - **Su LOG-B, che ha una risposta determinata, molti si astengono comunque.** Llama si astiene nel 74% dei casi, Mistral nel 49%, Qwen nel 29%. È un'astensione eccessiva davanti alla disgiunzione anche quando i due rami portano allo stesso valore.
5. **Controlli dopo il completo** (§4.3–§4.6).
   - **HC0 di M1 con la generazione naturale: confermato** in tutte le 17 celle che lo superavano (scarto massimo 0.017). Gli esiti di M1 restano validi.
   - **Concordanza del classificatore: 0.68** (kappa 0.62; 0.77 sulla classe di HC4), sotto la soglia di 0.90. Per il protocollo gli esiti di HC4 vanno letti **con l'avvertenza**.
   - **Troncamento:** su Qwen cambiano classe 43 risposte (elencano le fonti, poi concludono «UNKNOWN»). Fra 76 verdetti HC4 ne cambierebbe uno solo, al bordo della soglia. Vale il verdetto del completo.
   - **LOG-B:** nella rilettura di Simona la risposta di B è ricavabile in 20 casi su 20, ma solo con un passaggio logico per casi. L'astensione è quindi dei modelli, non dei passaggi.
6. **Sul naturale** (descrittivo), quando i modelli scelgono un solo valore su DUE-nat C, scelgono la risposta originale di SQuAD circa 2–2.6 volte più spesso del distrattore. È compatibile con la memoria degli articoli, ma non lo dimostra.

---

## 1. Integrità dell'esecuzione (verificata)

| Controllo | Esito |
|---|---|
| Lavori | 14/14 ESEGUITI, più 3 installazioni; nessun errore nell'analisi (`errori_analisi` vuoto) |
| Dati | SHA dello ZIP della selezione e di `righe_C` controllati dal notebook prima delle inferenze; 2398 righe e 1199 coppie |
| Copertura | 600/600 (minimo 570) e 200/200 su RIM (minimo 190), per tutti i 41 confronti |
| M2 | ricaricamento 0.0 per originale e senzaℓ2 sui 4 modelli. Epoche delle sonde: Qwen 1/5, Mistral 4/4, OLMo 1/3, Llama 2/3 (originale/senzaℓ2), le stesse del notebook B |
| Allineamento con il Test U2 | `env_m1` ≤ 1e-16. `env_sirin` ≤ 0.06. M4 in `env_obeso` 0.028 |
| p(UNKNOWN) `env_sirin` contro `env_m1` (descrittivo) | Qwen: 130 righe con differenza > 0.05, di cui 9 > 0.2; mediana 0. Altri modelli: 15–38 righe > 0.05. Ogni ΔW usa il riferimento dello stesso ambiente, come prevede il protocollo |
| M1, LM-Polygraph contro riferimento | testo uguale 2291–2372 su 2398; categoria uguale 2369–2389 su 2398 |
| GPU | A100-80GB per i lavori di Qwen e per M3, A100-40GB per gli altri. Le due famiglie sono equivalenti secondo l'impronta (scarto 1e-16, notebook A v8) |
| HC0 | ereditato da `esiti_A.json` (sha `aae347d2…`) e `esiti_B.json` (sha `349c0284…`) |
| Ricalcolo indipendente | stime puntuali identiche su 41/41 confronti; IC entro ±0.01; numerosità di HC4 identiche |

---

## 2. Esiti preregistrati (§7 del protocollo)

Analisi principale: 600 coppie sintetiche (DUE + CONF + LOG) su 200 passaggi. Per p(UNKNOWN) gli esiti tra parentesi sono descrittivi, perché è il riferimento.

| Metodo | Modello | HC0 | W (IC 95%) | HC1 | ΔW (IC) · margine | HC2 | D (IC) | HC3 | AUROC entro C (non supp./supp.) | HC4 C |
|---|---|---|---|---|---|---|---|---|---|---|
| p(UNKNOWN) | qwen | rif. | 0.942 (0.923–0.960) | (CONF) | — | — | +0.053 (+0.032…+0.075) | — | 0.743 (69/219) | (CONF) |
| M1-MSP | qwen | 0.819 | 0.615 (0.577–0.655) | CONF | −0.327 · 0.058 | NON CONF | −0.530 | NON CONF | 0.483 (66/226) | NON CONCL |
| M1-Perplexity | qwen | 0.815 | 0.585 (0.543–0.625) | NON CONCL | −0.357 · 0.058 | NON CONF | −0.455 | NON CONF | 0.537 | NON CONCL |
| M1-MeanTokenEntropy | qwen | 0.830 | 0.595 (0.558–0.635) | NON CONCL | −0.347 · 0.058 | NON CONF | −0.445 | NON CONF | 0.560 | NON CONCL |
| M1-SemanticEntropy | qwen | 0.815 | 0.662 (0.623–0.698) | CONF | −0.280 · 0.058 | NON CONF | −0.577 | NON CONF | 0.545 | NON CONCL |
| M1-PTrue | qwen | 0.284 ✗ | 0.308 | NV | — | NV | — | NV | 0.275 | NV |
| p(UNKNOWN) | mistral | rif. | 0.980 (0.968–0.992) | (CONF) | — | — | +0.020 | — | 0.732 (45/137) | (CONF) |
| M1-MSP | mistral | 0.835 | 0.600 (0.555–0.645) | CONF | −0.380 · 0.020 | NON CONF | −0.315 | NON CONF | 0.637 | NON CONCL |
| M1-Perplexity | mistral | 0.846 | 0.603 (0.555–0.652) | CONF | −0.377 · 0.020 | NON CONF | −0.158 | NON CONF | 0.840 (46/136) | CONF |
| M1-MeanTokenEntropy | mistral | 0.865 | 0.647 (0.603–0.693) | CONF | −0.333 · 0.020 | NON CONF | −0.072 | NON CONF | 0.859 | CONF |
| M1-SemanticEntropy | mistral | 0.839 | 0.683 (0.648–0.725) | CONF | −0.297 · 0.020 | NON CONF | −0.318 | NON CONF | 0.620 | NON CONCL |
| M1-PTrue | mistral | 0.402 ✗ | 0.520 | NV | — | NV | — | NV | 0.305 | NV |
| p(UNKNOWN) | olmo | rif. | 0.977 (0.965–0.987) | (CONF) | — | — | +0.023 | — | 0.559 (196/276) | (NON CONCL) |
| M1-MSP | olmo | 0.779 | 0.848 (0.813–0.882) | CONF | −0.128 · 0.023 | NON CONF | −0.148 | NON CONF | 0.545 | NON CONCL |
| M1-Perplexity | olmo | 0.778 | 0.773 (0.732–0.815) | CONF | −0.203 · 0.023 | NON CONF | +0.002 | NON CONCL | 0.666 | NON CONCL |
| M1-MeanTokenEntropy | olmo | 0.812 | 0.798 (0.757–0.835) | CONF | −0.178 · 0.023 | NON CONF | +0.012 | NON CONCL | 0.697 | NON CONCL |
| M1-SemanticEntropy | olmo | 0.802 | 0.862 (0.830–0.890) | CONF | −0.115 · 0.023 | NON CONF | −0.142 | NON CONF | 0.594 | NON CONCL |
| M1-PTrue | olmo | 0.704 | 0.572 (0.535–0.610) | NON CONCL | −0.405 · 0.023 | NON CONF | +0.423 (+0.385…+0.460) | CONF | 0.674 | NON CONCL |
| p(UNKNOWN) | llama | rif. | 0.963 (0.948–0.977) | (CONF) | — | — | +0.037 | — | 0.861 (57/215) | (CONF) |
| M1-MSP | llama | 0.867 | 0.752 (0.722–0.785) | CONF | −0.212 · 0.037 | NON CONF | +0.018 | NON CONCL | 0.877 (58/216) | CONF |
| M1-Perplexity | llama | 0.857 | 0.637 (0.603–0.672) | CONF | −0.327 · 0.037 | NON CONF | +0.213 (+0.155…+0.268) | CONF | 0.982 | CONF |
| M1-MeanTokenEntropy | llama | 0.871 | 0.640 (0.603–0.678) | CONF | −0.323 · 0.037 | NON CONF | +0.250 (+0.203…+0.295) | CONF | 0.983 | CONF |
| M1-SemanticEntropy | llama | 0.846 | 0.780 (0.748–0.810) | CONF | −0.183 · 0.037 | NON CONF | +0.030 | NON CONCL | 0.835 | CONF |
| M1-PTrue | llama | 0.351 ✗ | 0.593 | NV | — | NV | — | NV | 0.581 | NV |
| M2 | qwen | 0.499 ✗ | 0.627 | NV | — | NV | — | NV | 0.606 | NV |
| M2-senzaℓ2 | qwen | 0.881 | 0.798 (0.772–0.825) | CONF | −0.136 · 0.066 | NON CONF | +0.202 (+0.175…+0.228) | CONF | 0.892 (69/219) | CONF |
| M2 | mistral | 0.909 | 0.958 (0.943–0.973) | CONF | −0.020 · 0.022 | NON CONF | +0.042 | NON CONCL | 0.877 (45/137) | CONF |
| M2-senzaℓ2 | mistral | 0.925 | 0.947 (0.930–0.963) | CONF | −0.032 · 0.022 | NON CONF | +0.053 | NON CONCL | 0.909 | CONF |
| M2 | olmo | 0.911 | 0.753 (0.717–0.790) | CONF | −0.230 · 0.017 | NON CONF | +0.247 (+0.210…+0.283) | CONF | 0.739 (196/276) | CONF |
| M2-senzaℓ2 | olmo | 0.912 | 0.917 (0.897–0.937) | CONF | −0.067 · 0.017 | NON CONF | +0.083 | NON CONCL | 0.669 | NON CONCL |
| M2 | llama | 0.931 | 0.860 (0.837–0.882) | CONF | −0.108 · 0.032 | NON CONF | +0.140 (+0.118…+0.163) | CONF | 0.879 (57/215) | CONF |
| M2-senzaℓ2 | llama | 0.937 | 0.923 (0.903–0.942) | CONF | −0.045 · 0.032 | NON CONF | +0.077 | NON CONCL | 0.771 | CONF |
| M3 (giudice) | qwen | 0.805 | 0.920 (0.898–0.940) | CONF | −0.014 (−0.041…+0.011) · 0.066 | NON CONCL | +0.080 | NON CONCL | 0.732 (69/219) | CONF |
| M3 | mistral | 〃 | 〃 | 〃 | −0.058 · 0.022 | NON CONF | 〃 | 〃 | 0.797 (45/137) | CONF |
| M3 | olmo | 〃 | 〃 | 〃 | −0.063 · 0.017 | NON CONF | 〃 | 〃 | 0.710 (196/276) | CONF |
| M3 | llama | 〃 | 〃 | 〃 | −0.048 · 0.032 | NON CONF | 〃 | 〃 | 0.904 (57/215) | CONF |
| M4-lin | llama | 0.848 | 0.588 (0.552–0.622) | NON CONCL | −0.381 · 0.032 | NON CONF | −0.122 | NON CONF | 0.606 | NON CONCL |
| M4-LoRA | llama | 0.890 | 0.822 (0.798–0.845) | CONF | −0.147 · 0.032 | NON CONF | −0.234 | NON CONF | 0.553 | NON CONCL |

HC4 entro B è NON VALUTABILE in tutte le righe: le risposte errate sui B sintetici sono 0, contro 653–778 corrette.

**HC-dom (RIM, per M2 e M3).**
- È confermato per tutti. M3 e M2-senzaℓ2 hanno W(RIM) = 1.000, M2 1.000 per Mistral, OLMo e Llama.
- Fa eccezione M2-Qwen, che ha W(RIM) 0.665 ma è comunque NON VALUTABILE per HC0. Il suo collasso, già visto nel Test M, si ripete.

**Lettura per la libreria (regola dei 3 su 4, §7).**

| Metodo | HC1 | HC2 | HC3 | HC4 entro C | HC4 entro B |
|---|---|---|---|---|---|
| M1-MSP | 4/4 ✓ | 0/4 | 0/4 | 1/4 | NV |
| M1-Perplexity | 3/4 ✓ | 0/4 | 1/4 | 2/4 | NV |
| M1-MeanTokenEntropy | 3/4 ✓ | 0/4 | 1/4 | 2/4 | NV |
| M1-SemanticEntropy | 4/4 ✓ | 0/4 | 0/4 | 1/4 | NV |
| M1-PTrue (solo OLMo) | 0/1 | 0/1 | 1/1 | 0/1 | NV |
| M2 (Qwen NV) | 3/3 ✓ | 0/3 | 2/3 | 3/3 ✓ * | NV |
| M2-senzaℓ2 | 4/4 ✓ | 0/4 | 1/4 | 3/4 ✓ * | NV |
| M3 (giudice unico) | ✓ | 0 su 4 riferimenti | NON CONCL | 4/4 generatori ✓ * | NV |
| M4-lin (Llama) | NON CONCL | no | no | NON CONCL | NV |
| M4-LoRA (Llama) | ✓ | no | no | NON CONCL | NV |

\* Formalmente confermata. La lettura come «discrimina il supporto» non regge al controllo per famiglia (§4.2).

**Avvertenza su tutti gli esiti di HC4 (protocollo §4).** La concordanza fra classificatore automatico e lettura umana è 0.68, sotto la soglia di 0.90 (§4.3).

---

## 3. Comportamento dei modelli (descrittivo)

Ogni cella dà, nell'ordine, il numero di astensioni, di risposte che riportano le due alternative e di risposte che scelgono un solo valore del contesto, su 200 C per famiglia.

| Famiglia, lato C | Qwen | Mistral | OLMo | Llama |
|---|---|---|---|---|
| RIM | 200 / 0 / 0 | 199 / 0 / 1 | 184 / 0 / 15 | 197 / 0 / 1 |
| DUE | 40 / 160 / 0 | 55 / 136 / 9 | 9 / 190 / 0 | 7 / 191 / 2 |
| CONF | 180 / 13 attribuite / 6 | 188 / 0 / 12 | 37 / 60 (alternative + attribuite) / 83, più 20 «entrambi» | 118 / 23 / 49, più 5 «entrambi» |
| LOG | 92 / 46 / 62 | 175 / 1 / 24 | 78 / 26 / 92 | 198 / 1 / 1 |

**Accuratezza su B (HC0-set)**

| Famiglia | Qwen | Mistral | OLMo | Llama |
|---|---|---|---|---|
| DUE | 1.00 | 1.00 | 1.00 | 1.00 |
| CONF | 0.995 | 0.94 | 1.00 | 1.00 |
| RIM | 0.955 | 0.995 | 0.995 | 1.00 |
| **LOG** | **0.715** | **0.515** | 0.895 | **0.265** |
| tutte | 0.916 | 0.863 | 0.973 | 0.816 |

- Tutte le risposte non corrette su B sono **astensioni**: non ci sono risposte errate.
- **Avviso HC0-set per famiglia.** Il protocollo chiede l'accuratezza su B per modello e per famiglia, con la soglia 0.80 come segnalazione. Il rapporto del notebook segnala solo il totale. Su LOG l'accuratezza è sotto 0.80 per Qwen, Mistral e Llama. Su LOG, quindi, per questi tre modelli B non è «determinato» nel comportamento: il modello si astiene anche quando i due rami portano allo stesso valore.
- **Ricaduta sull'analisi.** Le coppie LOG confrontano C con un B su cui spesso il modello stesso si astiene. È il motivo per cui LOG è la famiglia più difficile per quasi tutti i metodi. Valori di W su LOG:
  - M1: 0.31–0.69 su Qwen, Mistral e Llama;
  - M2: 0.47–0.58 su Qwen, OLMo e Llama;
  - p(UNKNOWN): 0.86–0.98;
  - M3: 0.80.

**Troncamento a 32 token.**
- Llama ha 369 risposte non finite. 363 sono astensioni seguite da una spiegazione («UNKNOWN \n\nThe passage does not…»), quindi la categoria non cambia.
- Qwen ne ha 73, quasi tutte attribuite o alternative lunghe; OLMo 26; Mistral 0.
- Le risposte troncate sono state rigenerate fino a 96 token: vedi §4.5.

---

## 4. Problemi di interpretazione

### 4.1 Soffitto del riferimento (conseguenza del disegno, già nota nel Test M)

- **HC2.** ΔW non può superare il margine 1 − W(rif).
  - Margini di `env_m1`, usati per M1: Qwen 0.058, Mistral 0.020, OLMo 0.023, Llama 0.037.
  - Margini di `env_sirin`, usati per M2 e M3: 0.066, 0.022, 0.017, 0.032.
  - Con la soglia fissa +0.05, HC2 era **raggiungibile solo per Qwen**. La regola dei 3 su 4 per HC2 era quindi irraggiungibile per costruzione.
- **HC3.** D = W(RIM) − W(principale) ≤ 1 − W(principale), quindi con la soglia 0.10 era impossibile per ogni metodo con W > 0.90:
  - M3;
  - M2 su Mistral;
  - M2-senzaℓ2 su Mistral, OLMo e Llama.
- **Lettura corretta.**
  - Su questi passaggi nessun metodo esistente supera p(UNKNOWN). Tutti i ΔW sono ≤ 0. L'unico non negativo con certezza è M3 su Qwen, con −0.014 e IC che contiene 0.
  - Il riferimento lascia però troppo poco spazio perché un vantaggio, se esistesse, si possa vedere. Le soglie non si toccano dopo i dati. Il limite si scrive.

### 4.2 HC4 entro C confusa con la famiglia [esplorativo, post hoc]

Composizione delle due classi, sui C principali, per il riferimento (M1-riferimento):

| Modello | Supportate (DUE / CONF / LOG) | Non supportate (DUE / CONF / LOG) |
|---|---|---|
| Qwen | 160 / 13 / 46 | 0 / 7 / 62 |
| Mistral | 136 / 0 / 1 | 9 / 12 / 24 |
| OLMo | 190 / 60 / 26 | 0 / 103 / 93 |
| Llama | 191 / 23 / 1 | 2 / 54 / 1 |

AUROC **dentro** la famiglia, dove ci sono almeno 10 risposte per classe:

| Modello · famiglia | p(UNKNOWN) | M2-senzaℓ2 | M3 | M1-Perplexity | M1-MeanTokenEntropy | M1-MSP |
|---|---|---|---|---|---|---|
| Qwen · LOG (62/46) | 0.38 | 0.65 | 0.54 | 0.31 | 0.31 | 0.13 |
| OLMo · CONF (103/60) | 0.30 | 0.42 | 0.31 | 0.41 | 0.45 | 0.09 |
| OLMo · LOG (93/26) | 0.41 | 0.69 | 0.49 | 0.31 | 0.35 | 0.09 |
| Llama · CONF (54/23) | 0.39 | 0.41 | 0.54 | 0.92 | 0.95 | 0.08 |

**Cosa ne segue**
- La regola di §6.2 mette insieme le tre famiglie. Le classi però sono quasi separate per famiglia: le supportate sono «DUE con le due alternative», le non supportate sono «LOG o CONF con un valore scelto».
- Un punteggio che dà più incertezza ai prompt LOG e CONF che ai DUE ottiene un'AUROC alta senza distinguere il supporto. È un caso di confondimento alla Simpson.
- Dentro la famiglia, i metodi che leggono il prompt sono al caso o sotto. Le conferme di HC4 entro C per M2, M2-senzaℓ2 e M3 restano formalmente valide, ma **non sostengono** la frase «discrimina il supporto fra le risposte non astenute».
- L'unico segnale che sopravvive dentro la famiglia è quello di **M1-Perplexity e M1-MeanTokenEntropy su Llama · CONF (0.92 e 0.95)**. Anche qui c'è un possibile effetto della forma: le risposte con l'attribuzione sono lunghe e copiate dal testo, quelle che scelgono un valore sono brevi. Il disegno non lo separa.
- M1-MSP dentro la famiglia è **rovesciato** (0.08–0.13). Chi sceglie un valore lo fa con un primo token più sicuro di chi riporta le due alternative.

Questa analisi è stata decisa dopo aver visto le composizioni. Non sostituisce l'esito preregistrato, ma ne limita la lettura.

### 4.3 Classificazione automatica

**Concordanza con la classificazione alla cieca di Simona (protocollo §4).**
- 100 risposte, campione stratificato, chiave aperta solo dopo la compilazione.
- **Concordanza 0.680**, kappa di Cohen 0.619. Sulla classe usata da HC4 (supportata / non supportata / esclusa): 0.770.
- **Esito: sotto 0.90. Gli esiti di HC4 si riportano con l'avvertenza prevista dal protocollo.**

I 32 disaccordi cadono in pochi gruppi:

| Gruppo | Casi | Lettura |
|---|---|---|
| «corretta» su risposte del lato C (un valore scelto, o un numero dedotto dagli edifici su RIM) | ~15 | le regole riservano «corretta» al lato B: la lettura umana giudica la risposta, le regole la descrivono |
| «X and Y (according to different archives)» | 6 | il classificatore dice «altro», Simona «entrambi affermati»: **lacuna delle regole** (attribuzione generica con «and») |
| «one source… another…» e risposte tagliate prima della seconda fonte | 3 | **errori del classificatore**, due dovuti al troncamento (§4.5) |
| alternative condizionali («1855 if…, or 1851 if…»), barra «seven days / eight days» | 3 | zone grigie fra alternative, attribuite ed entrambi affermati |
| «Ulmundolis» (la provincia) invece di «Ulmathend», su B | 2 (stessa risposta di OLMo in due origini) | **unico errore vero su B** in tutto il completo; il classificatore lo mette in «altro», quindi HC4 entro B resta NON VALUTABILE |

**Sensibilità alle etichette dubbie** (mia, precedente alla concordanza). Ho riclassificato come «attribuite» le «entrambi affermati» che citano le fonti o usano la barra. Le AUROC di HC4 cambiano al massimo di 0.03 e **nessun verdetto cambia**. Il più vicino alla soglia è M3 con le etichette di OLMo: 0.710 → 0.702.

**Per il prossimo test.** Due regole da scrivere prima: come trattare l'attribuzione generica («according to different archives») e la barra. Serve anche un secondo annotatore, con istruzioni che chiedono di descrivere la risposta e non di giudicarla.

### 4.4 HC0 di M1 con la generazione naturale (verificato)

- Nel Test M l'HM0 di M1 è stato calcolato con il minimo di 2 token di LM-Polygraph 0.7.0. Nel Test C la generazione è naturale (`min_new_tokens=0`).
- Controllo (`TestC_controlli_v1_revisionato.ipynb`, `C-controlli-1a`): stesse 400 domande TriviaQA, 24 token, stessi semi, generazione naturale, 4 modelli.
- **Regola R1, scritta prima:** soglia 0.70; il controllo può togliere celle M1, non aggiungerne.

| Stimatore | Qwen | Mistral | OLMo | Llama |
|---|---|---|---|---|
| MSP | 0.819 → 0.814 | 0.835 → 0.834 | 0.779 → 0.796 | 0.867 → 0.868 |
| Perplexity | 0.815 → 0.812 | 0.846 → 0.848 | 0.778 → 0.788 | 0.857 → 0.853 |
| MeanTokenEntropy | 0.830 → 0.829 | 0.865 → 0.866 | 0.812 → 0.821 | 0.871 → 0.868 |
| SemanticEntropy | 0.815 → 0.808 | 0.839 → 0.845 | 0.802 → 0.806 | 0.846 → 0.843 |
| PTrue | 0.284 → 0.287 ✗ | 0.402 → 0.400 ✗ | 0.704 → 0.701 | 0.351 → 0.352 ✗ |

- **HC0 confermato in 17 celle su 17**, scarto massimo 0.017. Nessun verdetto di M1 cambia.
- Le risposte greedy uguali a quelle del Test M sono 358–397 su 400: togliere il minimo di 2 token cambia alcune risposte, ma non la capacità degli stimatori.

### 4.5 Troncamento a 32 token (analisi di sensibilità, regola R2)

- Le 468 risposte non finite del riferimento (Qwen 73, OLMo 26, Llama 369) sono state rigenerate fino a 96 token con lo stesso codice. **Tutte** cominciano con il testo vecchio e p(UNKNOWN) è identico. A 96 token ne restano non finite 17 (Qwen 6, OLMo 10, Llama 1).
- **Qwen** cambia molto: 43 risposte del riferimento cambiano classe, quasi tutte da «attribuite» o «alternative» ad «astensione». Qwen elenca le due fonti e poi conclude «Therefore, the answer is UNKNOWN»: a 32 token si vedeva solo la prima parte. OLMo cambia 10 classi, Llama 1.
- **HC4 entro C ricalcolata:** cambierebbe 1 verdetto su 76. OLMo M1-MeanTokenEntropy passa da 0.697 a 0.701 (IC 0.658–0.742), da NON CONCLUSIVA a CONFERMATA, al bordo della soglia. Per R2 vale il verdetto del completo.
- Con le risposte finite, p(UNKNOWN) di Qwen entro C sale da 0.743 a 0.818 e M2-senzaℓ2 da 0.892 a 0.934: parte delle «supportate» erano in realtà astensioni.
- Per M1 e M4 la categoria nuova vale solo dove il loro testo coincide con la vecchia risposta del riferimento. Non aggiornabili: Llama 74 (M1) e 76 (M4), Qwen 12, OLMo 3.
- **Per il prossimo test:** limite di generazione più alto, oppure classificare solo le risposte finite.

### 4.6 LOG: astensione su B (descrittivo e rilettura, regola R3)

**Dove si concentra.** Quota di astensioni su LOG-B per tipo di attributo:

| Tipo | Qwen | Mistral | OLMo | Llama |
|---|---|---|---|---|
| anno | 0.66 | 0.86 | 0.04 | **1.00** |
| luogo | 0.32 | 0.48 | 0.00 | 0.68 |
| numero | 0.06 | 0.60 | 0.38 | 0.84 |
| persona | 0.10 | 0.00 | 0.00 | 0.42 |

La rigenerazione a 96 token non cambia questi valori.

**W su LOG separato per esito del modello su B.**

| Metodo | B corretta | B astenuta |
|---|---|---|
| p(UNKNOWN) | 0.94–1.00 | 0.67–0.95 |
| M1-MSP | 0.46–1.00 | 0.14–0.43 |
| M2-senzaℓ2 | 0.74–0.99 | 0.68–0.95 |
| M3 | 0.78–0.86 | 0.70–0.91 |

I metodi funzionano bene sulle coppie in cui il modello risponde a B. Dove il modello si astiene anche su B, la coppia B/C è quasi uguale per il modello, e i metodi che leggono la sua risposta (M1) si rovesciano.

**Rilettura di Simona** (20 coppie con B astenuta, 5 per modello, passaggi diversi, senza risposta attesa né risposta del modello).
- In **20 casi su 20** Simona ha ricavato dal passaggio la risposta attesa: 18 coincidono, 1 senza nome, 1 con un refuso.
- Li ha segnati tutti «dubbio», perché la risposta si ottiene solo con un **ragionamento per casi**. Per esempio: «Bravolis è sul Coridell **o** sullo Zorougan; ogni città sul Coridell conserva lo statuto a Jorisk; ogni città sullo Zorougan anche», quindi Jorisk.
- Nessun «no». **Per R3: l'astensione su LOG-B è un comportamento dei modelli, non un difetto dei passaggi.** Con 0 casi su 20, la quota di passaggi difettosi è probabilmente sotto il 14% (limite superiore al 95%). Non si può dire che sia zero.

**Lettura (interpretazione, non verificata da un test).** Una spiegazione plausibile è che davanti alla «or» i modelli si fermino invece di provare i due casi, soprattutto sugli anni. È coerente con lo Step 1, dove il rilevatore SQuAD scattava sulla «o». LOG-B misura quindi anche la capacità di ragionare per casi, e la sua accuratezza va letta così.

---

## 5. Insieme naturale (descrittivo, SQuAD 2.0 dev)

| W | p(UNKNOWN) | M3 | M2-senzaℓ2 | M1-SemanticEntropy |
|---|---|---|---|---|
| RIM-nat | 0.94–0.98 | 0.99 | 0.95–0.98 | 0.26–0.77 |
| DUE-nat | 0.78–0.96 | 0.95 | 0.54–0.94 | 0.74–0.83 |

**Comportamento**
- Su DUE-nat C i modelli scelgono un solo valore molto più spesso che su DUE sintetico:
  - Mistral 51%, Qwen 38%, OLMo 30%, Llama 31%;
  - sul sintetico DUE: 0–4.5%.
- Quando scelgono, scelgono la risposta originale di SQuAD più spesso del distrattore:
  - Qwen 54 contro 22;
  - Mistral 74 contro 28;
  - OLMo 39 contro 21;
  - Llama 42 contro 19.
- L'ordine «span or distrattore» è estratto con un seme. Il risultato è compatibile con la memoria degli articoli, ma anche con un distrattore meno plausibile nel contesto. Non lo si può separare con questi dati.
- Su RIM-nat C il 70–89% sono astensioni.
- Su B l'accuratezza è 0.91–0.95.

---

## 6. Cosa è verificato e cosa resta da verificare

### Verificato

| Cosa | Come |
|---|---|
| Esecuzione completa e coerente | stato dei lavori, impronte, copertura, ricaricamento, allineamenti (§1) |
| Calcolo di W, ΔW, D e HC4 | ricalcolo indipendente dai file grezzi: stime identiche, IC entro ±0.01 |
| Applicazione delle soglie e della regola dei 3 su 4 | confronto voce per voce con §7 |
| Dati usati | gli SHA di C-sel-8 sono controllati dal notebook prima delle inferenze; deficit DUE-nat dichiarato |
| Robustezza di HC4 a un gruppo di etichette dubbie | sensibilità: nessun verdetto cambia (§4.3) |
| Concordanza del classificatore | 100 risposte alla cieca: 0.68, sotto 0.90 → avvertenza su HC4 (§4.3) |
| HC0 di M1 con la generazione naturale | 17/17 celle confermate, scarto ≤ 0.017 (§4.4) |
| Troncamento | 468 risposte rigenerate a 96 token: 1 verdetto HC4 su 76 cambierebbe, al bordo; vale il completo (§4.5) |
| Passaggi LOG-B | rilettura di Simona: risposta ricavabile 20/20 per deduzione; astensione dei modelli (§4.6) |

### Da verificare, e come

| # | Cosa | Perché | Come farlo | Costo |
|---|---|---|---|---|
| 1 | **Revisione semantica documentata** | il protocollo chiede 20 sintetiche, 30 RIM-nat (con la quota di C ancora rispondibili) e 20 DUE-nat. Il campione di 70 coppie esiste (`testC_selezione_risultati/C-sel-8/`, dentro lo ZIP della selezione), ma gli esiti per coppia non sono stati scritti | dichiarato come limite (§7). Controlli parziali già fatti: rilettura LOG 20/20 (§4.6) e concordanza del classificatore (§4.3) | — |
| 2 | **HC4 senza confondimento con la famiglia** | §4.2 | nuovo test preregistrato: AUROC stratificata per famiglia (media delle AUROC dentro la famiglia, o famiglia come strato nel ricampionamento), oppure un disegno in cui ogni famiglia abbia entrambe le classi in quantità sufficiente. Sui dati attuali resta esplorativo | protocollo breve; nessuna GPU per l'esplorativo |
| 3 | **Effetto della forma della risposta su M1** | supportata = due valori, non supportata = un valore | esplorativo sui dati attuali: limitare all'incertezza sul primo token del valore, o appaiare per lunghezza | solo CPU |
| 4 | **Soffitto del riferimento** | HC2 e HC3 erano irraggiungibili per 3 modelli su 4 | nel prossimo disegno: istruzione senza UNKNOWN offerto, oppure coppie più difficili, così che p(UNKNOWN) non sia vicino a 1. Da preregistrare | nuovo test |
| 5 | **Perché i modelli si astengono su LOG-B** | i passaggi sono a posto (§4.6), il limite è del modello | varianti di LOG senza «or» con la stessa catena (per esempio due regole e un'appartenenza certa), da confrontare con LOG | nuovo test |
| 6 | **Regole del classificatore e secondo annotatore** | concordanza 0.68 (§4.3) | regole scritte per l'attribuzione generica e la barra; due annotatori con istruzioni descrittive | prossimo test |
| 7 | **Limite di generazione** | risposte di Qwen tagliate prima della conclusione (§4.5) | limite più alto o sola classificazione delle risposte finite | prossimo test |
| 8 | **Replica del vantaggio M4-LoRA su AND** (dal Test M) | non coperta qui; nel Test C M4-LoRA ha ΔW −0.147 | test separato, già segnato | — |

---

## 7. Valutazione del lavoro come ricerca scientifica

**Punti di forza** (sopra la media di molti lavori pubblicati sull'argomento)
- **Preregistrazione vera.** Ipotesi, soglie, numerosità minime e formulazioni sono scritte prima dei dati. Gli esiti negativi sono riportati come tali (HC2 0 ovunque, per due test di fila).
- **Coppie minime con controlli della forma.** LOG è un controllo forte e ben pensato: la «or» è identica in B e in C. Le entità sono inventate.
- **Controlli positivi prima delle coppie (HC0).** Un metodo che non funziona sul suo dominio non viene giudicato qui. M2-Qwen collassato è escluso, con la causa documentata.
- **Riferimento forte e semplice.** p(UNKNOWN) senza addestramento è il termine di confronto. È il punto che rende il risultato utile e onesto.
- **Tracciabilità.** Ci sono impronte, SHA di dati e script, versioni dei pacchetti, GPU registrata, ripresa controllata, verifica indipendente della selezione e ricalcolo indipendente degli esiti.
- **Correzioni documentate** (C-sel-4 → C-sel-8), con la regola «non correggere a maggioranza, dichiarare il deficit».

**Debolezze e limiti**
- **Validità esterna limitata.**
  - Una sola istruzione, l'inglese, passaggi da template.
  - 4 modelli da 7–12 miliardi di parametri (Mistral-Nemo è 12B), nessun modello grande o chiuso.
  - Il naturale è solo descrittivo e probabilmente contaminato dalla memoria.
- **Soffitto del riferimento.** Il disegno rende HC2 e HC3 quasi irraggiungibili. Il protocollo lo sapeva in parte (margine riportato), ma non ha fissato prima cosa fare quando il margine è sotto la soglia.
- **HC4 mal identificata.** Con classi separate per famiglia, il confronto preregistrato non misura quello che dichiara. È il difetto principale del disegno, emerso solo dai dati.
- **LOG-B non determinato nel comportamento** per 3 modelli su 4. Il controllo forte è valido sul testo (rilettura 20/20), ma richiede un ragionamento per casi che i modelli spesso non fanno.
- **Classificatore automatico** con concordanza 0.68 sul campione umano: le regole hanno zone grigie (attribuzione generica, barra) e il troncamento ha sporcato alcune etichette di Qwen.
- **Molti confronti senza correzione** (decine di combinazioni di ipotesi, metodi e modelli). La regola dei 3 su 4 attenua il problema ma non lo risolve. Le analisi per famiglia sono nominali.
- **Revisione semantica non documentata coppia per coppia.** Il campione di 70 coppie (20 sintetiche, 30 RIM-nat, 20 DUE-nat) è stato preparato e il completo è partito con la revisione dichiarata approvata, ma non esiste un esito scritto per ogni coppia.
- **Un solo revisore umano** per la semantica e per il classificatore. Per una pubblicazione servirebbero due revisori alla cieca con concordanza (kappa).

**Valutazione complessiva**
- È un lavoro metodologicamente serio, più rigoroso nel processo (preregistrazione, controlli, tracciabilità) di quanto sia comune in quest'area.
- **Il risultato più solido, replicato fra Test M e Test C:** p(UNKNOWN) sul primo token, senza addestramento, non è superato da nessuno dei metodi esistenti provati. Né gli stimatori di LM-Polygraph, né la sonda di answerability SIRIN, né il giudice zero-shot, né le sonde di Obeso. Questo vale nel riconoscere un contesto che non determina la risposta.
- **Secondo risultato, utile per la libreria.** Gli stimatori di incertezza sulla risposta (M1) confondono l'astensione sicura con la bassa incertezza. Per esempio M1-MSP su Qwen ha W(RIM) = 0.085: il modello dice «UNKNOWN» con sicurezza, e il metodo lo legge come «certo».
- **Quello che non si può ancora dire:**
  - che qualche metodo «rilevi le allucinazioni con contesto», perché HC4 entro B non è valutabile ed entro C è confusa;
  - che i risultati valgano fuori da questo formato.
- **Per una pubblicazione** servono almeno una revisione semantica documentata (punto 1 di §6) e l'avvertenza sul classificatore, la dichiarazione esplicita dei limiti di §4 e, idealmente, un test con un riferimento lontano dal soffitto e una HC4 stratificata.

---

## 8. File

- Selezione C-sel-8: `testC_selezione_risultati/C-sel-8/` (ZIP della selezione `aaad5c5e…`, verifica 199, diagnosi, audit, nota di chiusura).
- Dati e uscite: `testC_completo_risultati/`. Contiene:
  - `completo_Drive_20261113.zip` (sha256 `da84d9bf…`);
  - `testC_completo_risultati.zip` (`cc89298c…`);
  - `rapporto_C.txt`, `esiti_C.json`, `tabella_C.csv`.
- Ricalcolo indipendente e analisi esplorative: `strumenti_resoconto_C/`. Si lanciano con `python -I <script> <cartella dello ZIP estratto>`:
  - `ricalcolo.py`;
  - `sensibilita_hc4.py`;
  - `hc4_per_famiglia.py`.
- Campione per il controllo del classificatore: `campione_classificazione.csv` (alla cieca) e `campione_classificazione_chiave.json`, dentro lo ZIP. Foglio compilato da Simona: `testC_completo_risultati/campione_classificazione_Simona_compilato_definitivo.xlsx`; esito: `concordanza_classificatore_esito.txt`; script: `strumenti_resoconto_C/concordanza_classificatore.py`.
- Controlli dopo il completo: notebook `TestC_controlli_v1_revisionato.ipynb` (`C-controlli-1a`) con la revisione `TestC_controlli_revisione_notebook.md`; risultati in `testC_controlli_risultati/`:
  - `controlli_Drive_20261113.zip`, `rapporto_controlli.txt`, `controlli_risultati.json`;
  - tabelle `hc0_M1.csv`, `hc4_sensibilita.csv`, `troncamento_transizioni.csv`, `log_accuratezza.csv`, `log_W_per_esito.csv`;
  - rilettura LOG compilata: `rilettura_LOG_Simona.xlsx`.
