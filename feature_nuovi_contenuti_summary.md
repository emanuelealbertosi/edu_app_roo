# Riepilogo Implementazione: Contatori Nuovi Contenuti Studente

**Data:** 24 Maggio 2025

## Obiettivo

Implementare un sistema di contatori visivi nel menu dell'applicazione `frontend-student` per notificare agli studenti la presenza di nuovi quiz non iniziati e nuove lezioni non lette.

## Attività Completate

### 1. Frontend (`frontend-student`)

*   **Modifica UI Menu ([`frontend-student/src/App.vue`](frontend-student/src/App.vue:1)):**
    *   Aggiunti indicatori visivi (pallini rossi con conteggio) accanto alle voci di menu "I Miei Quiz" e "Le Mie Lezioni" (sia per desktop che per mobile).
    *   Aggiunti messaggi hover dinamici (es. "Hai N nuovi quiz") per queste voci di menu.
    *   Gli indicatori e i messaggi appaiono solo se il conteggio dei nuovi elementi è maggiore di zero.
*   **Logica Store Pinia ([`frontend-student/src/stores/auth.ts`](frontend-student/src/stores/auth.ts:1)):**
    *   Introdotte nello stato le proprietà `unreadQuizzesCount` e `unreadLessonsCount`.
    *   Creata una nuova azione `fetchNewContentCounts` che chiama un servizio API per recuperare i conteggi dal backend.
    *   Questa azione aggiorna le proprietà di stato con i dati ricevuti.
    *   L'azione `fetchNewContentCounts` viene invocata dopo un login studente riuscito e durante l'inizializzazione dell'app (`initializeAuth`) se l'utente è già autenticato.
*   **Servizio API Frontend ([`frontend-student/src/api/dashboard.ts`](frontend-student/src/api/dashboard.ts:1)):**
    *   Aggiunta una nuova funzione `getNewContentCounts` all'oggetto `DashboardService`.
    *   Questa funzione effettua una chiamata `GET` all'endpoint backend `/api/student/new-content-counts/` utilizzando l'istanza `apiClient` configurata (con gestione token JWT).

### 2. Backend (Django)

*   **Nuovo Endpoint API ([`apps/education/views.py`](apps/education/views.py:2450)):**
    *   Creata una nuova view `StudentNewContentCountsView(APIView)`.
    *   L'endpoint è accessibile via `GET /api/student/new-content-counts/`.
    *   Richiede autenticazione studente (`IsAuthenticated`, `IsStudentAuthenticated`).
*   **Logica Conteggio Quiz:**
    *   La view interroga i modelli `QuizAssignment` e `QuizAttempt`.
    *   Un quiz è contato come "nuovo/non iniziato" se è assegnato allo studente (direttamente o tramite un gruppo a cui appartiene) e non esiste un `QuizAttempt` corrispondente per quello studente e quel quiz con il campo `started_at` valorizzato.
*   **Logica Conteggio Lezioni:**
    *   La view interroga i modelli `LessonAssignment` (da `lezioni.models`) e `Lesson` (da `lezioni.models`).
    *   Una lezione è contata come "nuova/non letta" se è assegnata allo studente (direttamente o tramite un gruppo), la lezione stessa ha `is_published = True`, e il campo `viewed_at` nel `LessonAssignment` è `null`.
*   **Registrazione URL ([`apps/education/urls.py`](apps/education/urls.py:72)):**
    *   Il nuovo endpoint è stato aggiunto alla configurazione degli URL dell'app `education`.

## Modelli Coinvolti (Identificati e Utilizzati)

*   **Utenti:**
    *   [`apps/users/models.py:98`](apps/users/models.py:98) (`Student`)
    *   [`apps/users/models.py:13`](apps/users/models.py:13) (`User`)
*   **Quiz e Tentativi:**
    *   [`apps/education/models.py:225`](apps/education/models.py:225) (`Quiz`)
    *   [`apps/education/models.py:1072`](apps/education/models.py:1072) (`QuizAssignment`)
    *   [`apps/education/models.py:420`](apps/education/models.py:420) (`QuizAttempt`)
*   **Lezioni e Assegnazioni Lezioni:**
    *   [`lezioni/models.py:50`](lezioni/models.py:50) (`Lesson`)
    *   [`lezioni/models.py:105`](lezioni/models.py:105) (`LessonAssignment`)
*   **Gruppi Studenti (per query su assegnazioni):**
    *   `apps/student_groups/models.py` (Modelli `StudentGroup`, `StudentGroupMembership` referenziati nelle query)

## Cosa Resta da Fare / Punti da Verificare

1.  **Test End-to-End:**
    *   Verificare che i conteggi vengano aggiornati correttamente nel frontend dopo il login e al caricamento dell'app per un utente già loggato.
    *   Testare il comportamento quando nuovi quiz vengono assegnati o iniziati.
    *   Testare il comportamento quando nuove lezioni vengono assegnate o marcate come lette (una volta implementata l'azione di marcatura).
2.  **Marcare Lezioni come Lette:**
    *   Attualmente, il backend conta le lezioni con `viewed_at = null` come "nuove".
    *   È necessario implementare la logica (probabilmente nel frontend `frontend-lessons` o `frontend-student` quando una lezione viene visualizzata) per chiamare un endpoint API che imposti il campo `LessonAssignment.viewed_at` con il timestamp corrente.
    *   L'endpoint API per marcare una lezione come vista (`POST /api/lezioni/assignments/{assignment_pk}/mark-viewed/`) sembra esistere già in [`lezioni/views.py`](lezioni/views.py:366) (`LessonAssignmentViewSet.mark_viewed`). Bisogna assicurarsi che il frontend lo chiami correttamente.
3.  **Ottimizzazioni Query (Opzionale):**
    *   Le query Django implementate per i conteggi sono funzionali. Se si dovessero riscontrare problemi di performance con un grande numero di utenti/assegnazioni, potrebbero essere ulteriormente ottimizzate (es. con `select_related` o `prefetch_related` più specifici se le relazioni diventano più complesse, anche se per i conteggi `distinct().count()` è generalmente efficiente).
4.  **Gestione Errori API nel Frontend:**
    *   Assicurarsi che lo store Pinia e i componenti gestiscano appropriatamente eventuali errori durante la chiamata API per recuperare i conteggi (es. mostrando 0 o un messaggio di errore discreto invece di bloccare l'UI). La gestione attuale nello store resetta i conteggi a 0 in caso di errore.

Questo documento riassume le modifiche principali apportate.