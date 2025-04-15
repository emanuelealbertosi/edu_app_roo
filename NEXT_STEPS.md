1. [OK]Dare ai docenti la possibilità di disassegnare quiz e percorsi agli studenti. OK
2. [OK]Dare ai docenti la possibilità di creare studenti a loro assegnati (compreso codice studente e pin).
3. [OK]Ai docenti di vedere i dettagli dei loro studenti compreso username e codice studente nella vista studenti (che già esiste).
4. [OK]Aggiornare la dashboard del docente rendendola funzionale e significativa.
5. [OK]Rendere significativi i link "dettagli" nelle varie pagine docente (es. quiz assegnati, percorsi assegnati, studenti).
6. [OK]Creare una homepage per l'applicazione da cui partire (con link alle aree studente e docente).
7. [OK]Aggiungere la possibilita' di creare gruppi di studenti (anch'essi associati ad un docente) raggruppando gli studenti.
8. [OK]Creare aggiornare la pagina di registrazione studenti dei docenti aggiungendo la possibilita' di creare un gruppo di studenti.
9. [OK]Fare in modo che gli studenti possano registrarsi da soli grazia ad un QR code che gli viene fornito dal docente (visibile nella home del docente)
10. Aggiungere funzionalità di reportistica e statistiche per docenti/admin. (Attività annullata, ma completati i seguenti sotto-punti)
    *   [OK] Backend: Aggiunti serializer `QuizTemplateStatsSerializer` e `PathwayTemplateStatsSerializer`.
    *   [OK] Backend: Aggiunta azione `statistics` a `TeacherQuizTemplateViewSet`.
    *   [OK] Frontend Docente: Aggiunta funzione API `fetchQuizTemplateStats`.
    *   [OK] Frontend Docente: Aggiornata vista `QuizTemplatesView.vue` per visualizzare statistiche template quiz.
11. Effettuare una revisione della sicurezza (permessi, validazione input, vulnerabilità).