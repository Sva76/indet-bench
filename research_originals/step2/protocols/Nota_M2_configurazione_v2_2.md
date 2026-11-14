# Test M, nota di configurazione di M2 e analisi per famiglia (v2.2)

Data: 11 novembre 2026. Aggiorna `Protocollo_testM_metodi_v2.md` (§2.1 e §5) per il notebook B. Sostituisce la v2.1 (approvata da Simona l'11 novembre), che resta valida per tutto ciò che qui non cambia.
Stato: **v2.2 approvata da Simona l'11 novembre**, ruoli compresi. Rispetto alla v2.1 aggiunge la variante **M2-senzaℓ2** (§2.10): variante definita dopo la diagnostica SQuAD e prima di calcolare i suoi punteggi sulle coppie B/C e sul controllo HM0 (Appendice B). Corregge inoltre due etichette del rapporto dell'ablation (Appendice B). Il notebook che la applica è M-B-notebook-4. Le modifiche sono elencate in fondo. I valori della nota non cambiano dopo aver visto i risultati.

Fonti controllate: l'articolo di SIRIN (arXiv 2608.00033v1, Tabella 3 e Appendici A e C) e il codice al commit `ef3bed1` (`sirin/detection/probing`, `sirin/classification/linear.py`, `sirin/detection/probing/training/trainers.py`, `sirin/inference/adapters/hf_adapter.py`, `sirin/configs`, `docs/reference`).

## 1. Cosa fissa l'articolo e cosa no

| Elemento | Articolo | Codice `ef3bed1` |
|---|---|---|
| Metodo | «Attpool probe»: stati nascosti dello strato centrale, con attention pooling sui token. AUROC 87.9 su SQuAD 2.0 | `SequenceLinearProbingDetector`: una query appresa per strato (`self.q`), softmax sui token, poi uno strato lineare |
| Modello | Qwen3-4B | qualsiasi modello HF |
| Strato | «middle layer», senza indice | `layers` in `hidden_states` (0 = embedding) |
| Ingresso | contesto e domanda, senza risposta | `_inspection_prompt`: `Context:\n…\n\nQuestion:\n…`, turno assistente vuoto |
| Lato dei token | non detto | la guida consiglia `LEFT` per l'answerability (token prima della risposta) |
| Lunghezza | non detta | `ProbingDetectorConfig.max_length` 128: limita gli stati passati alla sonda, dopo il forward. Il localizzatore del confine della risposta tokenizza il testo intero, senza troncamento (`hf_adapter.py`, righe 840–862) |
| Iperparametri | non detti | `train_args/default.yaml`: 5 epoche, lr 1e-3, batch 8, BCE, Adam con `weight_decay` 0 |
| Regolarizzazione | ℓ2 per i probe, senza valore | **termine ℓ2 fisso nel trainer** (`sirin/detection/probing/training/trainers.py`, righe 573–581): alla loss si aggiunge sempre Σw² / (2 × batch) su tutti i parametri tranne i bias, query dell'attention pooling compresa. Con batch 8 il coefficiente è 1/16. Non si configura ed è indipendente da `weight_decay` |
| Numero di esempi e divisione | non detti («annotated split») | validazione solo se si passa uno split `validation`. `val_size` non è usato |
| Ordine degli esempi | non detto | `shuffle_train=False` (default): l'ordine di addestramento è quello dei dati |
| Arresto anticipato | non detto | se la loss cambia meno di 1e-4 da un'epoca all'altra |
| Scelta dell'epoca | non detta | non funziona così com'è: vedi §2.7 |
| Soglia | «scelta sul training per massimizzare F1» | non entra in W né in AUROC |

## 2. Configurazione di M2

**2.1 Sonda.**
- `SequenceLinearProbingDetector`, `attention_pooling=[True]`, un solo strato, una testa binaria (`num_classification_heads=1`), `use_contrastive=False`.
- Compressione e scalatura: i default della libreria (`CompressionConfig`: metodo NONE, scalatura STANDARD).
- Etichetta 1 = «senza risposta». Il punteggio di M2 è la probabilità di «senza risposta»: più alto vuol dire più incerto, ed entra così in W.

**2.2 Strato centrale, fisso per modello.** L'indice è `num_hidden_layers // 2` in `hidden_states`.

| Modello | strati | strato usato |
|---|---|---|
| Qwen3-8B | 36 | 18 |
| Mistral-Nemo-Instruct-2407 | 40 | 20 |
| OLMo-2-1124-7B-Instruct | 32 | 16 |
| Llama-3.1-8B-Instruct | 32 | 16 |

Il notebook legge `num_hidden_layers` dalla configurazione del modello alla revisione fissata del protocollo, e si ferma se non coincide con la tabella.

**2.3 Estrazione degli stati.**
- `HiddensProcessor` con `side=LEFT`, `pooling_type='none'` (il pooling lo fa la sonda) e `locate_answer_start=True`.
- Template di chat attivo (`use_chat_template=True`, default), bf16, `attn_implementation='sdpa'` (bastano gli stati nascosti).
- `truncation=False` nel processore: il forward vede sempre il prompt intero.
- Cache delle feature disattivata (`cache_features=False`), per non riusare feature di una configurazione precedente (`pitfalls.md`).
- **Decodifica senza pulizia degli spazi** (aggiunta dopo la prova 1, approvata da Simona l'11 novembre). Il localizzatore di SIRIN (`HfTokenLocator.locate`) decodifica i token del prompt e li ritokenizza per avere gli offset. Se il tokenizer ha `clean_up_tokenization_spaces=True`, la decodifica toglie gli spazi prima di segni come «, . ? ! 's n't», la ritokenizzazione dà meno token e il localizzatore si ferma («200 token ids but 198 offsets»). Si imposta `clean_up_tokenization_spaces=False` sull'istanza del tokenizer dell'adattatore. La pulizia agisce solo sulla decodifica: tokenizzazione, prompt e stati non cambiano. Il valore originale di ogni tokenizer si registra.

**2.4 Lunghezza: prompt entro 512 token, accorciando a monte il solo contesto.**
- **Regola (Simona, 10 novembre).** Le parole sono le sequenze separate da spazi bianchi. Se il prompt completo, turno vuoto dell'assistente compreso, supera i 512 token con almeno uno dei 4 tokenizer, si toglie **una parola alla volta dalla fine del contesto** finché sta entro 512 token con tutti e 4. Il testo è così identico per i 4 modelli. Domanda, istruzione e template non si toccano. Il contesto accorciato è sempre un prefisso dell'originale, quindi gli inizi degli span annotati restano validi.
- **Sonda.** `ProbingDetectorConfig(max_length=512)`.
- **Controlli del confine,** con ciascuno dei 4 tokenizer, su addestramento, validazione, verifica e coppie:
  - il prompt completo ha al massimo 512 token;
  - la resa completa comincia con quella del solo turno utente, quindi la domanda compare intera in fondo al turno utente;
  - il localizzatore di SIRIN mette il confine dell'assistente esattamente dopo il turno utente;
  - nel lavoro di ogni modello, gli indici LEFT restituiti dalla libreria per ogni campione sono esattamente 0…n−1, con n il numero di token del turno utente: nessun troncamento a livello di feature.
- **Span annotati.** Uno span resta se finisce entro il contesto accorciato.
  - In addestramento e validazione, gli esempi con risposta che li perdono tutti si tolgono dal bacino prima del campionamento (§2.6), perché la loro etichetta non sarebbe più vera.
  - Sulle 400 domande di verifica (HM0), gli esempi con risposta che perdono tutti gli span si escludono da HM0.
  - Si riportano sempre i conteggi: esempi accorciati per insieme, esempi con risposta senza span residui, esclusi. Ogni esempio accorciato è registrato in `M2_accorciati.json`.
- **Coppie B/C.** I prompt (circa 100–220 token) non vengono mai accorciati. Il notebook lo verifica.
- **Esempi scartati dalla libreria.** `ProbingPipeline._preprocess_dataset` toglie in silenzio gli esempi con feature NaN o senza token localizzati. Il notebook controlla che il numero di esempi resti quello atteso e, se no, si ferma.

**2.5 Testo d'ingresso.** È lo stesso per SQuAD e per le coppie, ed è quello di M3: `Context:\n{contesto}\n\nQuestion:\n{domanda}` nel turno utente, con turno assistente vuoto e nessun prompt di sistema. Per le coppie, contesto e domanda sono quelli di §3 del protocollo (regola con i fatti; «Is approval given?» in P−S, «Is approval granted?» in S−S).

**2.6 Dati.**
- **Addestramento:** 2000 domande di SQuAD 2.0 train, 1000 con risposta e 1000 senza.
- **Validazione:** 400 domande di SQuAD 2.0 train (200 e 200), da articoli diversi da quelli dell'addestramento, passate come split `validation`.
- **Campionamento:**
  - dal dataset alla revisione fissata nel notebook;
  - per articolo, con seme 20261108: gli articoli rimasti dopo §2.4 si mescolano e il primo 20% va alla validazione;
  - dopo l'esclusione di §2.4;
  - uguale per i 4 modelli;
  - **sottoinsiemi annidati:** 200 + 40 della prova, 1000 + 200 della riserva e 2000 + 400 della selezione piena sono i primi esempi per classe dello stesso campione;
  - **ordine di addestramento fissato** con il seme 20261108 (la libreria non rimescola, §1).
- **ID fissati.** La prova estrae i due campioni e registra l'elenco degli ID con il suo sha256. Prima del completo l'hash entra come costante nel notebook e in appendice a questa nota. Il completo si ferma se l'elenco estratto ha un hash diverso.
- **HM0:** le 400 domande di verifica del test 4 (dev) non entrano né nell'addestramento né nella validazione (§3.1 del protocollo). Il notebook le ritrova per `sq_id` alla revisione fissata e controlla che contesto, domanda e classe coincidano.
- **Riserva per la memoria.**
  - La riserva (1000 + 200, per tutti e 4 i modelli) si decide **solo sul picco di RAM**.
  - **Misura (prova).** Su Qwen e su Mistral (il modello con stati più grandi, 5120 dimensioni), a due dimensioni: 200 + 40 e 400 + 80 esempi. Ogni misura percorre la catena di SIRIN fino a train e validazione preparati e tenuti in memoria insieme, poi si ferma **prima dell'addestramento**: non addestra la sonda e non produce metriche.
  - **Proiezione.** Per ogni modello si proietta la sola crescita fra le due dimensioni, fino a 2400 e a 1200 esempi, e si usa la proiezione più alta fra i due modelli. Si aggiunge la RAM già usata nella sessione e si confronta con l'85% della RAM della sessione: piena se entra la selezione piena, riserva se entra solo la riserva, altrimenti STOP. Con STOP il completo non parte e la scelta torna a Simona.
  - **Legame con le misure.** La decisione si registra prima di leggere qualsiasi metrica e prima della catena su Qwen, insieme alle impronte e allo sha256 dei file di misura e alle condizioni in cui è stata presa: versione del notebook, commit di SIRIN, pacchetti di `env_sirin`, famiglia della GPU, script, revisioni dei modelli, strati, dimensioni, soglia e sha256 degli ID.
  - **Completo.** La decisione della prova vale solo se le misure sono ancora quelle registrate (stato della prova, impronte, file invariati, proiezioni ricalcolate uguali) e le condizioni coincidono. Poi si ricontrolla il budget con la RAM della sessione del completo e vale la decisione più prudente fra le due. Se una ripresa in un'altra sessione cambiasse la decisione con lavori M2 già eseguiti, il completo si ferma.
  - Le stime di memoria fatte leggendo il codice (circa 130 GB per Mistral con 2000 + 400, circa 65–70 GB con la riserva, contro un limite di circa 70 GB) sono ipotesi: decide solo la misura.
  - Lunghezza e strato non cambiano.

**2.7 Addestramento e scelta dell'epoca.**
- **Iperparametri:** `train_args/default.yaml` della libreria: al massimo 5 epoche (con l'arresto anticipato qui sotto), lr 1e-3, Adam con `weight_decay` 0, batch 8, BCE, validazione a ogni epoca (`validation_interval=1`). Seme della libreria 42.
- **Regolarizzazione ℓ2 (corretta nella v2.1).** La v2 diceva «weight decay 0, nonostante la menzione di ℓ2 nell'articolo», come se la sonda non avesse regolarizzazione. Non è così. Il trainer di SIRIN (`BinaryHiddenStatesClassifierTrainer.train_epoch`, `sirin/detection/probing/training/trainers.py` righe 573–581) aggiunge sempre alla loss il termine Σw² / (2 × batch), su tutti i parametri tranne i bias e compresa la query dell'attention pooling. Con batch 8 il coefficiente è 1/16, anche con `weight_decay` 0 (il batch del DataLoader di addestramento è `train_batch_size` = 8, `pipeline.py` riga 318; con 2000 esempi tutti i batch sono pieni). Il termine è fisso, non si configura, e con ogni probabilità è la regolarizzazione ℓ2 di cui parla l'articolo. M2 lo usa così com'è; la variante M2-senzaℓ2 (§2.10) lo toglie. L'AUROC pubblicata (0.879, con Qwen3-4B) resta un riferimento descrittivo, perché modello e dati sono diversi.
- **Arresto anticipato e ordine.** Si tengono quelli della libreria (arresto se la loss cambia meno di 1e-4 fra due epoche; nessun rimescolamento). L'ordine degli esempi è fissato dal campionamento (§2.6). Entrambi si registrano nel JSON di ogni modello.
- **Problema del codice a `ef3bed1`.** La scelta dell'epoca migliore non funziona così com'è:
  1. con `metrics: null` l'F1 di validazione non viene calcolato, e la metrica bersaglio vale sempre 0;
  2. `save()` non restituisce nulla, quindi il trainer non ricarica mai l'epoca migliore e resta l'ultima;
  3. il file salvato da `_save_model` contiene lo strato lineare ma non la query appresa dell'attention pooling (`self.q`). Ricaricato, il modello avrebbe una query casuale.
- **Correzione nel notebook B, senza cambiare il metodo:**
  - si passa esplicitamente `metrics=[F1]` e `target_metric='f1'`: F1 della classe 1 sulla validazione alla soglia 0.5 della libreria, calcolato in `evaluate` (modalità eval, senza gradiente);
  - si sostituiscono `save` e `load` della sola istanza del detector: `save()` restituisce il percorso e salva lo `state_dict` completo di `LinearClassifier`, query comprese, con lo scaler. A ogni nuova epoca migliore (F1 strettamente più alto; a parità resta la prima) si salva, e alla fine il trainer ricarica l'epoca salvata;
  - il notebook verifica che l'epoca ricaricata sia la prima con l'F1 massimo;
  - si salva su Drive lo `state_dict` completo dell'epoca scelta, con l'epoca e l'F1 di ogni epoca;
  - **controllo di ricaricamento:** si costruisce un `LinearClassifier` nuovo, si carica lo `state_dict` salvato e si ricalcolano, sulle stesse feature, i punteggi di validazione, verifica e coppie B/C. Devono coincidere con quelli del modello in memoria (scarto massimo ≤ 1e-6, riportato). Altrimenti M2 è NON ESEGUITO per quel modello, con il log.

**2.8 Riferimento p(UNKNOWN).** HM2 confronta M2 con p(UNKNOWN) ricalcolato in `env_sirin`, sulle coppie comuni (§5). I riferimenti del notebook A (`REF_env_sirin_<modello>`) si riusano solo se coincidono tutti questi elementi:
- impronta dei pacchetti di `env_sirin`;
- famiglia della GPU;
- revisione del modello (sha);
- configurazione d'inferenza (script, dtype, attenzione, template di chat, decodifica greedy, numero di token);
- insieme dei `row_id` e sha256 dei prompt.

Il notebook ricostruisce l'impronta del lavoro del notebook A da script, input, pacchetti, configurazione e GPU, e la confronta con quella registrata. Se un controllo non passa, il riferimento si ricalcola nel notebook B. Quando un riferimento si riusa, lo ZIP del notebook B contiene il suo JSON con i punteggi grezzi e la sua configurazione (`riferimenti_A/`), così ΔW si ricalcola dal solo archivio B.

**2.9 Controllo positivo (HM0).** AUROC tra senza risposta e con risposta sulle domande di verifica rimaste dopo §2.4, soglia 0.70, per modello e per ciascuno dei due metodi (M2 e M2-senzaℓ2). HM0 si legge per ogni modello prima di interpretare le coppie B/C. L'esito si assegna se restano almeno 380 domande su 400; sotto, HM0 è NON VALUTABILE. Si riportano, per classe, le domande ammesse e quelle con punteggio finito, gli scarti per motivo e il numero di domande che entrano nell'AUROC. Il valore dell'articolo (87.9) si riporta accanto come confronto descrittivo.

**2.10 Variante M2-senzaℓ2 (aggiunta nella v2.2: variante definita dopo la diagnostica SQuAD e prima di calcolare i suoi punteggi sulle coppie B/C e sul controllo HM0).**
- **Origine.** La diagnostica dell'Appendice B (caso 3) e l'ablation della ℓ2: su Qwen, SQuAD 2000 + 400, l'AUROC di validazione passa da 0.575 (M2) a 0.941 togliendo la sola penalità ℓ2 interna del trainer. Per definire la variante si sono usati soltanto l'addestramento e la validazione SQuAD di Qwen. Le sonde della diagnostica non hanno prodotto punteggi né sulle 400 domande di verifica (HM0) né sulle coppie B/C. Dell'originale si erano già visti i punteggi della prova tecnica (Qwen, 200 + 40, coppie di 9 storie), che non entrano negli esiti.
- **Definizione.** M2-senzaℓ2 è M2 (§2.1–§2.9) con una sola differenza: la penalità ℓ2 interna del trainer, Σw² / (2 × batch), si toglie in valore e in gradiente, con il metodo dell'Appendice B. Restano quelli di M2:
  - dati, strato, estrazione, lunghezza, scalatura;
  - inizializzazione (seme della libreria 42), al massimo 5 epoche, lr 1e-3, batch 8, Adam con `weight_decay` 0;
  - arresto anticipato della libreria, calcolato sulla perdita senza penalità;
  - scelta dell'epoca con l'F1 di validazione e controllo del ricaricamento (§2.7).
  Nessun iperparametro si cerca o si regola: la penalità non si sostituisce con un'altra regolarizzazione.
- **Esecuzione.** Nel lavoro `M2_<modello>` gli stati si estraggono una volta. Le due sonde si addestrano sugli stessi DataLoader, partendo dalla stessa inizializzazione: prima di ciascun addestramento si ripristinano lo stato iniziale della sonda e i generatori casuali. Si salvano in `sonda/` e `sonda_senzaL2/` e danno punteggi separati, ciascuna con il proprio controllo del ricaricamento. Se il ricaricamento della sola variante non passa, M2 resta valido e la variante è NON ESEGUITA per quel modello. Nella prova a secco (modelli minuscoli, CPU) i punteggi delle due sonde coincidono esattamente (scarto 0) con quelli delle due esecuzioni separate della diagnostica.
- **Ruoli (confermati da Simona l'11 novembre).** M2 resta l'**analisi principale**, come preregistrato. M2-senzaℓ2 è un'**analisi secondaria preregistrata**, con le stesse regole:
  - HM0 per modello (≥ 0.70, almeno 380 domande su 400; §2.9);
  - HM1 e HM2 (§5 del protocollo), contro lo stesso riferimento p(UNKNOWN) di `env_sirin`, sulle coppie comuni;
  - copertura minima di 760 coppie su 800;
  - analisi per famiglia (§3);
  - regola nominale dei 3 modelli su 4.
  I verdetti dei due metodi si riportano separati, uno accanto all'altro. Non si sceglie a posteriori il migliore, e gli esiti della variante non cambiano quelli di M2.
- **Portata.** Il risultato dell'ablation riguarda, per ora, Qwen su SQuAD, in questa esecuzione. Per gli altri modelli lo dice HM0, per modello. Se il miglioramento si trasferisce all'indeterminatezza logica lo dicono HM1 e HM2 sulle coppie.
- **Lettura.** La variante si cita sempre come «M2-senzaℓ2»: è una variante della configurazione di SIRIN, non il metodo pubblicato. Il confronto fra M2 e M2-senzaℓ2 sulle coppie è descrittivo e non ha un'ipotesi propria. Un insuccesso di M2 resta un «risultato sull'implementazione SIRIN e sulla configurazione adottata».
- **Molteplicità.** La variante aggiunge una famiglia di confronti con IC non corretti, e lo si dichiara accanto ai suoi esiti.

## 3. Analisi per famiglia: secondaria, preregistrata per M2

Riguarda **M2** e, con lo stesso ruolo secondario, **M2-senzaℓ2** (§2.10), ciascuno con il suo riferimento, nel notebook B. Le analisi per famiglia del notebook A restano esplorative.

**3.1 Calcolo.**
- Ogni storia appartiene a una sola famiglia: AND 67 storie, OR 67, IMPLIES 66, con 4 coppie ciascuna.
- Per ogni modello e famiglia f, su P−S:
  - **W_f** è la quota di coppie della famiglia in cui il punteggio di C supera quello di B (i pareggi valgono mezzo punto), mediata per storia;
  - **ΔW_f** = W_f(M2) − W_f(p(UNKNOWN) di `env_sirin`), sulle coppie comuni.
- Una coppia è valida solo se entrambi i punteggi sono finiti: NaN e ±infinito escono dalle coppie valide e si contano fra gli scarti per motivo («non finito»).
- **Controllo del segno.** Su punteggi sintetici, un punteggio massimo su ogni C deve dare W_f = 1 in ogni famiglia e quello opposto 0; coppie con NaN o ±infinito non devono essere contate come valide.
- **Margine di HM2_f:** 1 − W_f(riferimento), calcolato separatamente in ogni famiglia e per ogni modello, Qwen compreso. Se il margine è sotto 0.05, HM2_f in pratica non si può confermare in quella cella, e lo si segnala.
- IC al 95% con 2000 ricampionamenti delle storie della famiglia, seme 20261108.
- Si riportano anche W_f del solo riferimento e, come descrittivo, la stessa tabella su S−S.

**3.2 Esiti per famiglia.**
- **Condizione:** HM0 superato dal metodo (M2 o M2-senzaℓ2) per quel modello. Se non lo supera, le sue celle per famiglia sono NON VALUTABILI, con W_f descrittivo.
- **HM1_f:** CONFERMATA se il limite inferiore è > 0.5 e W_f ≥ 0.60; NON CONFERMATA se il limite superiore è ≤ 0.5; altrimenti NON CONCLUSIVA.
- **HM2_f:** CONFERMATA se il limite inferiore è > 0 e ΔW_f ≥ 0.05; NON CONFERMATA se il limite superiore è ≤ 0; altrimenti NON CONCLUSIVA.
- **Copertura** (almeno il 95% delle coppie della famiglia: 255 su 268 per AND e OR, 251 su 264 per IMPLIES):
  - per HM1_f contano le coppie valide di M2;
  - per HM2_f contano le coppie comuni a M2 e al riferimento.
  - Sotto la soglia W_f e ΔW_f sono descrittivi.
- **Molteplicità:** 3 famiglie per 4 modelli, con IC non corretti, e lo si dichiara. Gli esiti per famiglia sono secondari e non cambiano HM1 e HM2 complessive.
- **Lettura:** la regola dei 3 su 4 si legge come **criterio nominale**. «M2 riconosce l'indeterminatezza sulla famiglia f» si scrive solo se HM1_f è confermata in almeno 3 modelli su 4, specificando che gli IC non sono corretti. Lo stesso vale per HM2_f.

**3.3 Eterogeneità (descrittiva).**
- Per ogni modello si riporta **H = max_f W_f − min_f W_f**, con IC bootstrap (in ogni ricampionamento si ricampiona dentro ciascuna famiglia).
- **H ≥ 0.20 sulla stima puntuale** è un riferimento descrittivo per scrivere «forti differenze tra famiglie». L'IC si riporta ma non entra nel confronto. Non è un criterio di conferma.

**3.4 Cosa non verifica.** Questa analisi verifica il comportamento di M2 per famiglia. Non replica il vantaggio di M4-LoRA su AND: per quello serve un esperimento separato su storie nuove, con M4-LoRA e il suo riferimento e il confronto per famiglia fissato prima.

## 4. Prova tecnica del notebook B

- **Qwen:**
  - 200 domande di addestramento (100 e 100), 40 di validazione, 40 di verifica e le coppie di **9 storie** (3 per famiglia, come la prova del notebook A; la v2 diceva 10);
  - catena completa, compresi la scelta dell'epoca e il controllo di ricaricamento (§2.7).
- **Misure di RAM su Qwen e Mistral** (§2.6): 200 + 40 e 400 + 80 esempi, fino a train e validazione in memoria. La sonda non si addestra.
- **Si controllano:**
  - installazione e impronta di `env_sirin` rispetto al notebook A;
  - le condizioni di riuso dei riferimenti (§2.8);
  - i chat template reali dei 4 tokenizer e i controlli del confine (§2.4), che le prove locali con modelli minuscoli non possono verificare;
  - picco di RAM per fase, proiezione a 2400 e a 1200 esempi e tempo per esempio;
  - i conteggi di §2.4 sui due campioni e sulle 400 di verifica;
  - l'elenco degli ID e il suo sha256 (§2.6).
- I numeri della prova non entrano negli esiti, come in §7 del protocollo.
- **Prova della v4 (M-B-notebook-4).** Stesse dimensioni (Qwen 200 + 40, 9 storie) con le due varianti. La decisione sulla RAM è legata alla versione del notebook e agli script, quindi la prova rifà le misure di RAM; la revisione di SQuAD e gli sha256 degli ID sono già nella cella 1 e la prova controlla che la selezione sia la stessa. Le misure non cambiano significato: si fermano prima dell'addestramento, e il secondo addestramento non aggiunge stati in memoria.

## 5. Scelte approvate (Simona, 10 e 11 novembre)

| Scelta | Esito |
|---|---|
| 1. Strato centrale fisso (18, 20, 16, 16) | approvata, con il controllo sulla configurazione del modello alla revisione fissata (§2.2) |
| 2. SQuAD 2000 + 400 | approvata, con gli ID fissati e la riserva decisa solo sul picco di RAM, misurato anche su Mistral, legata alle misure e ricontrollata nel completo (§2.6) |
| 3. Limite di 512 token | approvato, con il taglio a monte del solo contesto, parola per parola dalla fine, i controlli su domanda e confine e il conteggio degli span persi (§2.4) |
| 4. Regolarizzazione | `weight_decay` 0 della libreria, con il termine ℓ2 fisso del trainer (Σw² / (2 × batch), 1/16 con batch 8) così com'è; AUROC pubblicata solo descrittiva (§2.7). Corretta nella v2.1 |
| 5. Analisi per famiglia | approvata come analisi secondaria preregistrata; 3 su 4 nominale; H ≥ 0.20 sulla stima puntuale, descrittivo; HM0 per modello; copertura e margine per famiglia (§3) |
| Correzione del checkpoint | F1 di validazione esplicito, `state_dict` completo dell'epoca migliore, controllo dell'epoca ricaricata e del ricaricamento (§2.7) |
| Riuso di p(UNKNOWN) | anche revisione, configurazione d'inferenza, ID e prompt; JSON e configurazione del riferimento riusato nello ZIP di B (§2.8) |
| HM0 e RAM | almeno 380 domande su 400 per assegnare HM0 (§2.9); soglia della RAM all'85% della sessione (§2.6) |
| Variante M2-senzaℓ2 (v2.2) | da valutare nel completo accanto a M2 (Simona, 11 novembre); HM0 per modello prima delle coppie; ruoli confermati: M2 analisi principale preregistrata, M2-senzaℓ2 variante secondaria preregistrata con le stesse regole e verdetti separati, che affianca l'originale (§2.10) |

## Modifiche rispetto alla v2

1. **Regolarizzazione (§1, §2.7, §5).** La v2 leggeva «weight decay 0» come assenza di regolarizzazione ℓ2. Il trainer aggiunge invece sempre Σw² / (2 × batch), bias esclusi e query compresa (1/16 con batch 8). Il codice del notebook non cambia; cambia la descrizione.
2. **Accorciamento (§2.4):** definizione di parola, una parola alla volta dalla fine, prefisso dell'originale, controlli del confine con i 4 tokenizer e indici LEFT esattamente 0…n−1.
3. **Dati (§2.6):** 20% degli articoli alla validazione, sottoinsiemi annidati, ordine fissato, verifica ritrovata per `sq_id`.
4. **RAM (§2.6):** misure a due dimensioni su Qwen e Mistral che si fermano prima dell'addestramento; proiezione della sola crescita; decisione legata alle impronte delle misure e alle condizioni; ricontrollo del budget nella sessione del completo, con la decisione più prudente; stime da codice dichiarate come ipotesi.
5. **Riferimenti (§2.8):** impronta del notebook A ricostruita; riferimento riusato e sua configurazione nello ZIP di B.
6. **Analisi (§3):** NaN e ±infinito esclusi dalle coppie valide; controllo del segno su punteggi sintetici; H ≥ 0.20 sulla stima puntuale.
7. **Prova (§4):** 9 storie invece di 10; misure di RAM su due dimensioni.
8. **Dopo la prova 1 (11 novembre, notebook M-B-notebook-3):** decodifica senza pulizia degli spazi (§2.3), approvata da Simona.

## Modifiche rispetto alla v2.1

1. **Variante M2-senzaℓ2 (§2.10, nuova):** definizione, esecuzione nello stesso lavoro con la stessa inizializzazione, ruoli, portata e lettura. Riferimenti in §2.7, §2.9, §3, §4 e §5.
2. **Appendice B:** etichette del rapporto dell'ablation corrette (penalità controfattuale, obiettivo ottimizzato) e portata del risultato.
3. **§2.7:** batch del DataLoader verificato nel codice (8), quindi il coefficiente 1/16 è confermato.
4. **Correzioni di Simona all'approvazione (11 novembre):** momento della definizione della variante scritto con precisione (dopo la diagnostica SQuAD, prima dei suoi punteggi sulle coppie e su HM0); «al massimo 5 epoche», con l'arresto anticipato; ruoli confermati.
5. **Appendice, prova della v4:** decisione sulla RAM STOP con 83.5 GB; scelta A di Simona (stesse misure, decisione ricalcolata con circa 167 GB, riserva attesa, 1000 + 200 per i quattro modelli); conseguenze per la variante.

## Appendice: ID dei campioni SQuAD

Dalla prova del 11 novembre (notebook M-B-notebook-3, A100, sessione da 167.1 GB):
- revisione di SQuAD 2.0 (`rajpurkar/squad_v2`): `3ffb306f725f7d2ce8394bc1873b24868140c412`;
- bacino dopo §2.4: 130297 domande ammesse su 130319; 438 accorciate; 22 escluse perché la risposta è stata tagliata dall'accorciamento, tutte con risposta;
- selezione piena (2000 + 400): accorciate 6 in addestramento (3 per classe) e 1 in validazione;
- sha256 dell'elenco di addestramento: `10966c4c815bfa5e1441de49c9e77f59caf658de3a63d78f4c5a25736f5bed4b`;
- sha256 dell'elenco di validazione: `ca0f3def47b955688a9f7e5ccb97f58b9da444128e2b601b88d7c99de15ee057`;
- controlli del confine: 0 errori con i 4 tokenizer su addestramento, validazione, verifica e coppie;
- decisione sulla RAM: piena. Proiezioni dei picchi: Mistral 130.6 GB (piena) e 67.5 GB (riserva), Qwen 106.9 e 55.2 GB, contro un limite di 142.0 GB (85% di 167.1 GB). Questa decisione era legata alla versione M-B-notebook-3 e non vale per la v4.

**Prova della v4 (11 novembre, M-B-notebook-4, A100, sessione da 83.5 GB).**
- Selezione SQuAD identica: stessa revisione, stessi conteggi (130297 ammesse, 438 accorciate, 22 escluse) e stessi sha256 degli ID, controllati dal notebook. Controlli del confine: 0 errori.
- Due sonde su Qwen (200 + 40): ricaricamento con scarto 0 per entrambe, epoca ricaricata corretta, riferimento p(UNKNOWN) di Qwen riusato dal notebook A. Gli HM0 della prova (0.38 per M2, 0.40 per M2-senzaℓ2, su 40 domande) sono diagnostici e non hanno valore conclusivo.
- Misure di RAM (nuove, legate alla v4). Mistral: 16.4 GB a 240 esempi e 31.6 GB a 480, proiezione 153.7 GB per la piena e 77.4 GB per la riserva. Qwen: 13.7 e 24.2 GB, proiezione 107.8 e 55.5 GB. Le misure di Mistral sono più alte di quelle della prova 2 (17.1 e 29.7 GB): una differenza di circa 2 GB a 480 esempi diventa circa 23 GB nella proiezione a 2400.
- Decisione nella sessione da 83.5 GB (limite 71.0 GB): STOP.
- **Scelta di Simona (11 novembre, opzione A).** Si tengono le misure registrate e si ricalcola la sola decisione rieseguendo la prova in una sessione da circa 167 GB (limite circa 142 GB). Con queste misure la decisione attesa è **riserva**. Il completo usa quindi **1000 + 200 esempi per ciascuno dei quattro modelli**, con soglie e criteri invariati. La riserva deriva dalla regola sulla RAM (§2.6), non da una scelta sui risultati.
  - Ripetere una misura di RAM non è di per sé scorretto, ma scegliere poi quella più favorevole richiederebbe una regola esplicita. L'opzione A evita questa scelta.
- **Conseguenza per M2-senzaℓ2.** Il confronto fra le due sonde resta valido, perché usano gli stessi dati. La prestazione della variante va verificata con 1000 + 200 esempi, senza dare per acquisito lo 0.941 ottenuto nell'ablation con 2000 + 400.

## Appendice B: diagnostica prima del completo (regola fissata da Simona l'11 novembre alle 8:08, prima dei risultati)

Dopo la prova tecnica i punteggi di M2 su Qwen (200 + 40) erano quasi costanti. Prima del completo si esegue una diagnostica su Qwen con 2000 + 400 esempi, solo su SQuAD, con la configurazione della libreria invariata. Si registrano, per epoca, AUROC e F1 su addestramento e validazione, BCE, penalità ℓ2 e norme dei parametri. Non si calcolano HM0 né i punteggi delle coppie. I valori si leggono sull'epoca ricaricata dal trainer, cioè quella che userebbe il metodo.

- **Caso 1. AUROC di validazione ≥ 0.70:** si procede con il completo, configurazione invariata. HM0 si valuta poi sul suo campione separato.
- **Caso 2. AUROC di addestramento ≥ 0.70, validazione < 0.70:** difficoltà di generalizzazione. La causa resta da determinare, e la regolarizzazione potrebbe contribuire.
- **Caso 3. AUROC di addestramento e di validazione < 0.70:** segnale insufficiente rispetto all'obiettivo. Si esegue un'ablation della ℓ2 sugli stessi dati, con la stessa inizializzazione, lo stesso seme, le stesse epoche e lo stesso criterio di scelta del checkpoint, cambiando soltanto la penalità. Il rapporto fra ℓ2 e BCE è un indizio; il confronto diretto ne verifica l'effetto.
- **Valori sotto 0.70:** si descrivono come segnale insufficiente rispetto all'obiettivo. Un AUROC di 0.65, per esempio, può indicare apprendimento parziale.
- **Analisi principale:** resta M2 originale. Un'eventuale variante si documenta in questa nota prima di valutarla sulle coppie.
- **Interpretazione di un insuccesso:** «risultato sull'implementazione SIRIN e sulla configurazione adottata». Modelli, campioni e diversi dettagli di addestramento differiscono dall'esperimento dell'articolo.

**Risultato della diagnostica (11 novembre, 8:13; Qwen, 2000 + 400, configurazione invariata).** L'epoca ricaricata è la 1. L'AUROC è 0.606 sull'addestramento e 0.575 sulla validazione, quindi siamo nel **caso 3**: segnale insufficiente rispetto all'obiettivo. Osservazioni descrittive:
- nella prima epoca la norma della query scende da 1.007 a 0.016 e quella dei pesi da 0.573 a 0.230, mentre la penalità ℓ2 passa da 0.084 a 0.003. La BCE quasi non cambia: da 0.6928 a 0.6918 sull'addestramento.
- Dalla prima epoca la sonda predice «senza risposta» per il 100% degli esempi. I punteggi stanno fra 0.503 e 0.534, e le medie per classe differiscono di 0.002. L'F1 di 0.667 con cui la libreria sceglie il checkpoint è quindi quello del classificatore banale («sempre senza risposta» con classi bilanciate). La scelta dell'epoca è avvenuta per parità.
- L'arresto anticipato scatta dopo l'epoca 3, perché la perdita cambia meno di 1e-4.

**Ablation della ℓ2 (caso 3).** Stessa esecuzione, con lo stesso codice della libreria. La penalità interna del trainer, 0.5·Σw²(senza bias)/batch, si toglie in valore e in gradiente dopo che la closure della libreria l'ha calcolata: dai gradienti si sottrae w/batch prima del passo di Adam, e dalla perdita restituita il valore della penalità. Dati, inizializzazione, seme, epoche, arresto anticipato (sulla perdita senza penalità) e scelta del checkpoint restano quelli. Verifica locale: tre passi del trainer così modificato danno parametri identici (scarto 0.0) ad Adam sulla sola BCE. L'istantanea iniziale coincide con quella dell'esecuzione invariata, quindi l'inizializzazione è la stessa. L'ablation è diagnostica e non sostituisce M2 originale (analisi principale).

**Risultato dell'ablation (11 novembre, 8:49; Qwen, 2000 + 400; configurazione invariata salvo la penalità ℓ2 interna del trainer, tolta in valore e in gradiente).** L'istantanea iniziale coincide con quella dell'esecuzione invariata: AUROC 0.549 e 0.520, stesse norme. L'epoca ricaricata è la 5, con AUROC 0.943 sull'addestramento e **0.941 sulla validazione**; nell'esecuzione invariata era 0.575. F1 di validazione per epoca: 0.648, 0.858, 0.872, 0.870, 0.879. Le norme crescono invece di ridursi: query 11.3, pesi 9.8. La penalità che la libreria avrebbe applicato a questi pesi vale 14.0, contro una BCE di 0.33. Addestramento e validazione restano vicini, quindi non c'è segno di sovradattamento. I punteggi per esempio e per epoca sono in `punteggi_per_esempio_senzaL2.csv` (16800 righe). Il confronto diretto attribuisce il collasso della sonda alla penalità ℓ2 interna del trainer, con questi dati e questa configurazione. Il risultato riguarda, per ora, Qwen su SQuAD, in questa esecuzione. Se il miglioramento si trasferisce all'indeterminatezza logica è la domanda del test successivo, cioè del completo (§2.10).

**Etichette del rapporto dell'ablation (correzione di Simona, 11 novembre).** Nel file `M2DIAG_qwen_senzaL2.json` (diagnostica M-B-diag-3), all'epoca ricaricata:
- `penalita_l2 = 13.9841` è il **valore controfattuale** della penalità tolta: quanto la libreria avrebbe aggiunto con quei pesi. Non è stato applicato.
- `obiettivo_su_tutto_addestramento = 14.3171` somma la BCE (0.3330) e quel termine controfattuale, mentre l'addestramento ottimizzava la sola BCE.
- Il campo `nota` del file dice «Configurazione della libreria invariata». Vale solo per l'esecuzione invariata; per l'ablation la configurazione è invariata salvo la penalità.

La diagnostica M-B-diag-4 (celle A4 e B4 in `diagnostica_M2/`) scrive invece `penalita_l2_applicata` (0 nell'ablation), `penalita_l2_controfattuale` e `obiettivo_ottimizzato_su_tutto_addestramento` (la sola BCE nell'ablation), con una nota diversa per le due esecuzioni. I numeri non cambiano: cambiano i nomi.
