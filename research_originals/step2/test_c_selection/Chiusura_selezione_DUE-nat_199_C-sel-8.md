# Test C — Chiusura della selezione DUE-nat C-sel-8 a 199/200

**Data:** 12 novembre 2026  
**Ambito:** solo gestione del deficit di una coppia naturale DUE-nat. La verifica indipendente versione C-verifica-4 e l'audit semantico sono fasi separate, **non eseguite in questa chiusura**.

## Decisione

**Conservare 199 coppie DUE-nat su quota nominale 200 e dichiarare esplicitamente il deficit di una coppia**, secondo la previsione del protocollo riferita dall'autrice. Non aggiungere un esempio non ammesso; non allentare soglie, limiti token, regole C-nat-7 o vincoli di provenienza e plausibilità del distrattore. Questa è una **chiusura della numerosità della selezione**; non costituisce approvazione finale del dataset o della revisione semantica.

## Controlli effettuati sulla selezione disponibile

Fonte: ZIP `selezione_C-sel-8-20261112T103930Z-1-001.zip` caricato in conversazione. File interni `dati/righe_C.json`, `dati/registro_candidati_naturale.json`, `dati/rapporto_selezione.json`, `manifest_selezione.json`.

- **DUE-nat:** 199 coppie distinte, ciascuna con un record B e uno C (398 righe). Nessun `pair_key` duplicato o incompleto.
- **RIM-nat:** 200 coppie distinte, ciascuna B/C (400 righe).
- **Sintetico definitivo:** 200 coppie B/C per ognuna delle 4 famiglie (1.600 righe). **Sintetico prova:** 10 coppie B/C per ciascuna famiglia (80 righe).
- **Hash dei dati:** tutti gli 8 SHA-256 dei file elencati in `manifest_selezione.json` coincidono con il contenuto effettivo del pacchetto esaminato. Questo controlla la **coerenza interna**; **non** certifica la provenienza storica né l'autenticità indipendente dello ZIP.
- **Selezione:** registro di 11.873 domande SQuAD validation; le uscite riportano 199 DUE-nat e 200 RIM-nat. Non sono stati consultati esiti d'inferenza per modificare la selezione.

SHA-256 dello ZIP esterno ricevuto: `cff43d328cc0e3754a791fd94a77566587f612d94baf3842f89e9ed7058069b4`  
SHA-256 dell'archivio interno `testC_selezione.zip`: `aaad5c5e6150e2c29b16220fa26fa895d8a7b2bb1688800011c3b8cdbaf4d21d`

## Otto scarti DUE-nat dovuti al controllo del testo

Il registro consente di identificare **8** scarti specifici. **Tre** violano il limite SIRIN di 512 token per uno o più modelli, quindi non sono recuperabili mantenendo il limite. **Cinque** mostrano il messaggio «passaggio o domanda non intatti nel prompt di risposta» per Llama: **non sono stati dimostrati falsi scarti** con un test di tokenizzazione sui cinque testi originali; restano esclusi.

| ID SQuAD | Titolo | Esito documentato | Decisione |
|---|---|---|---|
| `5726b929f1498d1400e8e8ea` | European_Union_law | SIRIN oltre 512 (Llama 680, Mistral 673, OLMo 656, Qwen 674 in B) | Escludere |
| `5727e6cbff5b5019007d97ee` | Economic_inequality | SIRIN oltre 512 (Llama 528, Mistral 526, Qwen 535 in B) | Escludere |
| `5729d36b1d04691400779607` | Economic_inequality | SIRIN oltre 512 (Llama 533, Mistral 532, Qwen 542 in B) | Escludere |
| `56de52614396321400ee27fd` | Normans | Llama: controllo integrità B/C non superato | Escludere, non certificato falso positivo |
| `57283f014b864d19001647eb` | University_of_Chicago | Llama: controllo integrità B/C non superato | Escludere, non certificato falso positivo |
| `572f567cb2c2fd1400568040` | Rhine | Llama: controllo integrità B/C non superato | Escludere, non certificato falso positivo |
| `572fe393947a6a140053cdbb` | Rhine | Llama: controllo integrità B/C non superato | Escludere, non certificato falso positivo |
| `572fd8efb2c2fd14005684fc` | Scottish_Parliament | Llama: controllo integrità B/C non superato | Escludere, non certificato falso positivo |

Il codice C-sel-8 già disabilita `clean_up_tokenization_spaces` durante la decodifica letterale del prompt. Nonostante ciò, per questi cinque casi Llama segnala ancora un disallineamento. Senza riproduzione sui tokenizer reali e confronto carattere per carattere tra prompt originale e decodificato, **non è giustificato** modificare il controllo di integrità o riammettere quei casi.

## Cosa non viene dichiarato

- **Non** si dichiara 200/200: il dato corretto è 199/200.
- **Non** si dichiara conclusa la verifica indipendente: il verificatore incluso accetta C-sel-7 e rifiuta C-sel-8 per versione attesa; tale lavoro è **rinviato**, senza alterare il suo risultato.
- **Non** si dichiara approvata la qualità semantica dei 199 casi: è distinta dalla verifica di conteggi e integrità e richiede revisione separata.
- **Non** si altera `manifest_selezione.json` dello ZIP originale: documenta correttamente l'esito originario, inclusa la quota nominale non raggiunta e l'errore dell'esecuzione della verifica indipendente.

## Formula trasparente da usare nel report scientifico

> La selezione naturale C-sel-8, con regole C-nat-7 congelate, ha prodotto 199/200 coppie DUE-nat e 200/200 coppie RIM-nat. Il deficit di una coppia DUE-nat è mantenuto e dichiarato; non sono stati allentati i criteri per raggiungere la quota. I controlli locali qui descritti verificano conteggi, abbinamenti B/C e coerenza interna degli hash, non la validità semantica né la provenienza indipendente. La verifica indipendente C-sel-8 resta un'attività separata.

**Prossima fase concordata:** soltanto dopo aver chiuso questa decisione, aggiornare il verificatore per gestire esplicitamente C-sel-8 e, se previsto dal protocollo, la numerosità dichiarata 199/200, senza abbassare gli altri controlli.
