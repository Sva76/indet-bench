# Note al notebook `IndetBench_modelli_grandi_v4.ipynb` (N-notebook-4)

15 novembre 2026. Bozza per la revisione di Simona prima del lancio («punto 2»: modelli più grandi). La parte B (modelli reasoning) è fuori da questo notebook: richiede un protocollo proprio (sezione 6).

## 1. Scopo e statuto

Questo notebook verifica se il comportamento di p(UNKNOWN) sulle 800 coppie congelate in prosa (set PN) regge anche su modelli più grandi, **a famiglia fissa**: per ogni famiglia con un risultato valido si prende la versione più grande. I risultati sono **esplorativi**, come quelli del 14 novembre. Il confronto con le baseline resta descrittivo e non permette di affermare la superiorità di p(UNKNOWN).

## 2. Che cosa resta identico al notebook dei modelli nuovi (N-notebook-3)

- Benchmark congelato, prompt invariati, esportazione `export_rows("PN")`.
- Inferenza `hf_runner.score_pairs`: bfloat16, attenzione eager, batch 1, greedy, 8 token, solo il messaggio utente. Per Qwen3 il ragionamento è spento.
- `report` con la soglia di competenza vincolante (≥ 0.50 sui B, complessiva e per gold), copertura minima 760 coppie, esclusioni per lunghezza misurate e controllate, baseline descrittive. La «p(UNKNOWN) normalizzata» resta nel confronto con la sua nota, come deciso da Simona il 14 novembre. Tre livelli, anomalie DA CLASSIFICARE, controllo CPU dei 4 W del Test U2 obbligatorio prima del completo, identità delle coppie fra i modelli, controllo positivo Qwen3-8B.
- Repository al commit di main `2aa1f62`. Fra `c086e65` e `2aa1f62` i file `original_benchmark.py`, `hf_runner.py`, `metrics.py` e il benchmark congelato non sono cambiati (verificato con `git diff`).

## 3. Modelli proposti (revisioni lette dall'API di Hugging Face il 15 novembre, ricontrollate dal notebook)

| Chiave | Modello | Revisione | Parametri | Licenza | Pesi | Confronto con |
|---|---|---|---|---|---|---|
| qwen_controllo | Qwen/Qwen3-8B | b968826d… | 8B | Apache-2.0 | bf16 | controllo positivo |
| qwen3_32b | Qwen/Qwen3-32B | 9216db5781bf21249d130ec9da846c4624c16137 | 33B | Apache-2.0 | bf16, ~66 GB | Qwen3-8B (Test U2) |
| olmo2_32b | allenai/OLMo-2-0325-32B-Instruct | b96024342a77a69aa0dda815c3454a671f477463 | 32B | Apache-2.0 | bf16, ~65 GB | OLMo-2-1124-7B (Test U2) |
| gemma2_27b | google/gemma-2-27b-it | aaf20e6b9f4c0fcf043f6fb2a2068419086d77b0 | 27B | Gemma (gated) | bf16, ~55 GB | Gemma-2-9B (14 nov) |
| llama33_70b_4bit | meta-llama/Llama-3.3-70B-Instruct | 6f6073b423013f6a7d4d9f39144961bfbfbc386b | 71B | Llama 3.3 Community (gated) | **nf4 4 bit**, ~40 GB | Llama-3.1-8B (Test U2) |

- **Quantizzazione.** Llama-3.3-70B in bf16 richiede circa 141 GB e non entra nella A100. Il notebook lo carica in 4 bit nf4 con bitsandbytes, calcolando in bfloat16. Nel manifest risultano il tipo di pesi e la versione di bitsandbytes. È l'unica deviazione dalle impostazioni del Test U2: il suo risultato va letto come «70B quantizzato», non come 70B in precisione piena.
- **Confronti a famiglia fissa** (descrittivi): il notebook non calcola test fra modelli piccoli e grandi. Il resoconto metterà accanto i W pubblicati (Test U2) o del 14 novembre.
- **Esclusi.** Mistral-Small-3 (24B) probabilmente inserisce la data nel template e il notebook lo fermerebbe. L'alternativa Mistral-Small-Instruct-2409 (22B) ha una licenza di sola ricerca. Yi resta escluso (NON VALUTABILE il 14 novembre).

## 4. Novità della v4 (regole fissate prima dei dati)

1. **Copertura delle etichette (dopo il caso Yi).** Dopo il caricamento, su 24 righe (storie V2001–V2003) il notebook misura la massa di YES+NO+UNKNOWN al primo token, il token più probabile e se questo è fra le etichette. Registra anche i token delle etichette. **Se la massa mediana è < 0.5 il modello è NON MISURABILE (motivo tecnico)** e l'inferenza completa non parte. La stessa regola si riapplica alla massa mediana sull'insieme completo. In quel caso l'esito del codice resta registrato in `esito_del_codice_prima_della_regola_massa`. La soglia 0.5 separa il caso Yi (mediana 2·10⁻⁶) dai modelli valutabili (mediana ≥ 0.99 per tutti i modelli del 14 novembre e del Test U2).
2. **Memoria della GPU.** Ogni modello dichiara la memoria minima: 75 GB per i 27–33B in bf16, 45 GB per il 70B in 4 bit. Su una GPU più piccola il modello viene saltato con un *errore* (non con un esito), così rilanciando su una A100-80GB riparte.
3. **Disco.** Prima del download il notebook controlla lo spazio libero, e dopo ogni modello cancella i pesi dalla cache locale di Colab (non da Drive). Insieme i cinque modelli superano il disco della sessione.
4. **`GH_TOKEN` facoltativo.** La repository è pubblica; se il token c'è, lo si usa come prima, senza mai stamparlo.

## 5. Controlli fatti (CPU, modello finto)

- Il controllo CPU dei 4 W del Test U2 è superato anche con la repository a `2aa1f62`.
- La regola sulla massa funziona: un modello finto con massa mediana 0.04 è fermato come NON MISURABILE prima dell'inferenza completa.
- Il controllo del disco funziona: con 23 GB liberi, Gemma-2-27B e Llama-70B sono saltati con un errore e gli altri modelli proseguono.
- L'installazione di bitsandbytes funziona (versione registrata).
- **Non provato:** il caricamento in 4 bit e i modelli veri su GPU. Lo verificano la prova e il controllo positivo.

## 6. Parte B, modelli reasoning (proposta, non in questo notebook)

Nei modelli reasoning la risposta arriva dopo un ragionamento, quindi «la probabilità del primo token» non è più ben definita. Il disegno più pulito è **Qwen3-8B con il ragionamento acceso** (`enable_thinking=True`): sono gli stessi pesi del controllo positivo, quindi il confronto acceso/spento è a modello fisso. p(UNKNOWN) si misura sul primo token della risposta dopo la chiusura del ragionamento (`</think>`), con un budget massimo di ragionamento fissato prima. Serve una nota di protocollo dedicata, da approvare prima del notebook. Punti da fissare:
- il budget di token;
- cosa fare se il ragionamento non si chiude;
- se misurare anche durante il ragionamento;
- il batch, che potrebbe essere necessario per i tempi.

## 7. Prima del lancio

- Sessione **A100-SXM4-80GB** (controllare con `!nvidia-smi`) e spazio disco sufficiente: almeno circa 150 GB liberi per il 70B.
- Accettare su Hugging Face le licenze di Gemma-2-27B e di Llama-3.3-70B con l'account del `HF_TOKEN`.
- `testU2_risultati.zip` in MyDrive.
- Tempi stimati, non misurati: 15–30 minuti di inferenza per ciascun modello da 27–33B, circa un'ora per il 70B in 4 bit, più i download (60–140 GB per modello).
