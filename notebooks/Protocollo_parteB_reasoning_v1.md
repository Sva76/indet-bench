# Protocollo parte B: p(UNKNOWN) nei modelli reasoning (v1)

15 novembre 2026. **Approvato da Simona (15 nov, 14:11), con le 5 scelte raccomandate in §7**, prima di raccogliere qualsiasi dato della parte B. Note di attuazione (dettagli del notebook non scritti qui) in `Note_reasoning_v1.md`. Le revisioni dei modelli sono state lette dall'API di Hugging Face il 15 novembre e saranno ricontrollate dal notebook.

## 1. Domanda e statuto

**Domanda.** Se il modello ragiona prima di rispondere, p(UNKNOWN) separa ancora i casi C dai casi B sulle 800 coppie congelate in prosa (set PN)? E il ragionamento cambia la separazione rispetto allo stesso modello senza ragionamento?

**Statuto.** Come le parti precedenti, i risultati sono **esplorativi**: non sono una validazione indipendente del metodo. Un W più alto con il ragionamento non dimostra che il metodo funzioni meglio, e un W più basso non lo smentisce. Ogni anomalia va classificata nelle quattro categorie (comportamento del modello, problema tecnico, limite del protocollo, evidenza scientifica), dicendo se la categoria è sostenuta dai dati o resta aperta.

## 2. Il problema di misura

Nei modelli senza ragionamento p(UNKNOWN) è la probabilità del primo token della risposta. In un modello reasoning il primo token è l'inizio del ragionamento, quindi quella definizione non ha più senso. La risposta arriva dopo la chiusura del ragionamento (`</think>`), e dipende da quello che il modello ha scritto prima.

**Definizione proposta.** p(UNKNOWN) è la somma delle probabilità delle 6 varianti di UNKNOWN (stesse varianti e stessa funzione `token_label_ids` delle parti precedenti, senza rinormalizzare) **al primo token della risposta dopo `</think>`**. Il «primo token della risposta» è il primo token generato dopo `</think>` che non sia solo spazio o a capo. p(YES) e p(NO) si misurano nello stesso punto.

Conseguenza da dichiarare: la misura è **condizionata al ragionamento generato**. Con un campionamento diverso il ragionamento cambia, e quindi cambia anche p(UNKNOWN). Per questo il protocollo misura la ripetibilità (§5.4).

## 3. Modelli proposti

| Chiave | Modello | Revisione | Parametri | Licenza | Confronto | Ruolo |
|---|---|---|---|---|---|---|
| qwen3_8b_think | Qwen/Qwen3-8B, `enable_thinking=True` | b968826d9c46dd6066d109eabc6255188de91218 | 8B | Apache-2.0 | **stessi pesi** senza ragionamento | **principale** |
| qwen3_32b_think | Qwen/Qwen3-32B, `enable_thinking=True` | 9216db5781bf21249d130ec9da846c4624c16137 | 33B | Apache-2.0 | **stessi pesi** senza ragionamento (parte A: W 0.975) | secondario |
| phi4_reasoning | microsoft/Phi-4-reasoning | 1de18ec97600877ce63dbf60c73b998da99f0195 | 14.7B | MIT | Phi-4 (14 nov: W 0.944), stessa base ma addestramento diverso | descrittivo |
| r1_llama_8b (facoltativo) | deepseek-ai/DeepSeek-R1-Distill-Llama-8B | 6a6f4aa4197940add57724a7707d069478df56b1 | 8B | MIT; derivato da Llama-3.1-8B-Base, quindi vale anche la Llama 3.1 Community License | nessun confronto a modello fisso (la base non è l'Instruct del Test U2) | descrittivo |

- **Perché Qwen3 è principale.** È l'unico caso in cui ragionamento acceso e spento usano **gli stessi pesi**: la differenza misura il ragionamento e nient'altro. Qwen3-8B è anche il controllo positivo di tutte le parti precedenti.
- **Limite noto, prima dei dati.** Qwen3 senza ragionamento ha già W 0.975: c'è poco spazio per salire. Il confronto può mostrare bene un peggioramento, meno bene un miglioramento.
- **Phi-4-reasoning.** È Phi-4 addestrato in più per ragionare. Il confronto con Phi-4 è descrittivo, perché i pesi sono diversi. Il suo template **inserisce sempre un messaggio di sistema** di Microsoft, che chiede una sezione di ragionamento e una sezione «Solution». Lo usiamo così com'è, perché è il template del modello, e lo dichiariamo. **Rischio dichiarato:** la sezione «Solution» potrebbe non iniziare con YES/NO/UNKNOWN, e allora la regola sulla massa (§5.2) lo renderebbe NON MISURABILE.
- **R1-Distill-Llama-8B** è un'altra famiglia di ragionamento (distillata da DeepSeek-R1). Lo propongo solo come facoltativo: non ha un confronto pulito, e la licenza Llama 3.1 richiede le citazioni già previste per Llama.
- **Esclusi.** QwQ-32B e DeepSeek-R1-Distill-Qwen-32B (stessa famiglia Qwen, nessun confronto a pesi fissi in più); i modelli reasoning più grandi di 32B (non entrano in una A100 in bf16).

## 4. Generazione

| Voce | Proposta | Motivo |
|---|---|---|
| Prompt | gli stessi prompt congelati, solo il messaggio utente (più il sistema fisso del template per Phi-4-reasoning) | identità con le parti precedenti |
| Decodifica | **campionamento con i parametri degli autori**: Qwen3 temperatura 0.6, top-p 0.95, top-k 20, min-p 0; Phi-4-reasoning 0.8, 0.95, 50; R1 0.6, 0.95 | Qwen scrive esplicitamente di non usare la decodifica greedy in modalità ragionamento (degrada e può ripetere all'infinito); Phi-4-reasoning richiede il campionamento |
| Seme | fisso, 20261108, registrato insieme alla composizione dei batch | riproducibilità nella stessa sessione e con lo stesso ambiente |
| Budget di ragionamento | **4096 token** | le storie sono brevi; il budget completo raccomandato (32 768) renderebbe il completo troppo lungo |
| Ragionamento che non si chiude | il notebook aggiunge `\n</think>\n\n` e misura il token successivo; la riga è marcata `troncata` | la misura resta definita; il troncamento è registrato e analizzato a parte |
| Risposta dopo il ragionamento | fino a 16 token generati dopo `</think>`, letti con lo stesso `parse_label` | stessa lettura della risposta delle parti precedenti |
| Precisione | bfloat16 per tutti | come la parte A |
| Batch e attenzione | **batch 16 con padding a sinistra, attenzione sdpa; Qwen3-32B a batch 4** (con 16 sequenze da circa 4300 token cache e pesi superano gli 80 GB; dettaglio di attuazione, il batch è registrato nel manifest) | con batch 1 ed eager, migliaia di token per riga non stanno nei tempi di una sessione |
| Condizione senza ragionamento | per Qwen3-8B e 32B si rimisura **nella stessa pipeline** (stesso batch e stessa attenzione, `enable_thinking=False`, greedy, 8 token come il Test U2) | il confronto acceso/spento usa le stesse impostazioni tecniche; i valori si confrontano anche con il Test U2 e la parte A |
| Testi salvati | ragionamento e risposta completi di ogni riga | servono per controllare le anomalie; non entrano nelle misure |

## 5. Regole fissate prima dei dati

### 5.1 Controlli tecnici

1. Revisione, template ed etichette controllati come nella parte A. Il template non deve inserire la data.
2. **Controllo della pipeline a batch.** Con il ragionamento spento, la pipeline batch 16 + sdpa deve riprodurre i 24 valori archiviati di Qwen3-8B del Test U2. Tolleranza proposta: scarto massimo ≤ 0.01 e risposte uguali 24/24. È più larga della tolleranza 1e-3 della parte A, perché batch e attenzione diverse cambiano gli arrotondamenti. Se fallisce, il completo non parte.
3. Il controllo CPU dei 4 W del Test U2 resta obbligatorio prima del completo.

### 5.2 Misurabilità

- **Regola sulla massa (dalla v4):** se la massa mediana di YES+NO+UNKNOWN al primo token della risposta è < 0.5, il modello è **NON MISURABILE (motivo tecnico)**. Si controlla prima sulle 24 righe di prova e poi sull'insieme completo.
- **Troncamenti:** la coppia è «chiusa» se B e C hanno chiuso il ragionamento da soli entro il budget. Se le coppie chiuse sono almeno 760, l'analisi principale usa tutte le 800 coppie, e la sensibilità usa solo le chiuse. Se sono meno di 760, il risultato del modello è **solo descrittivo**, con la distribuzione dei troncamenti per famiglia, variante e posizione. È la stessa soglia di copertura delle parti precedenti.

### 5.3 Ipotesi e criteri

- **HR1 (per ogni modello):** stessa regola HU1/HI1. Con il ragionamento acceso W ≥ 0.60 e limite inferiore dell'IC95 > 0.5. Vale la soglia di competenza vincolante: accuratezza sui B ≥ 0.50, complessiva e per gold, calcolata sulla risposta dopo il ragionamento.
- **HR2 (Qwen3-8B principale, Qwen3-32B secondario):** ΔW = W acceso − W spento, appaiato per storia, IC95 bootstrap (2000 ricampionamenti delle storie, seme 20261108). Si riporta stima e IC. «Il ragionamento cambia W» solo se l'IC95 esclude 0. Non c'è una soglia di miglioramento, perché non è un test di superiorità.
- **Descrittivo:** per Phi-4-reasoning (contro Phi-4 del 14 novembre) e R1-Distill (nessun confronto). Si riportano anche:
  - le risposte cambiate fra acceso e spento sui B e sui C (UNKNOWN, YES, NO);
  - l'accuratezza sui B, per gold.

### 5.4 Baseline e ripetibilità

- **Baseline dalle stesse uscite (descrittive):**
  - entropia normalizzata;
  - meno p massima normalizzata;
  - risposta UNKNOWN 0/1;
  - p(UNKNOWN) normalizzata, con la nota del 14 novembre;
  - **lunghezza del ragionamento in token** (nuova): se il modello ragiona più a lungo sui C, la lunghezza da sola potrebbe separare C e B;
  - ragionamento troncato 0/1.
  La segnalazione «una baseline eguaglia o supera p(UNKNOWN)» usa le baseline indipendenti, compresa la lunghezza del ragionamento.
- **Ripetibilità:** sulle prime 20 storie (80 coppie) si ripete l'inferenza con due semi in più. Si riportano il W per seme e la quota di risposte uguali. È descrittiva, ma dice quanto il risultato dipende dal campionamento.

### 5.5 Che cosa non si misura

Non si misura p(UNKNOWN) durante il ragionamento. Non c'è una definizione unica del punto in cui misurare, e sceglierla dopo aver visto i testi sarebbe una scelta fatta sui dati. I testi restano salvati: un'analisi del ragionamento sarebbe un test separato, con un protocollo proprio.

## 6. Prova e completo

- **Prova:** 10 storie (40 coppie, 80 righe) per Qwen3-8B con ragionamento acceso e spento. Misura i tempi reali, la lunghezza media del ragionamento, la quota di troncamenti e il controllo della pipeline (§5.1). Dopo la prova stimo i tempi del completo con i numeri misurati.
- **Tempi stimati, non misurati:** se il ragionamento medio è di circa 1000 token:
  - Qwen3-8B: 1–2 ore;
  - Phi-4-reasoning: 2–3 ore;
  - Qwen3-32B: 4–6 ore.
  Si aggiungono la condizione spenta e la ripetibilità. Con troncamenti frequenti i tempi crescono.
- **Ambiente:** A100-SXM4-80GB (Qwen3-32B in bf16 la richiede), HF_TOKEN e GH_TOKEN nei Secrets, uscite su MyDrive con ripresa dai checkpoint, come nella parte A.

## 7. Decisioni di Simona (15 nov, 14:11: tutte e 5 come raccomandate)

1. **Modelli:** consiglio Qwen3-8B (principale), Qwen3-32B e Phi-4-reasoning. R1-Distill-Llama-8B è facoltativo.
2. **Decodifica:** consiglio il campionamento con i parametri degli autori, più la ripetibilità su 20 storie. L'alternativa greedy è deterministica, ma va contro le istruzioni di Qwen e Microsoft.
3. **Budget:** consiglio 4096 token, con chiusura forzata registrata.
4. **Pipeline:** consiglio batch 16 + sdpa, con il controllo a tolleranza 0.01 e la condizione spenta rimisurata nella stessa pipeline.
5. **Phi-4-reasoning:** se la regola sulla massa lo dichiara NON MISURABILE perché la «Solution» non inizia con un'etichetta, il risultato resta NON MISURABILE. Consiglio di non definire ora una misura alternativa, per non costruirne una apposta per un modello.
