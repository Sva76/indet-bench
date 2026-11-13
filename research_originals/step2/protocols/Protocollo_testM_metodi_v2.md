# Test M (metodi esistenti sulle coppie B/C): protocollo v2

Data: 10 novembre 2026. Stato: **scelte di §8 della v1 approvate da Simona (9 novembre), nessun dato raccolto**.
Riferimenti: `Protocollo_testM_metodi_v1_bozza.md`, `Risultati_testU.md` (v2), `Risultati_testU2.md`, `PHI/Step1_verifica/Riepilogo_Step1.md`.

## Cosa cambia rispetto alla v1
1. **Scelte approvate.** Entrano tutti e quattro i metodi, in due notebook. Si comincia dal notebook A (M1, M3, M4 e il riferimento p(UNKNOWN)), poi viene il notebook B (M2). Il giudice SIRIN addestrato con LoRA resta fuori e può entrare in una v1.1. Si usano le librerie originali in ambienti `uv` isolati.
2. **NON ESEGUITO.** Se una libreria non si installa o non gira, il metodo si riporta come NON ESEGUITO insieme al log dell'errore. Non si fanno reimplementazioni ad hoc che non siano state concordate.
3. **Controlli positivi (HM0) ridefiniti.**
   - M4 si controlla sul test LongFact annotato degli autori.
   - Per M2 le 400 domande di verifica restano fuori sia dall'addestramento sia dalla scelta degli iperparametri.
   - M1 si controlla stimatore per stimatore sulla correttezza della risposta. Il controllo SQuAD sull'answerability diventa una misura descrittiva separata.
4. **M4 con due sonde sulle stesse risposte.** La sonda lineare e la sonda LoRA-KL rilasciate valutano le stesse risposte, generate da Llama base.
5. **Limite di HM2 per Qwen.** Il limite è dichiarato (§5) e la soglia resta fissa.
6. **Vincoli delle librerie corretti (§6).** Gli ambienti sono tre, non uno.
7. **Prova obbligatoria per ogni metodo**, sul suo controllo positivo, prima della run completa.

## 1. Perché questo test
Il Test U e il Test U2 hanno mostrato che p(UNKNOWN) separa C da B in prosa in tutti e 4 i modelli, senza addestramento. Questo vale anche senza la frase che spiega la riga incerta (P−S, W tra 0.69 e 0.98). Nel formato simbolico invece il segnale resta debole.

La domanda è: **i metodi già pubblicati per rilevare incertezza, risposte non supportate e domande senza risposta riconoscono l'indeterminatezza logica?** Se non la riconoscono, le coppie B/C mostrano un limite dei metodi in uso, ed è questo il contributo del benchmark per la libreria.

Nessun metodo si addestra sulle storie. Ogni metodo si usa come è stato pubblicato, oppure addestrato sui dati del suo articolo, e poi si applica senza modifiche alle coppie B/C.

## 2. Metodi

| Famiglia | Metodo | Fonte e versione | Addestramento | Modelli |
|---|---|---|---|---|
| **M1. Incertezza sulle uscite** | Maximum Sequence Probability (MSP), Perplexity, Mean Token Entropy, Semantic Entropy (5 campioni), p(True) | LM-Polygraph 0.7.0 (PyPI) | nessuno | i 4 modelli |
| **M2. Sonda di answerability** | sonda SIRIN sugli stati interni del prompt, con attention pooling (la configurazione migliore dell'articolo per l'answerability) | SIRIN, commit `ef3bed1` | su SQuAD 2.0, come nell'articolo | i 4 modelli |
| **M3. Giudice di answerability** | giudice zero-shot Qwen3-4B con il prompt di answerability di SIRIN (testo in §2.2) | SIRIN, commit `ef3bed1` | nessuno | un solo giudice, applicato ai prompt (sono gli stessi per tutti i modelli) |
| **M4. Sonde pubblicate con pesi rilasciati** | sonde di Obeso et al. 2025 per entità allucinate: **M4-lin** (lineare) e **M4-LoRA** (LoRA-KL, λ_KL = 0.05). Punteggio per token, massimo sulla risposta | codice `obalcells/hallucination_probes` commit `295450e`; pesi `obalcells/hallucination-probes` revisione `db581ce` | già addestrate dagli autori | solo Llama-3.1-8B-Instruct |
| **Riferimento** | p(UNKNOWN) grezza sul primo token | codice del Test U2 | nessuno | i 4 modelli, ricalcolata in ogni ambiente |

I modelli e le revisioni sono gli stessi del Test U2: Qwen3-8B (`enable_thinking=False`), Mistral-Nemo-Instruct-2407, OLMo-2-1124-7B-Instruct e Llama-3.1-8B-Instruct (0e9e39f2). Si usano bf16 e attention eager.

### 2.1 Come si applica ogni metodo
- **M1.** I prompt sono quelli del Test U2, con il chat template di ogni modello. La risposta si genera in greedy fino a 8 token. Gli stimatori sono quelli della libreria, con i parametri di default. Per Semantic Entropy si usano 5 campioni con la temperatura di default della libreria e il modello NLI di default. Il seme è fisso. Il segno è quello della libreria: un valore più alto indica più incertezza. Con risposte di una parola, molte misure di sequenza si riducono a quelle sul primo token. Anche questo è un risultato da riportare.
- **M2.** Si fissa prima del notebook B, in una nota di aggiornamento a questo protocollo, con la configurazione esatta dell'articolo (strato, pooling, iperparametri). I vincoli sui dati sono già fissati in §3.
- **M3.** Si usano la classe di giudice locale di SIRIN (`SequenceDecoderJudge` con `HfJudgeConfig`) e Qwen3-4B con `enable_thinking=False`. Il punteggio è la probabilità della cifra «1» (contesto non sufficiente), normalizzata su {«0», «1»}, letta sui logit del primo token della risposta.
- **M4.** La risposta si genera una sola volta con Llama base (greedy, 8 token, come nel Test U2). Le due sonde valutano poi quella stessa risposta con un forward su prompt più risposta:
  - **M4-lin** legge lo strato 30 del modello base;
  - **M4-LoRA** legge lo stesso strato con l'adattatore LoRA attivo.

  Il punteggio è il massimo della probabilità per token sui token della risposta, escluso il token di fine turno. Le due sonde vedono quindi lo stesso testo e differiscono solo per la sonda. La sonda è stata addestrata su testi lunghi (entità inventate), quindi la nostra è una prova di trasferimento.

### 2.2 Prompt del giudice M3 (testo di SIRIN, `sirin/ui/presets.py`, `_ANSWERABILITY_JUDGE_PROMPT`)
> You are given a context passage and a question, with no answer. Decide whether the context contains enough information to answer the question.
> Dialogue: "{sample}"
> Reply with 1 if the context is NOT sufficient to answer the question, or 0 if it IS sufficient. Answer with a SINGLE character that is the digit 1 or the digit 0. Do not output JSON, quotes, spaces, reasoning, or any other character. Your entire reply must be exactly one digit:

Il campo `{sample}` si costruisce come in SIRIN (`_inspection_prompt`, con `dialogue_format='{question}'`): `Context:\n{regola e fatti}\n\nQuestion:\n{domanda}`. Nel repository questo prompt è usato con un giudice via API. Qui lo si usa con il giudice locale della stessa libreria, ed è l'unico adattamento. Va dichiarato nel resoconto.

## 3. Dati
- **Formato principale: P−S**, cioè la prosa con l'istruzione neutra del Test U2, sulle stesse 200 storie V2 (seme 20261120, 2400 prompt, 800 coppie B/C).
- **Controllo: S−S**, cioè il formato simbolico con l'istruzione neutra, sulle stesse storie (2400 prompt).
- Per M2 e M3 il «contesto» è la regola con i fatti e la «domanda» è «Is approval given?» (in P−S) oppure «Is approval granted?» (in S−S). Il testo è quello dei prompt del Test U2, senza l'istruzione di risposta.
- **Coppie.** Si usano le coppie del Test U2, appaiate per `pair_key`. Una coppia esce da un metodo solo se il metodo non dà un punteggio su B o su C (errore o valore non finito). Queste esclusioni si contano e si riportano.

### 3.1 Controlli positivi (HM0)
| Metodo | Dati | Misura |
|---|---|---|
| **M1**, ogni stimatore separatamente | 400 domande TriviaQA (rc.nocontext, validation, estratte con seme fisso), con risposta breve generata dal modello. La risposta è corretta se, dopo la normalizzazione SQuAD, coincide con uno degli alias di riferimento | AUROC errata contro corretta, per stimatore e per modello |
| **M2** | le 400 domande SQuAD 2.0 di verifica del test 4, con e senza risposta. Queste domande **non entrano né nell'addestramento né nella scelta degli iperparametri**: addestramento e selezione usano solo SQuAD 2.0 train, i cui articoli sono disgiunti da quelli del dev | AUROC senza risposta contro con risposta |
| **M3** | le stesse 400 domande SQuAD 2.0 | AUROC senza risposta contro con risposta |
| **M4**, ogni sonda separatamente | **prima scelta:** il test LongFact annotato degli autori per Llama 3.1 8B (`obalcells/longfact-annotations`, sottoinsieme `Meta-Llama-3.1-8B-Instruct`, split test, 989 testi), valutato con il codice di valutazione degli autori (`probe/evaluate.py`, AUC span-max per entità). **Riserva**, solo se il dataset o il codice non girano: le 400 domande TriviaQA di M1, con il massimo della sonda sulla risposta di Llama | AUC span-max (oppure AUROC errata contro corretta nella riserva) |

Descrittivo per M1, distinto da HM0: sulle 400 domande SQuAD il modello risponde con il contesto, e si calcola l'AUROC di ogni stimatore tra le domande senza risposta e quelle con risposta. Questa misura non decide la valutabilità.

## 4. Misure
Per ogni metodo (e per ogni stimatore di M1, ogni sonda di M4), modello e formato:
- **W(C > B)**: la quota di coppie in cui il punteggio di incertezza o di non risposta è più alto su C che su B (i pareggi valgono 0.5). Si media per storia e si calcola l'IC al 95% su 2000 ricampionamenti delle storie (seme 20261108), come nel Test U.
- **AUROC C contro B** e **AUROC C contro A ∪ B**, descrittive.
- **ΔW rispetto a p(UNKNOWN)**: si appaia per `pair_key` sulle coppie comuni ai due punteggi e si ricampiona la stessa storia nei due bracci, come nel Test U2. Il riferimento è il p(UNKNOWN) ricalcolato nello stesso ambiente del metodo (§6).
- **Controllo positivo**: la misura di §3.1.

## 5. Ipotesi preregistrate
- **HM0 (validità del metodo):** la misura del controllo positivo è ≥ 0.70. Se un metodo, uno stimatore o una sonda non passa HM0 su un modello, per quel modello è NON VALUTABILE: il suo fallimento sulle coppie B/C non si può distinguere da un errore di implementazione. W si riporta comunque, come descrittivo.
- **HM1 (il metodo riconosce l'indeterminatezza):** per ogni metodo valutabile, su P−S, W(C > B) > 0.5. È CONFERMATA se il limite inferiore è > 0.5 **e** W ≥ 0.60; NON CONFERMATA se il limite superiore è ≤ 0.5; altrimenti NON CONCLUSIVA.
- **HM2 (il metodo fa meglio di p(UNKNOWN)):** ΔW = W(metodo) − W(p(UNKNOWN)) su P−S. È CONFERMATA se il limite inferiore è > 0 **e** ΔW ≥ 0.05; NON CONFERMATA se il limite superiore è ≤ 0; altrimenti NON CONCLUSIVA.
- **Limite di HM2 per Qwen.** Nel Test U2, W di p(UNKNOWN) su P−S per Qwen vale 0.975, quindi il guadagno massimo possibile è circa +0.025, sotto la soglia di +0.05. HM2 in pratica non si può confermare per Qwen.
  - La soglia resta fissa.
  - ΔW e il suo IC si riportano comunque.
  - Il limite si segnala nel resoconto.
  - Di conseguenza, per scrivere «fa meglio di p(UNKNOWN)» con la regola dei 3 su 4 devono confermare **tutti e tre** gli altri modelli.
- Su S−S le stesse misure sono descrittive.

**Lettura per la libreria (almeno 3 conferme su 4 modelli valutabili):**
- «Il metodo X riconosce l'indeterminatezza logica in prosa» si scrive solo se HM1 è confermata in almeno 3 modelli. Per M1 la regola vale stimatore per stimatore.
- «Il metodo X fa meglio di p(UNKNOWN)» si scrive solo se HM2 è confermata in almeno 3 modelli, tenendo conto del limite di Qwen.
- M3 è un solo giudice, quindi dà un W per formato e la regola dei 3 su 4 non si applica. Si riporta il suo esito unico su HM0 e HM1. Il suo ΔW si calcola rispetto al p(UNKNOWN) di ciascuno dei 4 modelli ed è descrittivo, perché il giudice è un modello diverso.
- M4 vale solo per Llama. M4-lin e M4-LoRA si riportano separatamente come risultati su un solo modello, senza generalizzare.
- Un metodo che passa HM0 ma non HM1 si descrive così: «funziona sul suo dominio ma non riconosce l'indeterminatezza logica delle coppie B/C».

## 6. Ambienti di esecuzione
I vincoli reali delle librerie, controllati con `uv pip compile` sui loro file di dipendenze:
- **SIRIN** fissa transformers < 5.4 e numpy 1.26.4. Con Python 3.12 si risolve a transformers 4.56.2, torch 2.9.0 e peft 0.17.1. Il pacchetto `ripserplusplus` serve solo al processore MTopDiv, che non usiamo, e il suo import è protetto.
- **LM-Polygraph 0.7.0** chiede transformers ≥ 4.50, senza limite superiore. Con Python 3.12 si risolve a transformers 5.22.2, torch 2.15.0 e numpy 2.5.4.
- **Il codice di Obeso et al.** chiede Python ≥ 3.10 e < 3.12, e ha un `uv.lock` che fissa torch 2.3.0, transformers 4.50.3, peft 0.17.1 e numpy 2.2.6.

(Nella v1 e nella revisione era indicato «transformers < 4.48». Non corrisponde a nessuna delle tre librerie, ed è corretto qui.)

Le versioni non sono compatibili fra loro, quindi si usano **tre ambienti `uv` separati** in Colab. Ogni metodo gira in uno script lanciato con il Python del suo ambiente:

| Ambiente | Python | Contenuto | Metodi |
|---|---|---|---|
| `env_m1` | 3.12 | lm-polygraph 0.7.0, con le versioni risolte fissate in un file di vincoli scritto nel notebook | M1 e p(UNKNOWN) dei 4 modelli |
| `env_sirin` | 3.12 | SIRIN al commit `ef3bed1`, con le versioni risolte fissate | M3 (notebook A), M2 e p(UNKNOWN) dei 4 modelli (notebook B) |
| `env_obeso` | 3.11 | `hallucination_probes` al commit `295450e`, installato con `uv sync --frozen` dal lock degli autori | M4 e p(UNKNOWN) di Llama |

- **p(UNKNOWN) si ricalcola in ogni ambiente in cui girano i modelli**: in `env_m1` per i 4 modelli, in `env_obeso` per Llama e in `env_sirin` per i 4 modelli del notebook B. Ogni ΔW confronta due punteggi della stessa run.
- In ogni ambiente si confronta anche p(UNKNOWN) di P−S con il Test U2, come controllo descrittivo: scarto massimo, W e quota di risposte uguali. Con versioni diverse di transformers e torch sono possibili piccole differenze numeriche. Una differenza di W oltre 0.01 si segnala nel resoconto, ma non decide nulla.
- Ogni ambiente salva su Drive la lista completa dei pacchetti installati (`uv pip freeze`).
- Se l'installazione o l'esecuzione di una libreria fallisce, il metodo si riporta come NON ESEGUITO, con il log dell'errore. Non si sostituisce con una reimplementazione senza una nuova approvazione.

## 7. Struttura e tempi
Due notebook, per tenere separato il lavoro con addestramento:
- **Notebook A (senza addestramento): M1, M3, M4 e il riferimento.** Stima di circa 3–4 ore in tutto: M1 è la parte più lunga, per i 5 campioni di Semantic Entropy e il modello NLI. I risultati si salvano su Drive modello per modello e metodo per metodo, così una run interrotta riprende da dove si era fermata.
- **Notebook B (con addestramento su SQuAD 2.0): M2.** Stima di circa 1–2 ore. Si scrive dopo il notebook A, con la nota di configurazione di §2.1.

**Prova obbligatoria.** In ogni notebook, prima della run completa, ogni metodo gira sul proprio controllo positivo (in forma ridotta) e su poche storie. La prova si fa con Qwen per M1, con il giudice per M3 e con Llama per M4. La prova serve a scoprire subito i problemi di installazione e di formato (per esempio lo schema del dataset LongFact), e a verificare che il controllo positivo dia valori plausibili. I numeri della prova non entrano negli esiti.

## 8. Cosa non fa questo test
- Non adatta nessun metodo alle storie e non sceglie soglie sulle coppie B/C.
- Non prova il giudice SIRIN addestrato con LoRA (rinviato alla v1.1).
- Non separa notazione, istruzione e domanda tra P−S e S−S. Restano template interi, come nel Test U2.

## Fonti
- SIRIN: [articolo, arXiv 2608.00033](https://arxiv.org/pdf/2608.00033), [codice](https://github.com/sb-ai-lab/SIRIN) (Apache 2.0), commit `ef3bed143890dbee56b34755f8c27a218aef0aa2` (17 luglio 2026). Answerability su SQuAD 2.0: giudice LoRA Qwen3-4B AUROC 95.7, giudice zero-shot Qwen3-4B 92.4, migliore sonda (attention pooling) 87.9. Non sono rilasciati pesi addestrati.
- LM-Polygraph: [PyPI, versione 0.7.0](https://pypi.org/project/lm-polygraph/), [benchmark, arXiv 2406.15627](https://arxiv.org/pdf/2406.15627).
- Obeso et al. 2025, [Real-Time Detection of Hallucinated Entities in Long-Form Generation, arXiv 2509.03531](https://arxiv.org/html/2509.03531v1). Codice: [hallucination_probes](https://github.com/obalcells/hallucination_probes) (Apache 2.0), commit `295450e2c24db7ecac1229e21783d2ebd08f9582`. Pesi: `obalcells/hallucination-probes`, revisione `db581ce2166d9faf611ad1f45955dcea94c96f85`, cartelle `llama3_1_8b_linear` e `llama3_1_8b_lora_lambda_kl_0_05` (`probe_config.json` con lo strato 30, `probe_head.bin` lineare con sigmoide). Dati annotati: `obalcells/longfact-annotations` (sottoinsieme Meta-Llama-3.1-8B-Instruct: test 989, train 510, validation 64).