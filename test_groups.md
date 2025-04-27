# Piano di Test Manuale: Funzionalità Gruppi

**Ambiente di Test:**

*   Assicurati di avere accesso come **Docente** e come **Studente** (o di poter creare nuovi studenti).
*   Utilizza i frontend specifici: `frontend-teacher`, `frontend-lessons`, `frontend-student`.
*   Abbi a disposizione dei contenuti pre-esistenti: Template Quiz, Template Percorsi, Lezioni, Ricompense.

---

**A. Test Funzionalità Docente (`frontend-teacher`, `frontend-lessons`)**

**A1: Gestione Gruppi (CRUD)**

*   **[PASS] A1.1 Creazione Gruppo (Successo):**
    *   **Passi:** Accedi come Docente -> Vai alla sezione Gruppi -> Clicca "Crea Nuovo Gruppo" -> Inserisci un nome univoco e una descrizione (opzionale) -> Salva.
    *   **Risultato Atteso:** Il gruppo viene creato e appare nell'elenco dei gruppi. Viene mostrato un messaggio di successo.
*   **[PASS] A1.2 Creazione Gruppo (Nome Duplicato):**
    *   **Passi:** Tenta di creare un nuovo gruppo usando un nome già esistente per un gruppo dello stesso docente.
    *   **Risultato Atteso:** La creazione fallisce. Viene mostrato un messaggio di errore specifico (es. "Nome gruppo già in uso").
*   **[PASS] A1.3 Visualizzazione Elenco Gruppi:**
    *   **Passi:** Accedi come Docente -> Vai alla sezione Gruppi.
    *   **Risultato Atteso:** Viene visualizzato l'elenco di tutti i gruppi creati dal docente, con nome ed eventualmente numero membri/descrizione.
*   **[PASS] A1.4 Modifica Gruppo:**
    *   **Passi:** Dall'elenco gruppi, seleziona un gruppo -> Clicca "Modifica" -> Cambia il nome e/o la descrizione -> Salva.
    *   **Risultato Atteso:** Le modifiche vengono salvate e riflesse nell'elenco e nei dettagli del gruppo.
*   **[PASS] A1.5 Eliminazione Gruppo:**
    *   **Passi:** Dall'elenco gruppi, seleziona un gruppo -> Clicca "Elimina" -> Conferma l'eliminazione.
    *   **Risultato Atteso:** Il gruppo viene eliminato e non appare più nell'elenco. (Verifica se ci sono vincoli sull'eliminazione di gruppi con membri o assegnazioni attive).

**A2: Gestione Membri Gruppo**

*   **[PASS] A2.1 Aggiunta Membro:**
    *   **Passi:** Vai alla vista Dettaglio di un gruppo -> Sezione Membri -> Clicca "Aggiungi Membro" -> Seleziona uno studente esistente (non ancora membro) -> Conferma.
    *   **Risultato Atteso:** Lo studente viene aggiunto all'elenco dei membri del gruppo. Il contatore membri (se presente) si aggiorna.
*   **[PASS] A2.2 Rimozione Membro:**
    *   **Passi:** Vai alla vista Dettaglio di un gruppo -> Sezione Membri -> Seleziona uno studente membro -> Clicca "Rimuovi Membro" -> Conferma.
    *   **Risultato Atteso:** Lo studente viene rimosso dall'elenco dei membri del gruppo.

**A3: Gestione Token Registrazione**

*   **[PASS] A3.1 Generazione Token:**
    *   **Passi:** Vai alla vista Dettaglio di un gruppo -> Sezione Token Registrazione -> Clicca "Genera Token".
    *   **Risultato Atteso:** Viene generato e visualizzato un **link di registrazione univoco** (contenente un token UUID). Il pulsante cambia in "Elimina Link/Token".
*   **[PASS] A3.2 Revoca Token:**
    *   **Passi:** Vai alla vista Dettaglio di un gruppo dove è attivo un link/token -> Clicca "Elimina Link/Token".
    *   **Risultato Atteso:** Il token UUID associato viene eliminato. Non è più possibile registrarsi con quel link. L'interfaccia mostra che non c'è un link/token attivo.

**A4: Assegnazione Contenuti a Gruppi**

*   **[PASS] A4.1 Assegnazione Quiz:**
    *   **Passi:** Vai alla sezione Assegnazioni (o gestione Quiz) -> Seleziona un Template Quiz -> Scegli "Assegna" -> Nella destinazione, seleziona l'opzione "Gruppo" -> Scegli il gruppo desiderato -> Conferma.
    *   **Risultato Atteso:** Il Quiz viene assegnato al gruppo. Verifica che l'assegnazione sia visibile (es. in una lista di assegnazioni del quiz o del gruppo).
*   **[PASS] A4.2 Assegnazione Percorso:**
    *   **Passi:** Simile ad A4.1, ma selezionando un Template Percorso.
    *   **Risultato Atteso:** Il Percorso viene assegnato al gruppo.
*   **[PASS] A4.3 Assegnazione Lezione (`frontend-lessons`):**
    *   **Passi:** Accedi al frontend delle Lezioni come Docente -> Vai alla gestione Lezioni -> Seleziona una Lezione -> Scegli "Assegna" -> Seleziona "Gruppo" -> Scegli il gruppo -> Conferma.
    *   **Risultato Atteso:** La Lezione viene assegnata al gruppo.

**A5: Revoca Assegnazione Contenuti a Gruppi**

*   **[SALTATO - API MANCANTE] A5.1 Revoca Quiz/Percorso/Lezione:**
    *   **Passi:** Trova l'assegnazione del contenuto al gruppo (potrebbe essere nella vista del contenuto o nella vista del gruppo) -> Seleziona l'opzione "Revoca Assegnazione" (o simile) -> Conferma.
    *   **Risultato Atteso:** L'assegnazione al gruppo viene rimossa.

**A6: Disponibilità Ricompense per Gruppi**

*   **[PASS] A6.1 Rendere Disponibile Ricompensa:**
    *   **Passi:** Vai alla gestione Ricompense -> Seleziona una Ricompensa -> Scegli "Rendi Disponibile" (o gestione disponibilità) -> Seleziona "Gruppo" -> Scegli il gruppo -> Conferma.
    *   **Risultato Atteso:** La Ricompensa diventa disponibile per tutti i membri del gruppo scelto.
*   **A6.2 Revocare Disponibilità Ricompensa:**
    *   **Passi:** Trova la regola di disponibilità della ricompensa per il gruppo -> Seleziona "Revoca Disponibilità" (o simile) -> Conferma.
    *   **Risultato Atteso:** La Ricompensa non è più disponibile per il gruppo (a meno che non sia disponibile anche individualmente o tramite altri gruppi).

---

**B. Test Funzionalità Studente (`frontend-student`)**

**B1: Registrazione tramite Token**

*   **B1.1 Registrazione (Successo):**
    *   **Prerequisiti:** Un docente ha creato un gruppo e generato un **link** di registrazione dalla pagina di dettaglio di quel gruppo.
    *   **Passi:** Apri il **link di registrazione** fornito -> Compila i dati richiesti per il nuovo studente (nome, cognome, PIN, ecc.) -> Invia il form.
    *   **Risultato Atteso:** L'account studente viene creato, lo studente viene automaticamente **aggiunto come membro del gruppo da cui è stato generato il link** e associato al docente proprietario. Lo studente può effettuare il login.
*   **B1.2 Registrazione (Token Invalido/Scaduto):**
    *   **Passi:** Tenta di accedere alla pagina di registrazione usando un link con un token UUID inesistente, già usato o eliminato dal docente.
    *   **Risultato Atteso:** Viene mostrato un messaggio di errore indicando che il token non è valido o non trovato. La registrazione non è permessa.

**B2: Visualizzazione Contenuti Assegnati via Gruppo**

*   **B2.1 Visualizzazione Quiz/Percorsi/Lezioni:**
    *   **Prerequisiti:** Uno studente è membro di un gruppo a cui sono stati assegnati Quiz, Percorsi e Lezioni.
    *   **Passi:** Accedi come Studente -> Naviga nelle sezioni relative a Quiz, Percorsi e Lezioni (Dashboard, elenchi specifici).
    *   **Risultato Atteso:** Lo studente vede i Quiz, Percorsi e Lezioni che gli sono stati assegnati *tramite* il gruppo, oltre a quelli assegnati individualmente.
*   **B2.2 Verifica Post-Revoca Assegnazione:**
    *   **Prerequisiti:** Il docente revoca l'assegnazione di un Quiz/Percorso/Lezione da un gruppo di cui lo studente è membro.
    *   **Passi:** Accedi come Studente (o aggiorna la pagina se già loggato) -> Controlla l'elenco dei contenuti pertinenti.
    *   **Risultato Atteso:** Il contenuto la cui assegnazione è stata revocata dal gruppo non è più visibile (a meno che non sia ancora assegnato individualmente o tramite un altro gruppo).

**B3: Visualizzazione Ricompense Disponibili via Gruppo**

*   **B3.1 Visualizzazione Ricompense:**
    *   **Prerequisiti:** Uno studente è membro di un gruppo per cui una Ricompensa è stata resa disponibile.
    *   **Passi:** Accedi come Studente -> Vai allo Shop/Negozio Ricompense.
    *   **Risultato Atteso:** Lo studente vede la Ricompensa resa disponibile tramite il gruppo, oltre a quelle disponibili individualmente o per tutti.
*   **B3.2 Verifica Post-Revoca Disponibilità:**
    *   **Prerequisiti:** Il docente revoca la disponibilità di una Ricompensa da un gruppo di cui lo studente è membro.
    *   **Passi:** Accedi come Studente (o aggiorna la pagina) -> Vai allo Shop.
    *   **Risultato Atteso:** La Ricompensa la cui disponibilità è stata revocata dal gruppo non è più visibile nello shop (salvo altre regole di disponibilità).

**B4: Interazione con Contenuti/Ricompense via Gruppo**

*   **B4.1 Svolgimento/Progresso/Accesso:**
    *   **Passi:** Come studente, tenta di iniziare un Quiz, progredire in un Percorso o accedere a una Lezione assegnati tramite gruppo.
    *   **Risultato Atteso:** Lo studente può interagire normalmente con il contenuto.
*   **B4.2 Acquisto Ricompensa:**
    *   **Passi:** Come studente, tenta di acquistare una Ricompensa disponibile tramite gruppo (assicurati che abbia punti sufficienti).
    *   **Risultato Atteso:** L'acquisto viene completato con successo.

---

**C. Test di Interazione e Casi Limite**

*   **C1: Nuovo Membro e Assegnazioni Pregresse:**
    *   **Passi:** Assegna Contenuto X a Gruppo A -> Aggiungi Studente B (nuovo al gruppo) a Gruppo A -> Login come Studente B.
    *   **Risultato Atteso:** Studente B vede immediatamente il Contenuto X.
*   **C2: Rimozione Membro e Assegnazioni Attive:**
    *   **Passi:** Assicurati che Studente B sia in Gruppo A e veda Contenuto X (assegnato a Gruppo A) -> Rimuovi Studente B da Gruppo A -> Login come Studente B.
    *   **Risultato Atteso:** Studente B *non* vede più Contenuto X (a meno che non sia assegnato anche individualmente).
*   **C3: Assegnazione Mista (Individuale + Gruppo):**
    *   **Passi:** Assegna Quiz X a Studente B individualmente -> Assegna Quiz Y a Gruppo A (Studente B è membro) -> Login come Studente B.
    *   **Risultato Atteso:** Studente B vede sia Quiz X che Quiz Y.
    *   **Passi:** Revoca assegnazione Quiz Y da Gruppo A -> Studente B aggiorna la pagina.
    *   **Risultato Atteso:** Studente B vede solo Quiz X.
    *   **Passi:** Rimuovi Studente B da Gruppo A (Quiz Y è ancora assegnato a Gruppo A) -> Studente B aggiorna la pagina.
    *   **Risultato Atteso:** Studente B vede solo Quiz X.

---

Questi test dovrebbero coprire la maggior parte delle funzionalità introdotte. Ricorda di adattarli leggermente in base all'interfaccia utente specifica e ai comportamenti implementati (es. messaggi di conferma, gestione errori).