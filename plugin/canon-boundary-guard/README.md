# Canon Boundary Guard — plugin personale per ChatGPT

Conversione documentale di [Canon Boundary Guard for GPT Projects](https://github.com/xxyoudeadpunkxx/canon-boundary-guard-for-gpt-project), di XxYouDeaDPunKxX. Versione del pacchetto: **0.1.1**. Versione del protocollo originale: **1.1**, invariata.

## Importazione privata

In ChatGPT web, aprire **Plugin → Crea app**, scegliere lo ZIP del plugin e completare **Aggiungi plugin**. Questo è il percorso osservato nell'account durante la preparazione; non è la creazione di un'app MCP. Dopo l'importazione, aprire una nuova conversazione con il plugin disponibile.

Il pacchetto richiede che la postura completa sia attiva dall'inizio, prima della prima risposta sostanziale. La descrizione della skill espone questo requisito e l'invocazione implicita è consentita. Non è previsto un comando manuale di attivazione.

**Limite della verifica:** questo archivio è stato preparato e controllato localmente. L'importazione e l'attivazione implicita nella prima risposta di ChatGPT devono ancora essere provate nell'account. Il caricamento delle skill è gestito da ChatGPT: una descrizione non costituisce un hook tecnico che ne garantisca l'esecuzione. Se il bootstrap non avviene prima della prima risposta sostanziale, il requisito di avvio non è soddisfatto.

## Cosa contiene

- `plugin.json`: manifest portabile con metadati OpenAI.
- `.codex-plugin/plugin.json`: manifest di compatibilità con la stessa identità.
- `skills/canon-boundary-guard-gpt-project/`: skill nativa, istruzioni originali, cinque riferimenti, due schemi e tre script sincronizzati con il bundle sorgente.
- `LICENSE`: licenza originale CC BY-SA 4.0.

La skill conserva nome e testo originale. Le sole modifiche alla skill sono il richiamo all'avvio nella descrizione e la sezione **Native plugin binding**, che collega i vecchi percorsi del bundle alle risorse installate. Le istruzioni di progetto sono incluse integralmente e devono essere lette nel bootstrap. Riferimenti, schemi, script e istruzioni di progetto sono copie byte per byte del bundle sorgente aggiornato.

La versione 0.1.1 include le stesse correzioni applicate ai sorgenti: gestione coerente degli interi JSON nel validatore, controllo della sequenza del delta anche per `1.0`, esclusione delle intestazioni nei blocchi di codice, selezione delle intestazioni effettive e soglia corretta per le sezioni di dieci parole. Gli schemi e le regole del protocollo restano invariati.

La conversione rende la postura applicabile anche alle conversazioni ChatGPT fuori dai Projects. Le funzioni specifiche dei Projects continuano a indicare quelle superfici reali. I percorsi `/mnt/data` conservano il significato originale.

Le regole di stato, recupero, gate, prova di lettura, approvazione e le quattro etichette restano quelle del progetto. Installare il plugin non dichiara automaticamente un nuovo stato e non autorizza reset o ricostruzioni. Gli script restano controlli meccanici facoltativi secondo le condizioni originali.

## Verifica dopo l'importazione

In una nuova conversazione, con il plugin disponibile, inviare un normale primo messaggio senza nominarlo. Verificare che ChatGPT carichi la skill, legga le istruzioni e i riferimenti obbligatori e svolga lo Status Check prima dell'output sostanziale. Controllare poi che applichi le condizioni originali quando mancano fonti o stato valido e quando un risultato richiede persistenza. L'assenza di stato non va risolta dichiarando automaticamente una nuova installazione.

Questi controlli verificano il requisito originale; non introducono un'attivazione in fasi.

## Fonti del formato

- [Formato dei plugin](https://developers.openai.com/plugins/build/plugins)
- [Caricamento delle skill](https://developers.openai.com/plugins/concepts/skills)
- [Plugin in ChatGPT web](https://learn.chatgpt.com/docs/plugins?surface=web)
- [Controlli sui pacchetti](https://developers.openai.com/plugins/deploy/submission-errors)

## Attribuzione e modifiche

Autore del progetto originale: **XxYouDeaDPunKxX**. Sorgente: repository collegato sopra. Licenza: **Creative Commons Attribution-ShareAlike 4.0 International**, testo integrale in `LICENSE` e [testo ufficiale della licenza](https://creativecommons.org/licenses/by-sa/4.0/).

Modifiche del 22 settembre 2026: manifest, disposizione nativa delle risorse, descrizione di avvio, sezione di collegamento nel `SKILL.md`, metadati della skill e questo README; correzioni di `validate_state.py` ed `extract_proof.py` condivise con il bundle sorgente. Nessuna riscrittura delle regole originali. Il pacchetto mantiene la stessa licenza.
