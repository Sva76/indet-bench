# Test C (allucinazioni con contesto): protocollo v3

Data: 11 novembre 2026. Stato: **disegno approvato da Simona l'11 novembre (15:25), con le precisazioni di questa versione. Alle 15:46 si sono aggiunte la regola di selezione (§3.3c) e la correzione su M3 in HC2. Pronto per il generatore e la sua verifica. L'11 novembre sera, dopo la revisione del campione di Simona, si sono corrette le cronologie del contorno (C-gen-4) e le regole del naturale (C-sel-4): punto 9 qui sotto.** Nessun dato è stato generato o raccolto. Il notebook si scrive dopo che il generatore ha superato i controlli di §3.3 e la revisione manuale di §3.4.
Sostituisce `Protocollo_testC_bozza_v2.md` e `Protocollo_testC_bozza.md` (v1).
Riferimenti: `PHI/Step1_verifica/Riepilogo_Step1.md` (punto C), `Protocollo_testM_metodi_v2.md`, `Nota_M2_configurazione_v2_2.md`, `Risultati_testU2.md`, `Risultati_testM_A.md`.

## Cosa cambia rispetto alla v2
1. **Scelte del §9 confermate da Simona** (ora §9, «Scelte fissate»):
   - quattro famiglie, con RIM fuori dall'analisi principale;
   - istruzione neutra;
   - «entrambi affermati» non supportata, per attributi definiti con un solo valore;
   - per HC4 almeno 30 risposte e 15 passaggi per classe, come soglia operativa che non si riduce dopo i risultati;
   - 200 passaggi nel completo.
2. **HC4 principale fra le risposte non astenute** (§6.2, §7). La conclusione si scrive come «discrimina il supporto fra le risposte non astenute». Non misura l'affidabilità complessiva del sistema. Si riportano astensioni, esclusioni e numerosità rimaste, e si aggiunge come descrittivo il confronto entro C con le astensioni incluse.
3. **Motivazione dell'esclusione corretta.** p(UNKNOWN) si calcola prima della generazione, quindi non c'è automaticamente una fuga dell'etichetta. L'esclusione serve a separare la discriminazione del supporto dalla semplice previsione dell'astensione.
4. **Prova C separata** (§3.1, §8). I 10 passaggi della prova tecnica sono diversi dai 200 definitivi, con un altro seme, altri ID e altre entità, perché la prova può modificare le regole di classificazione.
5. **Risposte qualificate** (§4). «Maybe 1821» non vale come l'asserzione «1821». Ha una categoria propria, «qualificata», ed è esclusa da HC4 principale.
6. **M3 in HC2 e HC4** (§5, §6.1, §7), con la correzione di Simona delle 15:46:
   - M3 dà un esito unico per HC1 e HC3;
   - HC2 dipende dal riferimento p(UNKNOWN), quindi M3 ha quattro ΔW, uno per il p(UNKNOWN) di ciascuno dei 4 modelli generatori. Sono quattro confronti dello stesso giudice, non quattro giudici diversi;
   - per HC4 le etichette dipendono dalle risposte del modello che genera, quindi la sua AUROC si riporta per ciascuno dei 4 modelli generatori.
7. **Regola di selezione esplicita** (§3.3c, aggiunta alle 15:46 su indicazione di Simona). Gli stessi 200 passaggi valgono per tutti i modelli e i metodi. Un passaggio entra solo se tutte le sue otto versioni superano i controlli. I passaggi si prendono entro quote fisse per tipo di attributo e schema di posizione, con un registro dei candidati e lo sha256 dell'insieme salvati prima delle inferenze.
8. **Correzioni dopo la verifica dei token di Simona** (16:15). Generatore C-gen-3 e selezione C-sel-3: varianti di lunghezza equivalenti senza «to this day», persone con un nome e un titolo, unicità scritta nel testo, scelta della variante con la differenza minima, controllo che il testo inviato al modello coincida con le frasi analizzate, insieme naturale riempito con i candidati successivi o dichiarato incompleto (§3.1, §3.3b, §3.3c).
9. **Correzioni dopo la revisione del campione di Simona** (11 novembre, 16:34, prima di qualsiasi inferenza). Ipotesi, soglie e criteri statistici non cambiano.
   - Generatore C-gen-4: gli anni del contorno seguono la cronologia; nessuna attività precede la nascita dell'entità (§3.1, §3.3 punto 3, §3.3b). Riserva rigenerata, sha256 nuovi.
   - Selezione C-sel-4: validazione dei riferimenti di SQuAD, divisione in frasi che rispetta iniziali, abbreviazioni e incisi, controllo dei segni di taglio, almeno 3 frasi vere in RIM-nat, distrattore di DUE-nat della stessa classe e plausibile, registro di ogni candidato con il controllo esatto non superato (§3.3c, §3.5).
   - Verifica indipendente della selezione, senza il codice del generatore e della selezione, con errori bloccanti (§3.3c).
   - Le versioni precedenti (C-gen-3, C-sel-3) restano archiviate, con il registro delle modifiche in `testC_generatore/Note_generatore_C_v3.md`.
   - Selezione C-sel-5 (11 novembre, 18:30, dopo la verifica indipendente di C-sel-4): i numeri dei distrattori di DUE-nat si leggono con il punto decimale; confini di frase anche prima di cifre e maiuscole accentate; divisore in frasi della verifica corretto. Sintetico invariato; naturale rifatto sull'intero bacino. C-sel-4 resta archiviata (`testC_generatore/Note_generatore_C_v3.md`, §6).

## Cosa cambiava dalla v1 alla v2
1. **Scelte confermate da Simona:**
   - l'insieme sintetico è il principale;
   - l'insieme naturale è descrittivo;
   - nessun metodo si riaddestra;
   - HC3 è secondaria preregistrata.
2. **HC0-set diventa descrittivo** (§7). L'accuratezza sui B misura il modello che genera, non la validità dei rilevatori, e non rende NON VALUTABILE nessun metodo (in particolare M3, che è un giudice indipendente). Si riporta per modello e per famiglia.
3. **HC4 si misura entro B ed entro C** (§6.2, §7). Il confronto fra le risposte non supportate su C e le risposte corrette su B diventa descrittivo, con il suo limite scritto: si può vincere distinguendo C da B, senza rilevare nulla della risposta. Gli IC ricampionano i passaggi, tenendo insieme le risposte dello stesso passaggio.
4. **Il controllo della «or» è forte per LOG** (§3.2). In B i due rami della disgiunzione portano allo stesso anno, in C ad anni diversi. La disgiunzione è nello stesso punto e riguarda la domanda in entrambi. Per DUE il controllo resta parziale (solo il conteggio) e lo si dichiara come limite.
5. **CONF ha una semantica esplicita** (§3.2): due fonti discordanti, senza priorità tra loro. La classificazione delle risposte distingue chi riporta i due valori come alternativi, chi li attribuisce alle fonti e chi afferma che sono veri entrambi (§4).
6. **Il generatore verifica la determinabilità** (§3.3):
   - ogni item nasce da una rappresentazione formale, e un risolutore calcola i valori compatibili;
   - il testo generato si rilegge e si ricontrolla;
   - si controlla il testo che ricevono davvero i quattro modelli, compreso il limite dei token.
   Per RIM-nat si tolgono tutte le occorrenze che permettono ancora di rispondere (§3.5).
7. **Formulazione sulle entità inventate:** riducono il rischio che la risposta venga dalla conoscenza memorizzata, ma non lo eliminano.

## 1. Perché questo test
Il riepilogo dello Step 1 chiude con il punto C: le allucinazioni con contesto (RAG, SQuAD), con lo stesso protocollo di validazione. Il Test M ha misurato i metodi esistenti sulle storie B/C. Qui la domanda si sposta sul terreno per cui molti di quei metodi sono stati pensati: un passaggio di testo e una domanda su quel passaggio.

**Domanda.** Quando il contesto non basta a rispondere, il modello risponde lo stesso? I rilevatori se ne accorgono? E se ne accorgono allo stesso modo in due casi diversi?
- L'informazione **manca**. È il caso classico dell'answerability, come in SQuAD 2.0.
- L'informazione è **indeterminata**. Il contesto dà due valori possibili, oppure due fonti in conflitto, oppure una catena logica con una premessa disgiuntiva, come nelle storie C.

La seconda distinzione è il ponte con il benchmark B/C (HC3).

## 2. Principi ripresi dal protocollo di validazione
- **Coppie minime.** B (il contesto determina la risposta) e C (non la determina) differiscono solo per la modifica che toglie la determinazione. Stessa domanda, stessa lunghezza entro una tolleranza.
- **Controllo della forma.** Dove si può, la «or» compare in B e in C nello stesso punto e con lo stesso ruolo (LOG). Dove non si può, si pareggia almeno il conteggio (DUE) e lo si dichiara.
- **Riferimento forte dalle uscite.** p(UNKNOWN) grezza sul primo token, senza addestramento.
- **Controllo positivo prima delle coppie.** Si eredita dal Test M.
- **Nessun adattamento.** Nessun metodo si addestra sui passaggi e nessuna soglia si sceglie sulle coppie.
- **Statistica come nel Test M.** W con bootstrap per passaggio, ΔW sulle coppie comuni, copertura minima e regola dei 3 su 4 modelli.
- **Prova tecnica prima del completo.** I suoi numeri non entrano negli esiti.

## 3. Dati

### 3.1 Insieme principale: passaggi sintetici con entità inventate
- **200 passaggi** in inglese, ciascuno su un'entità inventata di uno di quattro generi: una città, un'azienda, una nave o un festival. La persona resta solo come tipo di attributo (§3.3b).
  - Le entità inventate riducono il rischio che la risposta venga dalla conoscenza memorizzata del modello, ma non lo eliminano. Un nome inventato può somigliare a uno reale, e il modello può avere preferenze per certi valori.
  - I nomi si generano da sillabe e si scartano quelli che compaiono in un elenco di nomi reali (§3.3). Anche questo controllo riduce il rischio, senza escluderlo.
- **Struttura del passaggio:**
  - 8 frasi, tra 120 e 180 parole;
  - una frase porta il **fatto bersaglio** (o, in LOG, le regole e il fatto);
  - le altre frasi danno altri attributi della stessa entità, con valori dello stesso tipo (per esempio altri anni), quindi rispondere richiede di leggere il passaggio;
  - le frasi di contorno non nominano mai l'attributo bersaglio e non contengono relazioni da cui ricavarlo (niente «vent'anni dopo la fondazione»);
  - le date del contorno seguono la cronologia (C-gen-4): ogni anno di contorno viene da 3 a 70 anni dopo un anno di riferimento. Nei passaggi sull'anno il riferimento è il più tardo dei due valori in gioco, quindi nessuna attività (premio, laboratorio, restauro, palco) precede la fondazione, il varo o la prima edizione, né in B né in C. Negli altri passaggi il riferimento è un anno estratto e mai scritto. Il contorno resta identico fra B e C.
- **Attributi bersaglio:** anno, numero, luogo e nome di persona, in quote uguali.
- **Posizione del fatto bersaglio:** inizio, metà o fine del passaggio, bilanciata. Serve anche per la domanda aperta sulla posizione dell'incertezza.
- **Domanda:** una per passaggio, sul fatto bersaglio (per esempio «In what year was Lorvane founded?»).
- **Seme fisso** del generatore (20261111 per i 200 passaggi definitivi) e template scritti prima di qualsiasi dato.
- **Passaggi della prova, separati.** I 10 passaggi della prova tecnica si generano con un altro seme (20261112) e hanno ID ed entità diversi dai 200 definitivi. Il generatore controlla che i due insiemi non condividano né ID né nomi di entità. Le regole di classificazione si possono correggere sui dati della prova senza aver visto nessuna risposta sui 200 definitivi.
- **Attributi con un solo valore, scritti come tali nel testo.** Ogni attributo bersaglio ha un solo valore (anno di fondazione o di varo, numero di ponti, uffici, scialuppe o giorni). Per luoghi e persone l'unicità è detta nel testo, nella frase di B, nella disgiunzione di C e nella domanda: «its only warehouse», «its only home port», «its sole auditor», «its sole commander», «its only patron saint», «its sole patron», «all its prizes made in». Non si usano attributi che possono avere più valori (per esempio «i fondatori»). Così «entrambi affermati» è sempre una risposta non supportata, e il modello lo può ricavare dal passaggio stesso.

### 3.2 Quattro famiglie di modifica (una coppia B/C per passaggio e per famiglia: 800 coppie)

| Famiglia | B (determinato) | C (non determinato) | Che cosa misura |
|---|---|---|---|
| **RIM** (informazione assente) | «Lorvane was founded in 1821.» | al suo posto una frase sull'entità, di lunghezza simile, senza il valore e senza dire che manca («Lorvane was described in an old travel guide.») | answerability classica |
| **DUE** (due valori in disgiunzione) | «Lorvane was founded in 1821.» | «Lorvane was founded in 1821 or 1823.» | indeterminatezza esplicita |
| **CONF** (due fonti discordanti) | «According to the town archive, Lorvane was founded in 1821. According to the regional register, Lorvane was founded in 1821.» | la seconda fonte dà 1823 | indeterminatezza da conflitto, senza «o» |
| **LOG** (catena con premessa disgiuntiva, controllo forte) | «Every town on the Elm river was founded in 1821. Every town on the Dars river was founded in 1821. Lorvane lies on the Elm river or on the Dars river.» | la seconda regola dice 1823; la frase con la disgiunzione è identica | la struttura delle storie C, dentro un passaggio |

**LOG.**
- La disgiunzione è identica in B e in C, nella stessa posizione, e riguarda la domanda in entrambi.
- La sola differenza è il valore della seconda regola. In B i due rami portano allo stesso anno, in C ad anni diversi.
- Così la presenza di una «or» rilevante non distingue più C da B.
- L'ordine dei due fiumi e quale dei due rami cambia valore sono bilanciati.

**DUE.**
- Qui la disgiunzione c'è solo in C. Per pareggiare il conteggio, B contiene una frase irrilevante con «or» («Visitors arrive by boat or by train.»), che in C diventa «Visitors arrive by boat and by train.».
- Il controllo resta **parziale**: pareggia il numero di «or», non la differenza fra una «or» rilevante per la domanda e una irrilevante. Lo si scrive tra i limiti.
- Il confronto fra DUE e LOG, descrittivo, dice quanto pesa questa differenza.

**CONF.**
- Le due fonti hanno lo stesso rango: due nomi di archivio dello stesso tipo, nessuna più recente, ufficiale o affidabile dell'altra, e nessuna parola che indichi una correzione.
- Il passaggio non dice quale sia giusta. Questa semantica si scrive nei template e si controlla nella revisione manuale.
- Sono bilanciati: quale fonte viene prima, quale dà il valore diverso e la distanza fra le due frasi.
- In B le due fonti concordano (stesso valore ripetuto), quindi la struttura a due fonti c'è in entrambi.

**RIM.** Né B né C contengono «or». La frase sostitutiva non dice che l'informazione manca (non «the founding year is unknown»), perché quella sarebbe un'istruzione implicita, come la frase del Test U2.

**Lunghezza.** B e C differiscono al massimo di 3 token, con il tokenizer di ciascuno dei 4 modelli. Le coppie che non rispettano la tolleranza si rigenerano prima di qualsiasi esecuzione dei modelli.

### 3.3 Controlli del generatore (automatici, prima dei modelli)
1. **Determinabilità sulla rappresentazione formale.** Ogni item nasce da una rappresentazione formale: entità, attributi, fonti, regole e disgiunzioni. Un piccolo risolutore calcola l'insieme dei valori compatibili con il passaggio per l'attributo bersaglio.
   - B: esattamente un valore.
   - DUE, CONF, LOG in C: esattamente due valori.
   - RIM in C: nessun valore determinato dal passaggio.
   - In LOG il risolutore applica le regole a entrambi i rami della disgiunzione. Controlla così che in B i rami diano lo stesso anno e in C due anni diversi.
2. **Determinabilità sul testo generato.** Il testo si rilegge con un analizzatore inverso dei template (una espressione per template). Si ricostruisce la rappresentazione e si rilancia il risolutore. Il risultato deve coincidere con quello del punto 1. Così si controlla che il testo dica davvero ciò che dice la rappresentazione.
3. **Assenza di altre vie alla risposta.** Il valore bersaglio e il valore alternativo compaiono solo dove previsto. Nessuna frase di contorno contiene l'attributo bersaglio, e nessun valore di contorno coincide con i due valori in gioco. Per anni e numeri si controllano anche le forme scritte in lettere. Nei passaggi sull'anno ogni altro anno del testo, letto sul testo di tutte le versioni, deve venire dopo entrambi i valori in gioco (C-gen-4).
4. **Testo ricevuto dai quattro modelli.** Per ogni modello e per ogni formato di prompt usato da un metodo (il prompt di risposta, il formato SIRIN per M2 e M3, il formato LM-Polygraph):
   - si applica il chat template e si tokenizza;
   - si decodifica e si controlla che passaggio e domanda siano interi;
   - si controlla che il prompt stia sotto il limite di token del metodo (per M2 i 512 token già usati nel notebook B), senza troncamenti.
   Un passaggio che non passa esce dalla selezione (§3.3c). Non si accorcia.
5. **Bilanciamento.** Si controllano, per famiglia, la posizione, il tipo di attributo, i conteggi di «or», le lunghezze, l'ordine delle fonti e dei rami.
6. **Nomi.** I nomi inventati non devono coincidere con un elenco di nomi reali (città, aziende, persone) scelto prima della generazione.
7. **Impronte.** Gli ID dei passaggi e l'sha256 del file generato si fissano alla prova, come per SQuAD nel notebook B.

### 3.3b Dettagli fissati scrivendo il generatore (11 novembre, prima di qualsiasi risposta dei modelli)
I dettagli sono in `testC_generatore/Note_generatore_C_v2.md`. Versione del generatore: C-gen-4 (C-gen-3 archiviata; le differenze sono in `Note_generatore_C_v3.md`). I punti che toccano il disegno, confermati da Simona l'11 novembre alle 16:15:
- **Generi.** Sono quattro: città, azienda, nave e festival. La persona non è un genere, perché le regole di gruppo di LOG con attributi a valore unico suonano innaturali per una persona. Resta come tipo di attributo (patrono, revisore, comandante, mecenate).
- **Persone con un titolo.** Il nome inventato è uno solo e porta un titolo fisso per genere: «Saint», «Doctor», «Admiral», «Lady». Il titolo si ripete in tutte e due le alternative della disgiunzione. Valgono come risposta giusta sia il nome sia il nome con il titolo.
- **Varianti di lunghezza per la tolleranza di 3 token.** Le varianti allungano la frase senza aggiungere contenuto: dicono la stessa cosa con più parole.
  - Solo in DUE, nella frase del fatto di B, che altrimenti è più corta della disgiunzione di C: per gli anni «in the year {v}» e «in the course of the year {v}»; per i numeri «a total of {v}»; per luoghi e persone «in the city of {v}», «the only … of the town / of the company / of the ship / of the festival» e «the one and only …».
  - Non si usano forme che aggiungono informazione, come «to this day», che aggiunge una continuità nel tempo (tolta su indicazione di Simona).
  - In RIM la frase neutra di C ha sei lunghezze, dalla più breve alla più lunga, tutte senza valori dello stesso tipo dell'attributo.
  - Le varianti che portano il passaggio fuori da 120–180 parole si scartano prima dei controlli.
  - **Scelta della variante.** Per ogni famiglia si sceglie la coppia di varianti B/C con la più piccola differenza massima di token fra C e B sui 4 tokenizer. A parità vale il primo nell'ordine fisso del generatore. La coppia scelta deve stare entro 3 token. La soglia di 3 token non cambia.
- **CONF.** Le due fonti sono sempre a 3 frasi di distanza, cioè con due frasi interposte. La distanza non varia, e questo test **non studia l'effetto della distanza** fra le fonti.
- **Testo ricevuto dal modello.** Il prompt usa il campo `testo` del passaggio. Il controllo verifica che `testo` coincida con l'unione delle frasi e che, ridiviso in frasi, dia di nuovo le stesse frasi. L'analizzatore inverso e il risolutore lavorano sul testo ridiviso, non sulle frasi salvate. Nella selezione si estrae anche il passaggio dal prompt effettivo di ogni modello e lo si rianalizza.
- **Prova dei controlli.** Una serie di errori introdotti di proposito (per esempio un «not» aggiunto solo nel testo, la disgiunzione tolta in C, due fonti concordi, una parola dell'attributo nel contorno) deve essere segnalata tutta. Nella versione C-gen-3 erano 174 errori, tutti segnalati. Nella C-gen-4 si aggiunge un anno di contorno messo prima della fondazione in B e in C: 179 errori, tutti segnalati.
- **Cronologia (C-gen-4).** Vedi §3.1. Nella riserva C-gen-3 55 passaggi sull'anno su 100 avevano almeno un anno di contorno non successivo alla fondazione (casi 7, 12 e 11 della revisione di Simona); nella C-gen-4 nessuno.
- La regola di selezione è in §3.3c.

### 3.3c Regola di selezione dalla riserva (aggiunta l'11 novembre, 15:46, prima di qualsiasi inferenza)
- **Riserva.** Il generatore produce una riserva ordinata di 400 passaggi (100 per tipo di attributo). In ogni tipo i tre schemi di posizione ruotano, e in ogni strato tipo × schema ruotano i generi e i bilanciamenti binari. La riserva della prova ha 16 passaggi a parte.
- **Stessi passaggi per tutti.** La selezione usa insieme i tokenizer dei 4 modelli. Ne esce un solo insieme di 200 passaggi, lo stesso per tutti i modelli e tutti i metodi.
- **Otto versioni.** Un passaggio entra solo se tutte le sue otto versioni (4 famiglie × B/C) superano tutti i controlli di §3.3. Sono compresi la tolleranza di 3 token fra B e C e i controlli sul testo ricevuto da ogni modello.
- **Quote fisse.** Si prendono i primi passaggi validi nell'ordine della riserva, entro quote fissate ora per strato (tipo di attributo × schema di posizione):
  - anno: 17, 17, 16;
  - numero: 17, 16, 17;
  - luogo: 16, 17, 17;
  - persona: 17, 17, 16.

  Sono 50 per tipo. In ogni famiglia le posizioni si dividono 67, 67 e 66. Se uno strato non si riempie, la selezione lo dice e non si compensa con altri strati: si torna al generatore.
- **Prova.** Si prendono i primi 10 passaggi validi della riserva della prova.
- **Si salvano prima delle inferenze:**
  - l'ordine dei candidati;
  - l'esito di ciascuno (scelto, escluso o valido con quota piena) e i motivi di esclusione;
  - le revisioni e le impronte dei tokenizer (vocabolario e chat template);
  - lo sha256 dell'insieme finale e dei suoi ID;
  - lo sha256 di `righe_C.json`.
- **Revisione manuale.** Le 20 coppie di §3.4 si estraggono dai 200 passaggi effettivamente selezionati.
- **Insieme naturale, quote.** Se una coppia naturale non passa un controllo (testo ricevuto, limite di token, risposta residua in RIM-nat, «or» in DUE-nat), si passa al candidato successivo nell'ordine fissato dal seme, fino alla quota. Se i candidati finiscono prima, l'insieme si dichiara incompleto nel rapporto, con il numero raggiunto per famiglia. Non si allentano i controlli.
- **Registro del naturale (C-sel-4).** Per ogni domanda di SQuAD dev si salva in `registro_candidati_naturale.json`: la fase (filtro iniziale o candidati nell'ordine fissato), l'esito per RIM-nat e per DUE-nat (scelto, escluso, non valutato) e il controllo esatto non superato. Per il testo ricevuto dai modelli si registrano i problemi trovati (modello, lato, motivo).
- **Verifica indipendente (C-sel-4).** `verifica_selezione_v2.py` non importa né il generatore né lo script di selezione. Rilegge il testo con regole proprie:
  - sintetico: occorrenze dei valori, «or», marcatori di riserva, parole, cronologia, B e C uguali fuori dal blocco; per famiglia, la frase con il solo valore (RIM), «v1 or v2» e lo scambio «or»/«and» (DUE), due frasi parallele con fonti o gruppi diversi, uguali tolti nome e valore (CONF, LOG), la disgiunzione identica in B e C (LOG);
  - la regola «primi validi» ricalcolata dai registri, il testo scelto uguale alla variante della riserva, le quote, le intersezioni fra prova e definitivo;
  - naturale: riferimenti coerenti, C fatto di frasi intere di B, almeno 3 frasi vere, nessun segno di taglio, nessuna risposta residua, C di DUE-nat uguale a B con la sola aggiunta «or distrattore», distrattore plausibile, confronto con SQuAD dev, registro completo.

  Ogni controllo non superato è un errore e fa uscire lo script con codice 1. Non verifica i conteggi dei token (servono i tokenizer) né l'esclusione delle 400 domande di HM0 (serve il train di SQuAD).

### 3.4 Revisione manuale
Prima del completo Simona legge 20 coppie estratte a caso dai passaggi selezionati, 5 per famiglia. Conferma tre cose:
- che B determini la risposta e C no;
- che in CONF le due fonti siano davvero alla pari;
- che in LOG la disgiunzione abbia lo stesso ruolo in B e in C.

Se una coppia è sbagliata si corregge il template, si rigenera tutto e si ripete l'estrazione.

### 3.5 Insieme descrittivo: passaggi naturali (SQuAD 2.0 dev)
- **Fonte.** Domande con risposta di SQuAD 2.0 dev, con risposta breve di tipo data, numero o nome.
  - Si escludono le 400 domande del controllo positivo di M2 e M3 e i loro paragrafi.
  - Gli ID si fissano con un sha256.
- **Validazione dei riferimenti (C-sel-4).** Le risposte di riferimento di SQuAD devono dire la stessa cosa. La canonica è la più breve fra quelle del tipo; ogni altra deve contenerla o esserne contenuta, dopo la normalizzazione SQuAD («Rankine» e «Rankine cycle» sì; «1864» e «Battle of Cedar Creek» no). Per anni e numeri nessuna risposta può portare un altro valore del tipo («270,000» e «121,200» no). Una domanda sull'anno vuole un anno, una «how many/much» un numero. Non si corregge nessuna etichetta, né a maggioranza né a mano: la domanda si esclude, con il motivo nel registro, e si passa al candidato successivo.
- **Frasi (C-sel-4).** Un confine di frase è un segno di fine frase seguito da spazio e maiuscola, tranne dopo un'iniziale («Arthur H. Compton»), un'abbreviazione di un elenco fisso o dentro una parentesi o virgolette non chiuse. Le «3 frasi» di RIM-nat si contano con questa divisione.
- **RIM-nat (200 coppie).** In C si tolgono tutte le frasi che permettono ancora di rispondere:
  - ogni frase che contiene una qualsiasi delle risposte di riferimento di SQuAD, dopo la normalizzazione SQuAD;
  - per date e numeri, anche le forme equivalenti (in cifre e in lettere, con e senza unità);
  - ogni frase che contiene il nome dell'attributo insieme a un valore dello stesso tipo, se il controllo automatico non esclude che porti alla risposta.

  Si scartano le coppie in cui, dopo la rimozione, il paragrafo ha meno di 3 frasi, e quelle in cui il testo C mostra segni di taglio: parentesi o virgolette non bilanciate, frasi che non cominciano con la maiuscola o non finiscono con un segno di fine frase (C-sel-4). Si scartano anche quelle in cui il risolutore non può escludere un'altra via, per esempio una risposta ricavabile da un calcolo. Una parte di rischio resta (parafrasi, calcoli impliciti), quindi:
  - Simona legge 30 coppie RIM-nat estratte a caso;
  - la quota di coppie in cui C permette ancora di rispondere si riporta.
- **DUE-nat (200 coppie).** In C lo span della risposta diventa «span or distrattore» (l'ordine è estratto con un seme fisso). Lo span deve comparire una volta sola nel paragrafo e la risposta in una sola frase; altrimenti la coppia si scarta.
  - **Distrattore (C-sel-4).** È la risposta coerente di un'altra domanda di SQuAD dev della stessa classe: persona (who), luogo (where), «what/which <nome>» con lo stesso nome, anno, numero. Deve essere plausibile: anni entro 50 anni dalla risposta, numeri fra metà e doppio (fino a 20, entro 5). Non deve comparire nel paragrafo né coincidere con una risposta. Si cerca prima nello stesso articolo; per persone, luoghi, anni e numeri, se l'articolo non ne ha, in tutto SQuAD dev. Se la classe della domanda non si riconosce («What is …?») o non c'è un distrattore plausibile, la coppia si scarta. Nella selezione C-sel-3 il distrattore era solo dello stesso tipo, e spesso implausibile («Raghuram Rajan or the Seine»).
  - Simona legge anche 20 coppie DUE-nat estratte a caso (plausibilità del distrattore).
- **Perché è descrittivo.** Gli articoli di Wikipedia sono probabilmente nella memoria dei modelli. Una risposta su C può quindi venire dalla memoria. Questo è proprio un'allucinazione rispetto al contesto, ma confonde il confronto con l'insieme sintetico. Le modifiche automatiche su testo naturale sono anche meno controllabili, e la lunghezza non si appaia esattamente.

## 4. Prompt e risposte
- **Modelli:** gli stessi del Test U2 e del Test M, alle stesse revisioni.
  - Qwen3-8B (`enable_thinking=False`), Mistral-Nemo-Instruct-2407, OLMo-2-1124-7B-Instruct e Llama-3.1-8B-Instruct (0e9e39f2).
  - bf16, attention eager, chat template di ogni modello.
- **Istruzione principale, neutra** (come la P−S del Test U2): «Answer the question using the passage. Reply with a short answer or UNKNOWN.» UNKNOWN è offerto come opzione, senza spiegare quando usarlo.
- **Generazione:** greedy, fino a 32 token, così c'è spazio per attribuire i valori alle fonti.
- **Classificazione della risposta.** Le regole sono scritte prima dei dati, con normalizzazione SQuAD, e si fissano dopo la prova (§8).

| Categoria | Dove | Supportata dal contesto? |
|---|---|---|
| **corretta**: coincide con il valore bersaglio | B | sì |
| **errata**: un valore diverso dal bersaglio, non un'astensione | B | no |
| **astensione**: UNKNOWN o una formula di non risposta da un elenco fisso | B e C | in C sì; in B no (risposta mancata, si conta a parte) |
| **alternative**: riporta i due valori come possibilità («1821 or 1823») | C di DUE, CONF, LOG | sì |
| **attribuite**: attribuisce ciascun valore alla sua fonte o al suo ramo («the archive says 1821, the register 1823») | C di CONF e LOG | sì |
| **entrambi affermati**: afferma che i due valori sono veri insieme («founded in 1821 and 1823»); possibile perché gli attributi hanno un solo valore (§3.1) | C di DUE, CONF, LOG | no |
| **qualificata**: un solo valore con una riserva esplicita («maybe 1821», «probably 1821», «possibly», «likely», «I think», «it seems»), da un elenco fisso di marcatori | B e C | non si decide: esclusa da HC4 principale e riportata a parte |
| **un valore del contesto**: sceglie uno solo dei valori presenti nel passaggio | C | no |
| **valore assente dal contesto**: un valore che non compare nel passaggio | B e C | no |
| **altro**: tutto ciò che le regole non classificano | B e C | escluso dalle analisi sul supporto |

- **Risposta non supportata (allucinazione con contesto):** «errata», «entrambi affermati», «un valore del contesto» e «valore assente dal contesto».
- **Esclusioni da HC4 principale:** «astensione», «qualificata» e «altro». Si contano e si riportano per modello, famiglia, B e C.
- **Ordine delle regole:** prima l'astensione, poi le alternative e le attribuzioni, poi la qualificazione, poi gli altri casi. Una risposta come «1821 or maybe 1823» è quindi «alternative», non «qualificata».
- **Controllo del classificatore.** Dopo il completo si estraggono 100 risposte, stratificate per categoria, e Simona le classifica senza vedere l'etichetta automatica. La concordanza si riporta. Se è sotto 0.90, gli esiti di HC4 si accompagnano a questa avvertenza nel resoconto.

## 5. Metodi
Sono gli stessi del Test M, negli stessi ambienti (`env_m1`, `env_sirin`, `env_obeso`). Nessuno si riaddestra.

| Metodo | Come si applica qui | Che cosa legge |
|---|---|---|
| **Riferimento p(UNKNOWN)** | primo token, come nel Test U2, ricalcolato in ogni ambiente | il prompt e il primo token |
| **M1 LM-Polygraph** (MSP, Perplexity, Mean Token Entropy, Semantic Entropy) | sulla risposta generata, come nel Test M; p(True) solo dove ha passato HM0 (OLMo) | la risposta |
| **M2 sonda SIRIN** (originale e M2-senzaℓ2) | **le sonde salvate dal completo del notebook B**, ricaricate con il controllo ≤1e-6; contesto = passaggio, domanda = domanda | solo il prompt |
| **M3 giudice di answerability** (Qwen3-4B zero-shot, prompt SIRIN) | passaggio come contesto, domanda come domanda; un punteggio per prompt, uguale per tutti i modelli | solo il prompt, con un modello diverso; HC2 e HC4 si riportano per ciascun modello generatore |
| **M4 sonde Obeso** (lineare e LoRA, solo Llama) | massimo per token sulla risposta generata da Llama | la risposta |

La colonna «che cosa legge» conta per HC4. M2 e M3 non vedono la risposta. Entro B o entro C, la loro AUROC dice se il punteggio del prompt prevede la risposta che il modello darà, non se riconoscono una risposta già data. Nel resoconto si legge così.

## 6. Misure

### 6.1 Sulle coppie
Per ogni metodo, modello e famiglia:
- **W(C > B)**: la quota di coppie in cui il punteggio è più alto su C che su B, con i pareggi a mezzo punto, mediata per passaggio. IC al 95% su 2000 ricampionamenti dei passaggi (seme 20261108).
- **ΔW** rispetto a p(UNKNOWN) dello stesso ambiente, sulle coppie comuni, ricampionando lo stesso passaggio nei due bracci, con il margine 1 − W(riferimento).
- **Per M3** il punteggio è uno solo per prompt, ma i riferimenti sono quattro. Si calcolano quindi quattro ΔW, uno per il p(UNKNOWN) di ciascun modello generatore (ricalcolato in `env_sirin`).
- **Comportamento** (descrittivo): le quote delle categorie di §4 per modello, famiglia, B e C, e l'accuratezza su B per modello e per famiglia (§7, HC0-set).

**Analisi principale:** l'insieme sintetico, con le tre famiglie di indeterminatezza (DUE, CONF, LOG) insieme, cioè 600 coppie su 200 passaggi. RIM fa da controllo di dominio, separato.

### 6.2 Sul supporto della risposta (HC4)
- **Entro C, fra le risposte non astenute:** AUROC del punteggio fra risposte non supportate e risposte supportate, sui C delle famiglie DUE, CONF e LOG insieme.
  - Supportate: «alternative» e «attribuite». Non supportate: «entrambi affermati», «un valore del contesto», «valore assente dal contesto».
  - **Escluse:** astensioni, risposte qualificate e «altro».
  - **Perché si escludono le astensioni.** p(UNKNOWN) si calcola prima della generazione, quindi non c'è automaticamente una fuga dell'etichetta. Ma un punteggio che prevede bene l'astensione otterrebbe un buon risultato anche senza distinguere il supporto delle risposte date. L'esclusione separa la discriminazione del supporto dalla semplice previsione dell'astensione.
  - **Che cosa si può concludere:** «il metodo discrimina il supporto fra le risposte non astenute». Non misura l'affidabilità complessiva del sistema, che dipende anche da quanto e quando il modello si astiene.
- **Entro B, fra le risposte non astenute:** AUROC fra risposte errate e risposte corrette, sulle quattro famiglie, con le stesse esclusioni. È la misura classica della rilevazione di allucinazioni.
- **Per ciascun modello generatore.** Le etichette dipendono dalle risposte del modello che genera. Per i metodi che girano sul modello stesso questo è già così. Per M3, che dà un punteggio per prompt uguale per tutti, l'AUROC si calcola e si riporta separatamente con le etichette di ciascuno dei 4 modelli.
- **Si riportano sempre:** per modello, famiglia, B e C, il numero di astensioni, di risposte qualificate, di «altro» e le numerosità rimaste per classe, con il numero di passaggi.
- **Numerosità minima (soglia operativa, fissata ora e non ridotta dopo i risultati):**
  - per ciascuna analisi, entro C ed entro B, almeno 30 risposte per classe;
  - queste risposte devono venire da almeno 15 passaggi diversi per classe;
  - sotto questi numeri l'analisi è NON VALUTABILE per quel modello, e i conteggi si riportano.
- **IC:** 2000 ricampionamenti dei passaggi. Tutte le risposte dello stesso passaggio entrano o escono insieme.
- **Descrittivo, con il limite scritto:**
  - entro C, con le astensioni incluse tra le risposte supportate;
  - AUROC fra risposte non supportate su C e risposte corrette su B, senza appaiamento;
  - lo stesso confronto C contro B con le astensioni incluse.

  Nei confronti C contro B un metodo può andare bene solo perché distingue C da B, senza riconoscere nulla della risposta. Nel confronto entro C con le astensioni, può andare bene solo perché prevede l'astensione. Per questo nessuno dei tre decide nulla.

## 7. Ipotesi da preregistrare (proposta)
- **HC0 (validità del metodo).** Si eredita dal Test M, senza ricalcolare: HM0 di ogni metodo, stimatore, sonda e modello.
  - Chi non l'ha passato è NON VALUTABILE anche qui, e il suo W è descrittivo.
  - Per M2 valgono gli HM0 del completo del notebook B, separati per M2 e M2-senzaℓ2.
- **HC0-set (descrittivo).** Si riporta l'accuratezza del modello su B, per modello e per famiglia.
  - La soglia operativa 0.80 serve solo da segnalazione: sotto, il resoconto avverte che il modello legge male i passaggi.
  - Non rende NON VALUTABILE nessun metodo. In particolare non tocca M3, che è un giudice indipendente dal modello che risponde.
- **HC-dom (controllo di dominio, su RIM).** Per M2 e M3: W su RIM ≥ 0.60 con limite inferiore > 0.5.
  - Non decide la valutabilità.
  - Dice se i metodi di answerability funzionano su questi passaggi sintetici.
  - Se non passa, il resoconto lo scrive prima di leggere le famiglie di indeterminatezza.
- **HC1 (il metodo riconosce l'indeterminatezza nel contesto).** Sulle 600 coppie DUE + CONF + LOG, W(C > B) > 0.5.
  - CONFERMATA se il limite inferiore è > 0.5 **e** W ≥ 0.60.
  - NON CONFERMATA se il limite superiore è ≤ 0.5.
  - Altrimenti NON CONCLUSIVA.
- **HC2 (il metodo fa meglio di p(UNKNOWN)).** Sulle stesse coppie, ΔW sulle coppie comuni.
  - CONFERMATA se il limite inferiore è > 0 **e** ΔW ≥ 0.05.
  - NON CONFERMATA se il limite superiore è ≤ 0.
  - Altrimenti NON CONCLUSIVA.
  - La soglia resta fissa anche se il margine è piccolo, come per Qwen nel Test M.
- **HC3 (assenza contro indeterminatezza, secondaria preregistrata).** Per ogni metodo valutabile, D = W(RIM) − W(DUE + CONF + LOG), sugli stessi passaggi, ricampionati insieme.
  - CONFERMATA se il limite inferiore è > 0 **e** D ≥ 0.10.
  - NON CONFERMATA se il limite superiore è ≤ 0.
  - Altrimenti NON CONCLUSIVA.
  - Se è confermata, il metodo riconosce l'informazione mancante meglio di quella indeterminata.
- **HC4 (il metodo discrimina il supporto fra le risposte non astenute).** Si valuta separatamente entro C ed entro B (§6.2), per ciascun modello generatore.
  - CONFERMATA se l'AUROC è ≥ 0.70 **e** il limite inferiore è > 0.5.
  - NON CONFERMATA se il limite superiore è ≤ 0.5.
  - Altrimenti NON CONCLUSIVA.
  - NON VALUTABILE sotto la numerosità minima.
  - Il confronto C contro B di §6.2 è descrittivo.
- **Copertura minima.** Come nel Test M: un esito si assegna solo con almeno il 95% di coppie valide. Sono 570 su 600 per HC1 e HC2, e 190 su 200 per RIM. Gli scarti si riportano per famiglia e per motivo.
- **Lettura per la libreria:**
  - «Il metodo X riconosce l'indeterminatezza nel contesto» solo con HC1 confermata in almeno 3 modelli su 4 valutabili;
  - la stessa regola vale per HC2, HC3 e HC4 (per HC4, separatamente entro C ed entro B, contando solo i modelli valutabili);
  - per HC4 la frase è «discrimina il supporto fra le risposte non astenute», mai «rileva le allucinazioni» senza qualificazione;
  - M3 è un solo giudice:
    - dà un esito unico per HC1 e HC3;
    - per HC2 ha quattro esiti, uno per ciascun riferimento p(UNKNOWN). Si leggono come quattro confronti dello stesso giudice, non come quattro repliche indipendenti: la frase è «M3 fa meglio del p(UNKNOWN) di n modelli su 4»;
    - per HC4 ha un esito per ciascun modello generatore, e la regola dei 3 su 4 si applica ai 4 generatori, con la stessa avvertenza;
  - M4 vale solo per Llama.
- **Per famiglia** (secondaria, IC non corretti): W, ΔW e HC1 per DUE, CONF e LOG separatamente, con la regola nominale dei 3 su 4, come nella nota M2 §3.
- **Formulazioni** come nel Test M:
  - HC0 superato e HC1 NON CONFERMATA: «funziona sul suo dominio ma non riconosce l'indeterminatezza nel contesto»;
  - HC1 NON CONCLUSIVA: «non ha superato il criterio HC1 in questo test».
- **Insieme naturale (§3.5):** le stesse misure, tutte descrittive.

## 8. Esecuzione e tempi
- **Un solo notebook** (`TestC_contesto_v1.ipynb`), costruito su due notebook esistenti:
  - il notebook A v8 per ambienti, impronte, ripresa, GPU registrata e ZIP;
  - il notebook B v4 per il caricamento delle sonde M2 con il controllo del ricaricamento.

  Le uscite vanno in `MyDrive/testC_parziali/<modalità>/`. Il generatore è uno script a parte. Il suo file di uscita entra nel notebook con l'sha256 fissato.
- **Dipendenza dal notebook B.** M2 entra solo se il completo di B ha salvato e ricaricato le sonde.
- **Prompt per modello:** 200 passaggi × 4 famiglie × 2 = 1600 sintetici, più 400 coppie naturali × 2 = 800. In tutto 2400 per modello, la metà delle righe del notebook A.
- **Ore di Colab (stima, A100):**
  - prova tecnica (Qwen, i 10 passaggi separati di §3.1, tutti i metodi): circa 1 ora con l'installazione degli ambienti;
  - completo sui 4 modelli: circa 4–5 ore. Il notebook A ha impiegato 6.5 ore per il doppio delle righe. Qui le risposte fino a 32 token allungano un po' M1, e M2 senza addestramento aggiunge circa 30–45 minuti di estrazione degli stati.
- **Ore di lavoro mio (stima, separate da Colab):**
  - protocollo definitivo: circa 1 ora;
  - generatore con risolutore, analizzatore inverso e controlli sui tokenizer: 5–6 ore;
  - notebook con le prove a secco: 1 giorno;
  - resoconto: 2–3 ore.
- **Prova obbligatoria** prima del completo:
  - installazione, formato delle risposte e ricaricamento delle sonde M2;
  - controlli del generatore ripetuti sul file usato;
  - classificazione delle risposte. Se la quota di «altro» supera il 10%, le regole di §4 si rivedono sui soli dati della prova e poi si fissano. La prova usa solo i suoi 10 passaggi, quindi le regole si fissano prima di vedere qualsiasi risposta sui 200 definitivi.

## 9. Scelte fissate (confermate da Simona l'11 novembre)
1. **Famiglie:** tutte e quattro (RIM, DUE, CONF, LOG), con RIM separata dall'analisi principale come controllo di dominio.
2. **Istruzione:** quella neutra di §4.
3. **«Entrambi affermati»:** non supportata, perché gli attributi bersaglio hanno un solo valore per definizione (§3.1).
4. **Numerosità minima di HC4:** 30 risposte e 15 passaggi per classe. È una soglia operativa e non si riduce dopo i risultati.
5. **Dimensione:** 200 passaggi nel completo, più i 10 passaggi separati della prova.
6. **Già confermate nella v2:** insieme sintetico principale, insieme naturale descrittivo, nessun riaddestramento, HC3 secondaria preregistrata.

## 10. Cosa non fa questo test
- **Non prova il recupero dei documenti.** Il passaggio è dato, non cercato. «RAG» qui vuol dire solo risposta con un contesto fornito.
- **Non valuta risposte lunghe.** Le risposte sono brevi, mentre M4 è nato per il testo lungo.
- **Non addestra nulla** sui passaggi e non sceglie soglie sulle coppie.
- **Non generalizza da solo a testi reali.** Usa solo l'inglese, entità inventate e template. La generalizzazione si legge solo dall'insieme naturale, che è descrittivo.
- **Il controllo della «or» in DUE è parziale** (§3.2). Solo LOG ha il controllo forte.
- **M2 e M3 leggono solo il prompt**, quindi HC4 per loro misura la previsione della risposta, non il riconoscimento di una risposta data.
- **HC4 riguarda solo le risposte non astenute.** Non misura l'affidabilità complessiva del sistema.
- **Non sostituisce la replica** del vantaggio di M4-LoRA sulla famiglia AND, che resta un test separato.
