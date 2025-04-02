# Test Manuali Applicazione Educativa

## Frontend Docente (`http://localhost:5174`)

1.  **Login Docente:**
    *   Accedi con `teacher_test` / `password123`. OK
    *   Verifica: Accesso riuscito e reindirizzamento alla dashboard. OK

2.  **Creazione Quiz:**
    *   Vai alla sezione Quiz. OK
    *   Clicca "Crea Nuovo Quiz". OK 
    *   Inserisci titolo e descrizione. OK
    *   Salva. OK
    *   Verifica: Il quiz appare nella lista. OK

3.  **Modifica Quiz (Info Base):**
    *   Trova un quiz esistente e clicca "Modifica".
    *   Modifica il titolo e la descrizione.
    *   Imposta date di disponibilità (opzionale).
    *   Salva.
    *   Verifica: Torna alla lista quiz, il titolo aggiornato è visibile. Rientrando in modifica, le date sono corrette.

4.  **Modifica Quiz (Aggiunta Domanda MC - Single):**
    *   Entra in modifica di un quiz.
    *   Clicca "Aggiungi Domanda".
    *   Inserisci testo, seleziona tipo "Multiple Choice (Single Answer)".
    *   Crea Domanda.
    *   Verifica: Reindirizzamento a modifica domanda, editor opzioni visibile.

5.  **Aggiunta/Modifica Opzioni MC-Single (BUG FIX):**
    *   Nell'editor opzioni:
        *   Aggiungi 3 opzioni (es. A, B, C).
        *   Seleziona B come corretta. Salva Opzioni.
        *   Ricarica/Rientra. Verifica: B è selezionata.
        *   Seleziona C come corretta. Salva Opzioni.
        *   Ricarica/Rientra. Verifica: C è selezionata, B non più.

6.  **Modifica Quiz (Aggiunta Domanda MC - Multi):**
    *   Entra in modifica di un quiz.
    *   Clicca "Aggiungi Domanda".
    *   Inserisci testo, seleziona tipo "Multiple Choice (Multiple Answers)".
    *   Crea Domanda.
    *   Verifica: Reindirizzamento a modifica domanda, editor opzioni visibile.

7.  **Aggiunta/Modifica Opzioni MC-Multi:**
    *   Nell'editor opzioni:
        *   Aggiungi 4 opzioni (es. W, X, Y, Z).
        *   Seleziona X e Z come corrette (checkbox). Salva Opzioni.
        *   Ricarica/Rientra. Verifica: X e Z sono selezionate.
        *   Deseleziona X, seleziona Y. Salva Opzioni.
        *   Ricarica/Rientra. Verifica: Y e Z sono selezionate.

8.  **Modifica Quiz (Aggiunta Domanda TF):**
    *   Entra in modifica di un quiz.
    *   Clicca "Aggiungi Domanda".
    *   Inserisci testo, seleziona tipo "True/False".
    *   Crea Domanda.
    *   Verifica: Reindirizzamento a modifica domanda, editor opzioni visibile (dovrebbe mostrare automaticamente opzioni True/False?). *Nota: Se le opzioni TF non sono auto-generate, testare l'aggiunta manuale.*

9.  **Aggiunta/Modifica Opzioni TF:**
    *   Nell'editor opzioni (se manuali):
        *   Aggiungi opzione "True", selezionala come corretta.
        *   Aggiungi opzione "False". Salva Opzioni.
        *   Ricarica/Rientra. Verifica: "True" è selezionata.
        *   Cambia la selezione a "False". Salva Opzioni.
        *   Ricarica/Rientra. Verifica: "False" è selezionata.

10. **Modifica Quiz (Aggiunta Domanda FillBlank):**
    *   Entra in modifica di un quiz.
    *   Clicca "Aggiungi Domanda".
    *   Inserisci testo (es. "La capitale della Francia è ____.").
    *   Seleziona tipo "Fill in the Blank".
    *   Crea Domanda.
    *   Verifica: Reindirizzamento a modifica domanda. *Nota: L'editor opzioni non dovrebbe apparire. La gestione delle risposte corrette avviene tramite metadata?*

11. **Modifica Quiz (Aggiunta Domanda OpenManual):**
    *   Entra in modifica di un quiz.
    *   Clicca "Aggiungi Domanda".
    *   Inserisci testo (es. "Descrivi la fotosintesi.").
    *   Seleziona tipo "Open Answer (Manual Grading)".
    *   Crea Domanda.
    *   Verifica: Reindirizzamento a modifica domanda. *Nota: L'editor opzioni non dovrebbe apparire.*

12. **Ordinamento Domande:**
    *   Entra in modifica di un quiz con almeno 2 domande.
    *   Verifica se esiste un modo per cambiare l'ordine delle domande (es. drag-and-drop, campi numerici 'ordine').
    *   Se sì, cambia l'ordine e salva (potrebbe essere un salvataggio automatico o richiedere un salvataggio del quiz).
    *   Ricarica/Rientra. Verifica: Il nuovo ordine è mantenuto.

13. **Eliminazione Opzione:**
    *   Entra in modifica di una domanda MC con opzioni.
    *   Clicca "Rimuovi" su un'opzione.
    *   Clicca "Salva Modifiche Opzioni".
    *   Ricarica/Rientra. Verifica: L'opzione è stata rimossa.

14. **Eliminazione Domanda:**
    *   Entra in modifica di un quiz.
    *   Trova una domanda nella lista.
    *   Clicca sul pulsante/icona per eliminare la domanda.
    *   Conferma l'eliminazione (se richiesto).
    *   Verifica: La domanda scompare dalla lista.

15. **Eliminazione Quiz:**
    *   Vai alla lista Quiz.
    *   Trova un quiz.
    *   Clicca sul pulsante/icona per eliminare il quiz.
    *   Conferma l'eliminazione (se richiesto).
    *   Verifica: Il quiz scompare dalla lista.

16. **Assegnazione Quiz a Studente:**
    *   Torna alla lista Quiz.
    *   Trova un quiz valido (es. ID 88).
    *   Cerca un'opzione per "Assegna".
    *   Assegna il quiz allo studente `STUDENT1000`.
    *   Verifica: Conferma dell'assegnazione. Prova ad assegnarlo di nuovo. Verifica: Messaggio che indica che è già assegnato.

## Frontend Studente (`http://localhost:5175`)

17. **Login Studente:**
    *   Accedi con il codice `STUDENT1000`.
    *   Verifica: Accesso riuscito e reindirizzamento alla dashboard studente.

18. **Visualizzazione Quiz Assegnato:**
    *   Nella dashboard studente, cerca la sezione dei quiz assegnati.
    *   Verifica: Il quiz assegnato (ID 88) è visibile con un pulsante "Inizia".

19. **Inizio Tentativo Quiz:**
    *   Clicca "Inizia" per il quiz ID 88.
    *   Verifica: Navigazione alla pagina di svolgimento. La prima domanda (MC) viene visualizzata con le opzioni corrette.

20. **Risposta a Domanda MC:**
    *   Seleziona l'opzione corretta ("Roma").
    *   Clicca "Invia Risposta".
    *   Verifica: Passaggio alla domanda successiva (se esiste) o completamento.

21. **Risposta ad altri tipi di domande (se presenti nel quiz):**
    *   Rispondi a domande TF, MC-Multi, FillBlank, OpenManual se le hai aggiunte al quiz ID 88.
    *   Verifica: L'interfaccia per ogni tipo di domanda è corretta e permette l'invio.

22. **Completamento Quiz:**
    *   Arriva alla fine del quiz.
    *   Clicca sul pulsante per completare il tentativo.
    *   Verifica: Messaggio di completamento. Se viene mostrato un punteggio, verifica che sia corretto (considerando solo le domande auto-gradate per ora).

23. **Visualizzazione Tentativi Precedenti (se implementato):**
    *   Torna alla dashboard studente.
    *   Verifica se per il quiz ID 88 viene mostrato lo stato "Completato" e/o il punteggio.
    *   Verifica se è possibile rivedere il tentativo (opzionale).

24. **Logout Studente:**
    *   Trova il pulsante/link di logout.
    *   Clicca Logout.
    *   Verifica: Reindirizzamento alla pagina di login.