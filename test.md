# Test Manuali Applicazione Educativa (Flusso Template)

## Frontend Docente (`http://localhost:5174`)

1.  **Login Docente:**
    *   Accedi con `teacher_test` / `password123`.
    *   Verifica: Accesso riuscito e reindirizzamento alla dashboard.

2.  **Creazione Template Quiz:**
    *   Vai alla sezione "Quiz Templates".
    *   Clicca "Crea Nuovo Template".
    *   Inserisci titolo (es. "Template Storia Romana") e descrizione.
    *   Imposta Punti e Soglia di default (opzionale).
    *   Salva Template.
    *   Verifica: Il template appare nella lista.

3.  **Modifica Template Quiz (Info Base):**
    *   Trova il template "Template Storia Romana" e clicca "Modifica".
    *   Modifica il titolo e la descrizione.
    *   Modifica Punti/Soglia.
    *   Salva Modifiche Template.
    *   Verifica: Torna alla lista, il titolo aggiornato è visibile. Rientrando in modifica, i dati sono corretti.

4.  **Modifica Template Quiz (Aggiunta Domanda Template MC - Single):**
    *   Entra in modifica del template "Template Storia Romana".
    *   Clicca "Aggiungi Domanda Template".
    *   Verifica: Navigazione alla vista `QuestionTemplateFormView`.
    *   Inserisci testo (es. "Chi fu il primo imperatore romano?"), seleziona tipo "Multiple Choice (Single Answer)".
    *   Imposta metadati (opzionale, es. punti specifici).
    *   Crea Domanda (Salva).
    *   Verifica: Reindirizzamento alla modifica del template quiz. La nuova domanda appare nella lista domande.

5.  **Modifica Domanda Template (Aggiunta/Modifica Opzioni MC-Single):**
    *   Entra in modifica del template "Template Storia Romana".
    *   Trova la domanda "Chi fu il primo imperatore romano?" e clicca "Modifica" (o l'icona corrispondente).
    *   Verifica: Navigazione alla vista `QuestionTemplateFormView` per quella domanda.
    *   Nella sezione "Opzioni Risposta Template":
        *   Aggiungi opzione "Giulio Cesare". Salva Opzione.
        *   Aggiungi opzione "Augusto". Salva Opzione.
        *   Aggiungi opzione "Nerone". Salva Opzione.
        *   Seleziona "Augusto" come corretta (radio button). Verifica: Il salvataggio avviene automaticamente o tramite pulsante "Salva Opzioni" dedicato.
        *   Ricarica la pagina (o torna indietro e rientra). Verifica: "Augusto" è selezionata.
        *   Seleziona "Giulio Cesare" come corretta. Verifica: Salvataggio automatico/manuale.
        *   Ricarica/Rientra. Verifica: "Giulio Cesare" è selezionata, "Augusto" non più.

6.  **Modifica Template Quiz (Aggiunta Domanda Template TF):**
    *   Torna alla modifica del template "Template Storia Romana".
    *   Clicca "Aggiungi Domanda Template".
    *   Inserisci testo (es. "Roma fu fondata nel 753 a.C.?"), seleziona tipo "True/False".
    *   Crea Domanda.
    *   Verifica: La domanda appare nella lista.

7.  **Modifica Domanda Template (Aggiunta/Modifica Opzioni TF):**
    *   Entra in modifica della domanda "Roma fu fondata...".
    *   Nella sezione opzioni:
        *   Aggiungi opzione "Vero".
        *   Aggiungi opzione "Falso".
        *   Seleziona "Vero" come corretta. Salva.
        *   Ricarica/Rientra. Verifica: "Vero" è selezionata.
        *   Cambia selezione a "Falso". Salva.
        *   Ricarica/Rientra. Verifica: "Falso" è selezionata.

8.  **Modifica Template Quiz (Aggiunta Domanda Template FillBlank):**
    *   Torna alla modifica del template "Template Storia Romana".
    *   Clicca "Aggiungi Domanda Template".
    *   Inserisci testo (es. "Il Colosseo si trova a ____.").
    *   Seleziona tipo "Fill in the Blank".
    *   Nei Metadati JSON, inserisci: `{"correct_answers": ["Roma", "roma"], "case_sensitive": false}`.
    *   Crea Domanda.
    *   Verifica: La domanda appare nella lista.

9.  **Modifica Template Quiz (Aggiunta Domanda Template OpenManual):**
    *   Torna alla modifica del template "Template Storia Romana".
    *   Clicca "Aggiungi Domanda Template".
    *   Inserisci testo (es. "Descrivi le guerre puniche.").
    *   Seleziona tipo "Open Answer (Manual Grading)".
    *   Nei Metadati JSON, inserisci (opzionale): `{"max_score": 5}`.
    *   Crea Domanda.
    *   Verifica: La domanda appare nella lista.

10. **Eliminazione Opzione Template:**
    *   Entra in modifica di una domanda template MC.
    *   Clicca "Elimina" su un'opzione.
    *   Verifica: L'opzione scompare (potrebbe richiedere conferma).

11. **Eliminazione Domanda Template:**
    *   Entra in modifica del template "Template Storia Romana".
    *   Trova una domanda nella lista.
    *   Clicca sul pulsante "Elimina".
    *   Conferma l'eliminazione.
    *   Verifica: La domanda scompare dalla lista e l'ordine delle successive viene aggiornato.

12. **Eliminazione Template Quiz:**
    *   Vai alla lista "Quiz Templates".
    *   Trova un template.
    *   Clicca "Elimina".
    *   Conferma l'eliminazione.
    *   Verifica: Il template scompare dalla lista.

13. **Creazione Template Percorso:**
    *   Vai alla sezione "Template Percorsi".
    *   Clicca "Crea Nuovo Template".
    *   Inserisci titolo (es. "Percorso Impero Romano") e descrizione.
    *   Imposta Punti (opzionale).
    *   Salva Template.
    *   Verifica: Reindirizzamento alla modifica del template percorso.

14. **Modifica Template Percorso (Aggiunta Quiz Template):**
    *   Nella vista di modifica del "Percorso Impero Romano":
    *   Seleziona "Template Storia Romana" dal dropdown "Aggiungi Quiz Template".
    *   Clicca "Aggiungi Template".
    *   Verifica: Il template quiz appare nella lista "Quiz Template nel Percorso".
    *   Aggiungi un altro template quiz (se ne hai creato un altro).

15. **Modifica Template Percorso (Rimozione Quiz Template):**
    *   Nella lista "Quiz Template nel Percorso", clicca "Rimuovi" su uno dei template aggiunti.
    *   Verifica: Il template scompare dalla lista.

16. **Eliminazione Template Percorso:**
    *   Vai alla lista "Template Percorsi".
    *   Trova il template "Percorso Impero Romano".
    *   Clicca "Elimina".
    *   Conferma.
    *   Verifica: Il template scompare.

17. **Assegnazione Contenuto (da Template):**
    *   Vai alla sezione "Assegna".
    *   Seleziona "Template Quiz" come Tipo Contenuto.
    *   Seleziona "Template Storia Romana" dal dropdown.
    *   Imposta una data di scadenza (opzionale).
    *   Seleziona lo studente `STUDENT1000`.
    *   Clicca "Assegna Selezionati".
    *   Verifica: Messaggio di successo.
    *   Seleziona "Template Percorso" come Tipo Contenuto.
    *   Seleziona "Percorso Impero Romano" dal dropdown.
    *   Seleziona lo studente `STUDENT1000`.
    *   Clicca "Assegna Selezionati".
    *   Verifica: Messaggio di successo.

18. **Visualizzazione Istanze Assegnate:**
    *   Vai alla sezione "Quiz Assegnati".
    *   Verifica: Dovrebbe apparire un'istanza del quiz "Template Storia Romana" (potrebbe avere lo stesso titolo o uno generato). Verifica che indichi il template sorgente.
    *   Vai alla sezione "Percorsi Assegnati".
    *   Verifica: Dovrebbe apparire un'istanza del percorso "Percorso Impero Romano". Verifica che indichi il template sorgente.

## Frontend Studente (`http://localhost:5175`)

19. **Login Studente:**
    *   Accedi con il codice `STUDENT1000`.
    *   Verifica: Accesso riuscito.

20. **Visualizzazione Contenuti Assegnati:**
    *   Nella dashboard studente, cerca le sezioni quiz e percorsi.
    *   Verifica: L'istanza del quiz "Template Storia Romana" e l'istanza del percorso "Percorso Impero Romano" sono visibili con il pulsante "Inizia".

21. **Svolgimento Quiz (Istanza):**
    *   Clicca "Inizia" per l'istanza del quiz.
    *   Verifica: Navigazione alla pagina di svolgimento. Le domande create nel template (Augusto, 753 a.C., Colosseo, Guerre Puniche) vengono visualizzate correttamente.
    *   Rispondi alle domande (correttamente e/o erroneamente).
    *   Completa il tentativo.
    *   Verifica: Messaggio di completamento.

22. **Svolgimento Percorso (Istanza):**
    *   Clicca "Inizia" per l'istanza del percorso.
    *   Verifica: Viene presentato il primo quiz del percorso (l'istanza creata da "Template Storia Romana").
    *   Completa il quiz.
    *   Verifica: Se ci sono altri quiz nel percorso, viene presentato il successivo. Altrimenti, il percorso viene segnato come completato.

23. **Logout Studente:**
    *   Esegui il logout.
    *   Verifica: Reindirizzamento al login.