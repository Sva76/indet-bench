# Note al notebook `IndetBench_reasoning_v2.ipynb` (R-notebook-2)

15 novembre 2026, sera. Questa versione corregge la pipeline di misura dopo la prova del pomeriggio. Valgono ancora le note della v1 (`Note_reasoning_v1.md`), salvo quanto scritto qui.

## 1. Che cosa è successo nella prova (R-notebook-1, A100-SXM4-40GB)

- Il **controllo della pipeline non è superato**: sulle 24 righe di controllo, a ragionamento spento, lo scarto massimo dal Test U2 è 0.060 (tolleranza 0.01) e le risposte uguali sono 23/24. Sulle 80 righe della prova lo scarto massimo è 0.229 (79/80 risposte uguali). Secondo il protocollo (§5.1) il completo non parte con questa pipeline.
- Lo scarto sta tutto nelle righe con probabilità intermedia: 11 righe su 80 superano 0.01 e sono tutte casi C con la domanda all'ultima riga. La mediana dello scarto è 6e-7. Le lunghezze dei prompt sono identiche a quelle del Test U2.
- Il notebook non ha fermato la sessione da 40 GB: controllava solo che la GPU fosse una A100.

## 2. Causa più probabile

- **Ipotesi:** la misura a batch 16 con padding a sinistra e attenzione sdpa. In bfloat16 questa cambia gli arrotondamenti dei logit rispetto al Test U2, che misurava a batch 1 e con attenzione eager. Fra le 64 righe in cui la probabilità cambia più del 10%, in 45 il rapporto con il Test U2 è una potenza esatta di e^0.25, il passo dei logit in bfloat16 in quella fascia. La differenza è quindi numerica, non di testo né di token.
- **Prova a favore:** la parte A, con la stessa versione di transformers (5.22.1) ma a batch 1 ed eager, ha riprodotto il Test U2 con scarto 8e-17 e 24/24 risposte uguali.
- **GPU da 40 GB:** è improbabile che sia la causa, perché nel Test M le A100 da 40 e da 80 GB hanno dato valori identici (scarto 1e-16). Non è però escluso. La diagnostica qui sotto lo verifica sulla sessione da 80 GB.
- **Incertezza:** la prova non separa l'effetto del batch da quello di sdpa. Lo fa la diagnostica.

## 3. Che cosa cambia nella R-notebook-2 (da approvare: modifica la riga «Batch e attenzione» del protocollo)

1. Il **ragionamento** si genera ancora a batch (16, oppure 4 per Qwen3-32B) con sdpa e con il campionamento degli autori.
2. La **misura** si fa riga per riga, a batch 1 senza padding e con attenzione eager, come nel Test U2 e nella parte A. Comprende la risposta greedy e la probabilità delle etichette. Vale in tutte e due le condizioni. Per la condizione accesa la misura parte dai token del ragionamento generato e dalla chiusura, senza ritokenizzare.
3. Il **controllo della pipeline** resta identico: tolleranza 0.01 e 24/24, sulla nuova misura.
4. **Diagnostica descrittiva** (solo Qwen3-8B, prima del controllo): le 24 righe si rimisurano a batch 1 e 16, con eager e con sdpa. Si registra lo scarto di ciascuna combinazione dal Test U2. Non decide niente: serve a confermare o smentire la causa del §2.
5. **GPU** (aggiornato alle 17:50, dopo che Colab ha assegnato a Simona solo la 40 GB): `SOLO_80GB = False` per impostazione. Vale il minimo di ogni modello: Qwen3-32B richiede 80 GB e su 40 GB si ferma. Phi-4-reasoning su 40 GB genera il ragionamento a batch 8 invece di 16, perché la cache di 16 sequenze da circa 4300 token non ci sta (circa 14 GB più 29 GB di pesi). Il batch è registrato nel manifest. Il nome della GPU entra nell'impronta della cartella, quindi una sessione su un'altra GPU non mescola i blocchi. Il nome compare anche nell'intestazione del rapporto.
6. **Costo:** la misura a batch 1 aggiunge circa 0.3 s per riga, cioè una decina di minuti per 1600 righe.

Prova a secco sulla CPU, con il modello finto: con il ragionamento uguale, la misura nuova dà gli stessi ragionamenti e le stesse risposte della v1, con punteggi entro 2e-6. Il completo si ferma se il controllo non è superato. Con 42 GB di GPU il notebook si ferma.

## 4. Altri dati della prova (tecnici, nessuna lettura scientifica)

- Massa mediana sulle etichette: 1.0. Tutte le 80 righe accese hanno chiuso il ragionamento da sole. La mediana è di 274 token sui B e 298 sui C, con un massimo di 3457.
- Ripetibilità (2 storie, 16 righe): con gli altri due semi le risposte uguali sono 15/16 e 14/16.
- Tempo: 577 s per 80 righe accese su 40 GB, cioè circa 7 s a riga. Il completo di Qwen3-8B (1600 righe più 320 di ripetibilità) richiede circa 4 ore. Qwen3-32B e Phi-4-reasoning saranno molto più lenti: per stimarli serve una prova di ciascuno.

## 5. Decisione di Simona (15 nov, 17:20) e che cosa rilanciare

Simona ha scelto **«Prima solo la diagnostica»**. La pipeline si decide dopo la diagnostica, prima di leggere qualsiasi risultato sulle storie.

Per questo il notebook ha `SOLO_DIAGNOSTICA = True` (cella 1). Con questa impostazione carica Qwen3-8B e misura solo le 24 righe di controllo: quattro combinazioni di batch e attenzione, più il controllo della pipeline nella misura nuova. Salva lo ZIP e si ferma, senza generare ragionamenti e senza misurare le storie.

Da lanciare: sessione **A100**, va bene anche quella da 40 GB, notebook `IndetBench_reasoning_v2.ipynb`, `MODALITA = "prova"`, `MODELLI = ["qwen3_8b"]`, `SOLO_DIAGNOSTICA = True`, poi `AVVIA_GPU = True`. Il tempo previsto è di qualche minuto, quasi tutto per scaricare il modello.

Come leggere la diagnostica:
- La diagnostica sulla 40 GB basta. Il Test U2 è stato misurato proprio su una A100-SXM4-40GB, e la parte A lo ha riprodotto sulla 80 GB con scarto 8e-17, cioè a batch 1 con eager. A parità di misura, quindi, la GPU non cambia i valori. Su 40 GB la diagnostica confronta il notebook con un riferimento fatto sulla stessa GPU.
- Se «batch 16, sdpa» ridà circa 0.06, il risultato della prova si ripete.
- Se «batch 1, eager» dà uno scarto di circa 0, la causa sono batch e attenzione. L'altra combinazione a batch 1 o a batch 16 dice quale delle due pesa.
- Se anche «batch 1, eager» si scosta, la causa è un'altra (ambiente o versione), e la misura a batch 1 da sola non basta.

## 6. Esito della diagnostica (15 nov, 18:13, A100-SXM4-40GB, R-notebook-2)

| Batch, attenzione | scarto max dal Test U2 (24 righe) | risposte uguali |
|---|---|---|
| batch 1, eager | 8.3e-17 | 24/24 |
| batch 1, sdpa | 0.060 | 23/24 |
| batch 16, eager | 0.117 | 23/24 |
| batch 16, sdpa | 0.060 | 23/24 |

Il controllo della pipeline nella misura nuova (batch 1, eager) è superato: scarto 8.3e-17, 24/24.

Che cosa dice:
- La causa è confermata: la misura del Test U2 si riproduce solo a batch 1 con eager.
- Bastano sdpa da sola (a batch 1) o il passaggio a batch 16 con eager, che porta con sé il padding, per spostare i valori. La diagnostica non separa il batch dal padding.
- La GPU da 40 GB non è la causa.
- La configurazione con cui si genera il ragionamento (batch e sdpa) non entra nei calcoli della misura, perché la misura riparte riga per riga a batch 1 con eager. Il testo del ragionamento invece entra, come prefisso: un ragionamento diverso, per esempio con un altro seme o con altri arrotondamenti nella generazione, può dare probabilità diverse. Questa è la dipendenza dal ragionamento campionato che la ripetibilità misura, ed è distinta dall'effetto numerico della configurazione di misura.

Archivio: `diagnostica_parte_B/indetbench_reasoning_diagnostica_20261115.zip`. Lo ZIP contiene anche la cartella della prova R-notebook-1. In attesa dell'approvazione di Simona della misura a batch 1 con eager.
