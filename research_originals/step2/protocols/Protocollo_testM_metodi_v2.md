# Test M (metodi esistenti sulle coppie B/C): protocollo v2

Data: 10 novembre 2026. Stato: **pronto per l'implementazione e la prova tecnica**. Le scelte di §8 della v1 sono state approvate da Simona il 9 novembre, e le quattro regole del 10 novembre sono in §5 e §6. Dopo la revisione del notebook A (10 novembre): HM2 conta le coppie comuni (§5), la ripresa è legata a un'impronta e Llama ha una revisione fissata anche in HM0 (§6.1). Nessun dato è stato raccolto. La raccolta completa parte solo dopo che i tre ambienti si sono installati e ogni metodo ha girato sul proprio controllo positivo.
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
| **M4. Sonde pubblicate con pesi rilasciati** | sonde di Obeso et al. 2025 per entità allucinate: **M4-lin** (lineare) e **M4-LoRA** (LoRA-KL, cartella `llama3_1_8b_lora_lambda_kl_0_05`; il `training_config.json` della cartella indica λ_KL = 0.5). Punteggio per token, massimo sulla risposta | codice `obalcells/hallucination_probes` commit `295450e`; pesi `obalcells/hallucination-probes` revisione `db581ce` | già addestrate dagli autori | solo Llama-3.1-8B-Instruct |
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
- **Margine di HM2 sui dati confrontati (regola del 10 novembre).** ΔW si calcola solo sulle coppie valide sia per il metodo sia per il riferimento, con le stesse `pair_key` e nello stesso ambiente. Su quelle coppie si riporta anche il margine massimo possibile, 1 − W(riferimento). La soglia di +0.05 resta fissa anche quando il margine è più piccolo.
- **Copertura minima (regola del 10 novembre).** Un esito di HM1 o HM2 si assegna solo se nel formato principale restano almeno **760 coppie valide su 800** (95%). Per HM1 contano le coppie valide del metodo. Per HM2 contano le coppie valide sia per il metodo sia per il riferimento, cioè quelle su cui si calcola ΔW. Sotto questa soglia W e ΔW si riportano come descrittivi. Gli scarti si riportano sempre, per famiglia (AND, OR, IMPLIES) e per motivo. I motivi sono, per B e per C, «mancante» (il metodo non ha dato un punteggio per quella riga) e «non finito» (punteggio None, NaN o infinito).
- Su S−S le stesse misure sono descrittive.

**Lettura per la libreria (almeno 3 conferme su 4 modelli valutabili):**
- «Il metodo X riconosce l'indeterminatezza logica in prosa» si scrive solo se HM1 è confermata in almeno 3 modelli. Per M1 la regola vale stimatore per stimatore.
- «Il metodo X fa meglio di p(UNKNOWN)» si scrive solo se HM2 è confermata in almeno 3 modelli, tenendo conto del limite di Qwen.
- M3 è un solo giudice, quindi dà un W per formato e la regola dei 3 su 4 non si applica. Si riporta il suo esito unico su HM0 e HM1. Il suo ΔW si calcola rispetto al p(UNKNOWN) di ciascuno dei 4 modelli, ricalcolato in `env_sirin`, ed è descrittivo, perché il giudice è un modello diverso.
- M4 vale solo per Llama. M4-lin e M4-LoRA si riportano separatamente come risultati su un solo modello, senza generalizzare.
- **Formulazioni per gli esiti di HM1 (regola del 10 novembre).**
  - Se un metodo passa HM0 e HM1 è NON CONFERMATA: «funziona sul suo dominio ma non riconosce l'indeterminatezza logica delle coppie B/C».
  - Se un metodo passa HM0 e HM1 è NON CONCLUSIVA: «non ha superato il criterio HM1 in questo test».
  - Se un metodo non passa HM0, è NON VALUTABILE e il suo W si riporta come descrittivo.

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
| `env_sirin` | 3.12 | SIRIN al commit `ef3bed1`, con le versioni risolte fissate | M3 e p(UNKNOWN) dei 4 modelli (notebook A); M2 (notebook B) |
| `env_obeso` | 3.11 | `hallucination_probes` al commit `295450e`, installato con `uv sync --frozen` dal lock degli autori | M4 e p(UNKNOWN) di Llama |

- **p(UNKNOWN) si ricalcola in ogni ambiente in cui girano i modelli**: in `env_m1` per i 4 modelli e in `env_obeso` per Llama. Ogni ΔW confronta due punteggi della stessa run.
- **I riferimenti di `env_sirin` si calcolano nel notebook A (regola del 10 novembre).** I quattro p(UNKNOWN) di `env_sirin` servono ai ΔW di M3, quindi si calcolano già nel notebook A. Il notebook B li riusa se ambiente e configurazione coincidono: stessa lista di pacchetti, stesso commit, stessi prompt e stesse revisioni dei modelli, verificati con un'impronta. Se qualcosa cambia, B li ricalcola. Il giudice M3 dà un solo W per formato. I suoi quattro ΔW, uno per ogni riferimento di `env_sirin`, sono descrittivi.
- In ogni ambiente si confronta anche p(UNKNOWN) di P−S con il Test U2, come controllo descrittivo: scarto massimo, W e quota di risposte uguali. Lo scarto massimo si misura sui 24 valori di allineamento. La quota di risposte uguali si misura su tutti i prompt P−S eseguiti, confrontando la prima parola analizzata (YES, NO, UNKNOWN o altro) con quella del Test U2. Con versioni diverse di transformers e torch sono possibili piccole differenze numeriche. Una differenza di W oltre 0.01 si segnala nel resoconto, ma non decide nulla.
- Ogni ambiente salva su Drive la lista completa dei pacchetti installati (`uv pip freeze`).
- Se l'installazione o l'esecuzione di una libreria fallisce, il metodo si riporta come NON ESEGUITO, con il log dell'errore. Non si sostituisce con una reimplementazione senza una nuova approvazione.

### 6.1 Dettagli di implementazione (fissati scrivendo il notebook A, prima di qualsiasi dato)
Queste scelte non cambiano i metodi: riguardano la configurazione, i dati di controllo e l'installazione.

**M1 (LM-Polygraph).**
- Il modello si avvolge in `WhiteboxModel(..., instruct=True)`, che applica il chat template come il Test U2. Per Qwen il template si chiama con `enable_thinking=False`.
- Prima della run il notebook verifica, prompt per prompt, che LM-Polygraph veda gli stessi token del riferimento. Se c'è anche una sola differenza, M1 non si esegue per quel modello.
- 5 campioni invece dei 10 di default della libreria. Si impostano con un builder, cioè il punto di estensione previsto dalla libreria per i calcolatori. Il passo greedy non salva attenzioni né stati interni, che a questi stimatori non servono.
- La libreria genera sempre almeno 2 token (`min_new_tokens=2`), sia in greedy sia nei campioni. Le sue misure di sequenza includono quindi un token dopo la parola di risposta. È il comportamento pubblicato e non si modifica. Nel resoconto si riporta quanto spesso la risposta greedy di LM-Polygraph coincide con quella del riferimento.
- **Batch.** Sulle coppie i batch contengono solo prompt della stessa lunghezza in token, quindi non c'è padding. Sui controlli positivi i batch sono da 16 con padding a sinistra, l'uso standard della libreria.

**M1, controllo TriviaQA.**
- Le domande sono 400, estratte da `mandarjoshi/trivia_qa` (rc.nocontext, validation) con il seme 20261110. L'istruzione è «Answer the following question with a short answer only, without explanation.», e la risposta ha al massimo 24 token.
- Una risposta è corretta se, dopo la normalizzazione SQuAD, contiene come sequenza di parole intere uno degli alias normalizzati. È il criterio usuale con i modelli chat, che raramente rispondono con il solo alias. Sostituisce la «coincidenza» indicata in §3.1.

**M3 (giudice SIRIN).**
- Si usano la classe `SequenceDecoderJudge` e l'adattatore `HfModelAdapter` di SIRIN, con Qwen3-4B alla revisione `1cfa9a7`.
- La configurazione è quella del preset di answerability: lo stesso `user_prompt`, `dialogue_format='{question}'` e il `system_prompt` di default della libreria. Quel system prompt è scritto per la rilevazione di allucinazioni; si lascia com'è, perché è quello che usa il preset.
- Due impostazioni sono necessarie per leggere un punteggio:
  - `num_classification_heads=2`, così la probabilità di «1» è normalizzata su {«0», «1»};
  - `max_new_tokens=1`, così si legge solo il primo token.
- I campioni si passano uno alla volta, perché il tokenizer dell'adattatore aggiunge il padding a destra e in un batch sposterebbe il primo token letto.
- **Modo senza ragionamento (§2.1).** Il giudice locale di SIRIN unisce il dialogo senza prompt di generazione e poi aggiunge solo `<|im_start|>assistant\n`. Con Qwen3 questo è il modo con ragionamento: il primo token atteso è `<think>`, e le probabilità delle cifre 0 e 1 non dicono nulla. Nella prova su GPU del 10 novembre il giudice dava circa 0.7 a tutte le domande SQuAD, con AUROC 0.35 su 40. Il prefisso dell'assistente si prende quindi dal chat template con `enable_thinking=False` (`<|im_start|>assistant\n<think>\n\n</think>\n\n`), come fa il preset di SIRIN per il giudice via API. Il manifest registra sia questo prefisso sia quello della libreria.
- SIRIN si importa dal repository clonato, tramite PYTHONPATH. Non si installano il progetto, né la copia di lm-polygraph inclusa nel repository, né i due pacchetti git del processore MTopDiv (`mtopdiv`, `ripserplusplus`). Il giudice non li usa, e il loro import in SIRIN è protetto. Tutte le altre dipendenze si installano con le versioni risolte. Due vincoli si aggiungono alla risoluzione, e ciascuno cambia solo il proprio pacchetto:
  - `pyarrow<26` (si risolve a 25.0.1). La prova a secco ha mostrato che pyarrow 26.0.1, scelto dalla risoluzione automatica, richiede numpy 2 quando si importa, mentre SIRIN fissa numpy 1.26.4: senza il vincolo `datasets` non si importa.
  - `torchao==0.14.1`. La risoluzione sceglieva torchao 0.18.0, richiesto senza limiti da `unsloth-zoo`. Quella versione richiede torch ≥ 2.11, e nella prova su GPU del 10 novembre ha fatto fallire l'import di transformers con torch 2.9.0. La 0.14.1 è quella compilata per torch 2.9.0. Il giudice e il riferimento non usano torchao: transformers lo importa solo perché è installato.

**Esecuzione, ripresa ed esportazione.**
- Ogni lavoro (metodo × modello) scrive in una cartella che porta un'impronta. L'impronta copre il contenuto dei file di input, gli script, i pacchetti installati nell'ambiente, la configurazione e la versione del notebook. Se cambia uno di questi, il lavoro riparte in una cartella nuova e non riusa né il file finale né i checkpoint precedenti.
- **GPU.** Si usa una A100, come nel Test U2, e il notebook si ferma su un'altra GPU. Nella prova del 10 novembre una sessione su L4 ha dato p(UNKNOWN) diversi dal Test U2 fino a 0.06 sui 24 valori di allineamento, mentre le A100 da 40 e da 80 GB danno lo stesso valore del Test U2 (scarto 1e-16). La famiglia della GPU entra nell'impronta, quindi un lavoro non riusa mai uscite o checkpoint calcolati su un'altra GPU. Il rapporto elenca la GPU di ogni lavoro.
- **Pacchetti dell'ambiente effettivo.** L'impronta usa i pacchetti letti dall'ambiente installato (`uv pip freeze` sul suo Python), non l'elenco salvato su Drive. Se un ambiente già installato non coincide più con la sua installazione, si reinstalla da zero con le versioni fissate. Se coincide con l'installazione ma non con l'elenco su Drive, vale l'ambiente effettivo: l'elenco su Drive si conserva a parte e i lavori fatti con l'altro ambiente non si riusano. L'elenco su Drive si usa solo quando l'ambiente non è installato, cioè per riesportare in una sessione nuova. Anche l'impronta di ogni checkpoint copre il contenuto completo delle righe, prompt compresi.
- `stato.json` registra per ogni lavoro l'esito, l'impronta, la cartella e l'ambiente. La nuova impronta si registra prima del lancio, con esito «IN CORSO»: se il tentativo si interrompe o fallisce, `stato.json` non indica più il risultato precedente.
- L'analisi ricalcola l'impronta attesa di ogni lavoro con gli input, gli script, gli ambienti e la configurazione attuali. Legge un risultato solo se è ESEGUITO con quell'impronta. Un risultato ESEGUITO con un'impronta diversa resta fuori dall'analisi: il rapporto lo segnala e lo ZIP lo mette a parte, in `uscite_escluse/`.
- **Ambiente dei processi.** Ogni script gira con `MPLBACKEND=Agg`. Il kernel di Colab imposta il backend grafico inline, che negli ambienti separati non esiste: nella prova del 10 novembre matplotlib rifiutava quel valore all'import, e M1 e il codice di valutazione di M4 non partivano. Agg non disegna a schermo e non cambia nessun calcolo.
- **Versioni fissate cambiate.** Se le versioni fissate di un ambiente (o il commit con il lock degli autori) cambiano rispetto all'installazione, l'ambiente si reinstalla da zero.
- Lo ZIP si esporta sempre, anche se tutti i lavori falliscono o l'analisi va in errore. Contiene esiti, tabella, rapporto, `stato.json`, i log, gli elenchi dei pacchetti, i dati di input e le uscite di ogni lavoro (JSON dei metodi, configurazione, cartelle HM0 di M4), senza i checkpoint. I risultati si possono quindi ricalcolare dallo ZIP.

**M4 (sonde di Obeso et al.).**
- Le sonde si scaricano alla revisione `db581ce` e si caricano dal disco con `setup_probe` degli autori: prima la lineare, poi la LoRA, che modifica il modello.
- I dataset annotati si scaricano alle revisioni `949fd2f` (LongFact) e `620117a` (TriviaQA bilanciato degli autori) e si passano al codice di valutazione come cartelle locali. Si scaricano interi, con tutti i sottoinsiemi. Con una cartella locale, `datasets` 3.5 cerca i file del primo sottoinsieme elencato nel README anche quando se ne chiede un altro: nella prova su GPU, con il solo sottoinsieme di Llama 3.1 8B, `probe.evaluate` non trovava i dati. Dopo il download, il notebook verifica il caricamento nel Python di `env_obeso`.
- La riserva di HM0 diventa il test TriviaQA bilanciato degli autori per Llama 3.1 8B, valutato con lo stesso codice. Sostituisce le 400 domande TriviaQA di M1 indicate in §3.1.
- `probe.evaluate` carica Llama per nome, senza revisione. Per questo il notebook scarica prima Llama alla revisione fissata (`0e9e39f`) e passa a `probe.evaluate` la cartella locale di quella revisione. Il risultato di HM0 registra la revisione usata. Se non coincide con quella del protocollo, HM0 per quella sonda non vale come controllo positivo.
- **Memoria per HM0.** Prima di `probe.evaluate`, che carica un secondo Llama, il processo di M4 libera la GPU. Nella prova del 10 novembre il modello con LoRA restava in memoria, LongFact finiva in CUDA out of memory e HM0 ripiegava sulla riserva TriviaQA (0.925 lineare, 0.949 LoRA, su 40 testi). La valutazione usa il batch 4, il default degli autori. Solo in caso di out of memory si ripete con batch 1, che non cambia le metriche, e il batch usato si registra.
- Se `probe.evaluate` non gira per una sonda né su LongFact né sulla riserva, M4 è NON ESEGUITO con il log (§6): è un errore di esecuzione della libreria, non un controllo positivo fallito. Le uscite già calcolate restano in un file a parte (`M4_senza_HM0.json`), e al tentativo successivo si riusano i checkpoint.
- Le cartelle delle sonde contengono le metriche degli autori, che si riportano accanto al nostro HM0 come confronto descrittivo. Per la LoRA l'AUC span-max su LongFact test è 0.890, su TriviaQA test 0.968. Per la lineare la cartella riporta solo HealthBench (0.849). Il nome della cartella LoRA dice λ = 0.05, mentre la sua configurazione di addestramento dice 0.5: si usa la cartella così com'è, e nel resoconto si cita il valore della configurazione.

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
