# Step 2, riepilogo (bozza v1, 13 novembre)

Progetto: indeterminatezza logica negli LLM, verso un metodo e una libreria Python (ispirazione: lm-polygraph).
Modelli: Qwen3-8B, Mistral-Nemo-Instruct-2407, OLMo-2-7B-Instruct, Llama-3.1-8B-Instruct, su tutti i test dello Step 2. Giudice M3: Qwen3-4B.
Test: U (8 nov), U2 (9 nov), M notebook A (10 nov) e B (11 nov), C (12–13 nov).
Dettagli e numeri completi nei resoconti di questa cartella: `Risultati_testU.md`, `Risultati_testU2.md`, `Risultati_testM_A.md`, `Risultati_testM_B.md`, `Risultati_testC.md` (bozza v2). Questo file non aggiunge analisi nuove: riassume e collega.

## In breve

1. **Il risultato più solido dello Step 2 è negativo per i metodi esistenti e positivo per il riferimento semplice.** La probabilità che il modello risponda UNKNOWN sul primo token, p(UNKNOWN), senza addestramento, non è superata da nessuno dei metodi pubblicati provati, né sulle storie logiche (Test M, 800 coppie) né sui passaggi di testo (Test C, 600 coppie). I metodi provati sono 4 stimatori di LM-Polygraph, la sonda di answerability di SIRIN (originale e senza ℓ2), il giudice zero-shot di SIRIN e le sonde di Obeso et al. Unica eccezione confermata: M4-LoRA su Llama nel Test M (+8.6 punti di W), trainata dalla famiglia AND e non replicata nel Test C (ΔW −0.147).
2. **p(UNKNOWN) funziona bene solo in prosa.** Nel Test U separa C da B in 4 modelli su 4 solo nel formato in prosa; nel Test U2 si conferma 4 su 4 anche senza la frase che spiega la riga incerta. Nei formati simbolici il segnale è debole o rovesciato.
3. **Gli stimatori di incertezza sulla risposta confondono l'astensione sicura con la certezza.** Quando un modello dice «UNKNOWN» con sicurezza, MSP, perplexity ed entropia lo leggono come bassa incertezza. Il caso più netto è Mistral nel Test M (W ≈ 0.30, sotto il caso) e M1-MSP su Qwen nel Test C (W su RIM 0.085). Il meccanismo è un'interpretazione plausibile dai valori medi, non un test.
4. **Quasi tutti i metodi dipendono molto dall'operatore logico e dalla forma.** Un metodo può essere quasi perfetto su OR e sotto il caso su AND (Llama con M2: 0.963 contro 0.004). Anche varianti logicamente equivalenti (POS/NOT) cambiano molto i W. Solo p(UNKNOWN) di Qwen è stabile su tutte le famiglie. Queste analisi sono in parte preregistrate (famiglie in M2) e in parte esplorative.
5. **Sulle allucinazioni con contesto (Test C) non si può ancora dire che un metodo le rilevi.** Sui B sintetici i modelli non sbagliano mai (0 errori), quindi HC4 entro B non è valutabile. HC4 entro C è formalmente confermata per alcuni metodi, ma è confusa con la famiglia del passaggio [esplorativo, post hoc].
6. **Comportamento dei modelli.** Con il contesto i modelli riportano bene le due alternative («1821 or 1823») e si astengono quando l'informazione manca. Davanti a una disgiunzione si astengono anche quando i due rami portano allo stesso valore (LOG-B: Llama 74%, Mistral 49%, Qwen 29%). La rilettura dei passaggi (20 su 20 deducibili) indica che il limite è dei modelli, non dei passaggi.

## Che cosa abbiamo misurato

- **Coppie minime B/C**, come nello Step 1. B ha una risposta determinata, C no (la risposta corretta è UNKNOWN). Stessa storia, cambia un solo valore.
- **W**: quota di coppie in cui il punteggio di incertezza di C supera quello di B (pareggi a mezzo punto), mediata per storia o passaggio, con IC al 95% su 2000 ricampionamenti.
- **ΔW**: W(metodo) − W(p(UNKNOWN)) sulle stesse coppie e nello stesso ambiente.
- **Controllo positivo (HM0, HC0)**: un metodo viene giudicato sulle coppie solo se funziona sul suo dominio (AUROC ≥ 0.70 su TriviaQA, SQuAD 2.0 o LongFact). Altrimenti è NON VALUTABILE.
- **Regola della libreria**: un'affermazione generale su un metodo richiede la conferma in almeno 3 modelli su 4.
- **Formati**: P−S (prosa senza frase di spiegazione, formato principale dal Test M), S−S (simbolico, descrittivo); nel Test C passaggi di testo con entità inventate (famiglie RIM, DUE, CONF, LOG) e un insieme naturale da SQuAD 2.0 dev (descrittivo).

## Risultati per test

| Test | Domanda | Risultato |
|---|---|---|
| U | p(UNKNOWN) separa C da B nei 4 modelli? Una soglia fissata su un formato si trasferisce? La «o» fa scattare il rilevatore SQuAD? | HU1 confermata 4 su 4 solo in prosa V2 (W 0.914 Qwen, 0.834 Mistral, 0.736 OLMo, 0.839 Llama); su ADD e V1 un solo modello per formato, e in V1 OLMo e Llama vanno nella direzione opposta. HU2: la soglia di ADD non si trasferisce in nessun formato. HO1 rovesciata 4 su 4: una «o» neutra abbassa il punteggio del rilevatore SQuAD; lo fa salire la modifica che crea due valori. Polarità NON VALUTABILE (nessuna domanda negata passa il filtro). |
| U2 | Il risultato in prosa dipende dalla frase che spiega la riga incerta? | No. Senza la frase, HI1 4 su 4 (W 0.975, 0.783, 0.694, 0.746). HI2 (la frase migliora W) 2 su 4: Mistral e Llama sì, Qwen scende. HI3 4 su 4: il template in prosa batte quello simbolico, ma cambiano anche istruzione e domanda, quindi non si attribuisce alla sola notazione. La frase agisce sulla risposta generata (molti più UNKNOWN, anche sui B: Llama dal 5% al 79%), non sull'ordinamento. |
| M, notebook A | I metodi pubblicati (LM-Polygraph, giudice SIRIN, sonde Obeso) riconoscono l'indeterminatezza e fanno meglio di p(UNKNOWN)? | M1: HM1 al massimo 2 su 4 (MeanTokenEntropy, SemanticEntropy); HM2 0 su 17 celle, tutti i ΔW negativi con IC sotto 0; su Mistral W ≈ 0.30. M3: HM1 confermata (0.693), sotto p(UNKNOWN) in prosa. M4-LoRA (solo Llama): HM1 e HM2 confermate, ΔW +0.086 [+0.039, +0.135], trainato da AND [esplorativo]. M4-lin compatibile con il caso. |
| M, notebook B | La sonda di answerability SIRIN addestrata su SQuAD 2.0 riconosce l'indeterminatezza? | M2 originale: HM0 3 su 4 (Qwen collassata, 0.499, per la ℓ2 fissa del trainer); HM1 1 su 3 valutabili (Mistral); HM2 0. M2-senzaℓ2 (variante preregistrata dopo la diagnostica): HM0 4 su 4; HM1 1 su 4; HM2 0. Per famiglia: solo M2-senzaℓ2 su OR arriva a 4 su 4 (nominale). |
| C | Sui passaggi di testo i metodi riconoscono un contesto che non determina la risposta, e distinguono le risposte supportate da quelle non supportate? | HC1 confermata per molti metodi (M1-MSP e SemanticEntropy 4/4, M2 3/3, M2-senzaℓ2 4/4, M3, M4-LoRA). HC2 0 ovunque. HC3 non confermata con la regola dei 3 su 4. HC4 entro B NON VALUTABILE (0 errori su B). HC4 entro C confermata per M2, M2-senzaℓ2 e M3, ma confusa con la famiglia; concordanza del classificatore 0.68 (sotto 0.90), quindi HC4 si legge con l'avvertenza. |

## Test M in sintesi (notebook A e B insieme)

800 coppie P−S su 200 storie, 4 modelli, riferimento p(UNKNOWN) nello stesso ambiente. Conteggi sui modelli valutabili.

| Metodo | HM0 (controllo positivo) | HM1 (riconosce C) | HM2 (meglio di p(UNKNOWN)) | Nota |
|---|---|---|---|---|
| M1-MSP | 4/4 | 0/4 | 0/4 | Mistral rovesciato (0.305) |
| M1-Perplexity | 4/4 | 0/4 | 0/4 | quasi uguale a MSP su risposte brevi |
| M1-MeanTokenEntropy | 4/4 | 2/4 (Qwen, Llama) | 0/4 | |
| M1-SemanticEntropy | 4/4 | 2/4 (Qwen, Llama) | 0/4 | |
| M1-PTrue | 1/4 (solo OLMo) | 0/1 | 0/1 | comportamento della libreria pubblicata, non modificata |
| M2 originale (SIRIN) | 3/4 (Qwen collassa) | 1/3 (Mistral) | 0/3 | «risultato sull'implementazione SIRIN e sulla configurazione adottata» |
| M2-senzaℓ2 | 4/4 | 1/4 (Mistral) | 0/4 | variante della configurazione, non metodo pubblicato |
| M3 giudice zero-shot (Qwen3-4B) | 0.805 | confermata (0.693) | 0 su 4 riferimenti, descrittivo | quasi perfetto su OR, sotto il caso su AND |
| M4-lin (Obeso, solo Llama) | 0.848 | NON CONCLUSIVA (0.481) | no | |
| M4-LoRA (Obeso, solo Llama) | 0.890 (= autori) | confermata (0.823) | **confermata, +0.086** | guadagno da AND [esplorativo]; su OR e IMPLIES il riferimento è migliore |

Riferimento p(UNKNOWN) su P−S: W 0.975–0.980 (Qwen), 0.78 (Mistral), 0.69–0.70 (OLMo), 0.74–0.75 (Llama). Il margine possibile per HM2 su Qwen era 0.020–0.025, sotto la soglia +0.05: per Qwen HM2 era quasi irraggiungibile.

**Lettura unica del Test M.** I metodi pubblicati passano i loro controlli positivi, ma sulle coppie B/C riconoscono l'indeterminatezza in modo instabile tra modelli e tra famiglie logiche. Nessuno fa meglio di p(UNKNOWN), tranne M4-LoRA su un solo modello e soprattutto su una sola famiglia. La penalità ℓ2 fissa del trainer di SIRIN fa collassare la sonda di Qwen (ablation: AUROC di validazione da 0.575 a 0.941 a 2000 + 400 esempi; 0.925 a 1000 + 200), ma anche la sonda che funziona su SQuAD non separa le coppie meglio del riferimento.

## Test C in sintesi

600 coppie sintetiche principali (DUE, CONF, LOG) su 200 passaggi, più RIM come controllo di dominio e 399 coppie naturali (descrittive).

- **Il riferimento è al soffitto.** p(UNKNOWN) ha W 0.94–0.98. Il margine per HC2 era sotto 0.05 in 3 modelli su 4, e HC3 era impossibile per ogni metodo con W > 0.90. «HC2 non confermata» significa «nessun metodo supera il riferimento», non che il margine non esista.
- **HC4 entro C confusa con la famiglia** [esplorativo, post hoc]. Le risposte supportate vengono quasi tutte da DUE, le non supportate da CONF e LOG. Dentro la stessa famiglia i metodi che leggono il prompt sono vicini al caso o sotto (AUROC 0.30–0.69). L'unico segnale che sopravvive è M1-Perplexity e MeanTokenEntropy su Llama · CONF (0.92–0.95), con un possibile effetto della lunghezza della risposta.
- **Controlli dopo il completo**: HC0 di M1 con la generazione naturale confermato in 17 celle su 17; troncamento: 1 verdetto HC4 su 76 cambierebbe, al bordo, e vale il completo; rilettura LOG-B 20 su 20 deducibili.
- **Naturale** (descrittivo): su DUE-nat C i modelli scelgono un solo valore molto più spesso che sul sintetico (30–51% contro 0–4.5%), e scelgono la risposta originale di SQuAD circa 2–2.6 volte più spesso del distrattore. Compatibile con la memoria degli articoli, non dimostrato.
- **Revisione semantica** delle 70 coppie del campione: dichiarata come limite (decisione di Simona), non documentata coppia per coppia.

## Che cosa regge, attraverso i test

| Risultato | Dove | Quanto è solido |
|---|---|---|
| p(UNKNOWN) separa C da B in prosa | U (V2), U2 (P−S), M, C | replicato in 4 test e 4 modelli; preregistrato |
| Nessun metodo pubblicato provato supera p(UNKNOWN) in prosa | M (A e B), C | preregistrato in due test; unica eccezione M4-LoRA su Llama nel Test M, non replicata nel Test C |
| Gli stimatori di incertezza sulla risposta leggono l'astensione sicura come certezza | M (Mistral), C (RIM, M1-MSP dentro la famiglia) | osservato in due test; il meccanismo è un'interpretazione |
| Forte dipendenza dalla famiglia logica e dalla forma | Step 1, M (A e B), C | in parte preregistrato (famiglie in M2), in parte esplorativo |
| Il rilevatore SQuAD non reagisce alla parola «o» in sé | U | preregistrato (HO1 rovesciata 4/4); corregge in parte lo Step 1 |
| Astensione eccessiva davanti alla disgiunzione | C (LOG-B), coerente con lo Step 1 | descrittivo, con rilettura dei passaggi |

## Che cosa non si può dire

- Che un metodo «rilevi le allucinazioni con contesto»: HC4 entro B non è valutabile ed entro C è confusa con la famiglia.
- Che M4-LoRA sia in generale migliore di p(UNKNOWN): un solo modello, guadagno da una sola famiglia, non replicato nel Test C.
- Che p(UNKNOWN) funzioni in qualunque formato: nei formati simbolici è debole o rovesciato (Test U), e dipende dalla famiglia in 3 modelli su 4 (Test M).
- Che i risultati valgano per modelli grandi, chiusi, per altre lingue o per testi reali: 4 modelli da 7–12B, inglese, storie e passaggi da template; il naturale è solo descrittivo.
- Che la sonda di SIRIN «non funzioni»: il collasso su Qwen è un risultato sull'implementazione SIRIN e sulla configurazione adottata.

## Limiti trasversali

- **Validità esterna**: 4 modelli open-weights tra 7 e 12B, una sola lingua, testi da template, una sola istruzione per test.
- **Soffitto del riferimento**: quando p(UNKNOWN) è vicino a 1, un vantaggio dei metodi non si può vedere. Il protocollo riportava il margine ma non fissava prima cosa fare sotto soglia.
- **Molti confronti** senza correzione; la regola dei 3 su 4 attenua ma non risolve. Le analisi per famiglia sono nominali.
- **Un solo revisore umano** per la semantica e per il classificatore (concordanza 0.68).
- **M2-senzaℓ2** è stata definita dopo la diagnostica su Qwen: regole preregistrate, scelta non indipendente.
- **Riserva RAM** nel notebook B: 1000 + 200 esempi invece di 2000 + 400.

## Le domande iniziali, aggiornate

| Domanda | Stato dopo lo Step 2 |
|---|---|
| Quali pattern fanno scattare l'allarme | Il rilevatore SQuAD sale quando la modifica crea due valori, non per la parola «o» (Test U). I metodi pubblicati dipendono molto dall'operatore logico (AND, OR, IMPLIES) e dalla polarità della regola. |
| Posizione dell'incertezza | Non ripresa nello Step 2. |
| Bidirezionalità e polarità | Ancora NON VALUTABILE: nessuna formulazione della domanda negata ha superato il filtro (Test U). Le varianti POS/NOT del Test M mostrano una forte sensibilità alla trasformazione [esplorativo]. |
| Campione piccolo o effetto reale | Il risultato principale (p(UNKNOWN) non superato) è replicato tra Test M e Test C, su 800 e 600 coppie con IC per storia o passaggio. |
| Bias e falle matematiche | Controllati: allineamento fra test ≤ 1e-16, controlli positivi, ricalcoli indipendenti, impronte e SHA. Trovati e dichiarati: soffitto del riferimento, confondimento di HC4 con la famiglia. |
| Llama e altri open-weights | Llama aggiunto in tutti i test dello Step 2. |
| Allucinazioni | Test C eseguito: i modelli non sbagliano sui B, quindi le allucinazioni con contesto non sono ancora misurabili con questo disegno. |

## Che cosa significa per la libreria

1. **p(UNKNOWN) come misura di base**, senza addestramento, con la documentazione dei suoi limiti: funziona in prosa, dipende dal formato e dalla famiglia logica, ha un soffitto che nasconde i vantaggi degli altri metodi.
2. **Il benchmark delle coppie B/C come contributo principale.** Rivela su metodi già pubblicati cose che i loro controlli abituali non mostrano: inversioni (Mistral con M1), dipendenza dall'operatore, collasso di una configurazione.
3. **Il protocollo di validazione come parte della libreria**: controllo positivo prima delle coppie, riferimento p(UNKNOWN) nello stesso ambiente, W e ΔW con IC per storia, regola dei 3 su 4, analisi per famiglia, formule di lettura fissate prima.
4. **Separare «incertezza sulla risposta» da «la risposta è non determinabile».** Gli stimatori classici misurano la prima; l'astensione sicura va trattata a parte.
5. **Gli adattatori ai metodi esistenti** (LM-Polygraph, SIRIN, sonde Obeso) possono stare nella libreria come esempi, con i loro ambienti fissati, ma non come dipendenze obbligatorie.

## Test futuri già individuati (non avviati)

- HC4 stratificata per famiglia, preregistrata; un disegno che produca errori sui B.
- Un riferimento lontano dal soffitto: istruzione senza UNKNOWN offerto, o coppie più difficili.
- Replica del vantaggio M4-LoRA su AND, su storie nuove con confronto per famiglia fissato prima.
- LOG senza «or» con la stessa catena logica, per capire l'astensione su LOG-B.
- Regole del classificatore e un secondo annotatore alla cieca.
- Polarità con una formulazione negata che i modelli eseguano.

## File

- Resoconti: `Risultati_testU.md`, `Risultati_testU2.md`, `Risultati_testM_A.md`, `Risultati_testM_B.md`, `Risultati_testC.md`.
- Protocolli: `Protocollo_testU_v2.md`, `Protocollo_testU2_istruzione_v2.md`, `Protocollo_testM_metodi_v2.md`, `Nota_M2_configurazione_v2_2.md`, `Protocollo_testC_v3.md`.
- Dati: `testU_risultati/`, `testU2_risultati/`, `testM_risultati/`, `testC_selezione_risultati/`, `testC_completo_risultati/`, `testC_controlli_risultati/`.
- Revisione indipendente del Test C: `Revisione_testC_Fable.md`.
- Step 1: `../Step1_verifica/Riepilogo_Step1.md`.