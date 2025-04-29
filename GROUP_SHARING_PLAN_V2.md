# Piano di Implementazione: Condivisione Gruppi Studenti (v2 - Flusso Approvazione)

**Stato Attuale:** Fase 3 (Aggiornamento Interfaccia Frontend) - Frontend Studente da iniziare.

Questo documento descrive il piano per implementare la funzionalità di condivisione dei gruppi di studenti tra docenti, utilizzando un modello basato su gruppi pubblici e richieste di accesso con approvazione.

## Obiettivo

Permettere ai docenti di condividere i propri gruppi di studenti con altri docenti, mantenendo il controllo sull'accesso. Tracciare quale docente assegna lezioni e quiz.

## Flusso Proposto

1.  **Permesso Admin:** Un Admin può abilitare un Docente a creare "gruppi pubblici".
2.  **Creazione Gruppo:** Un Docente (con permesso) può creare un gruppo e marcarlo come "pubblico".
3.  **Ricerca e Richiesta:** Un altro Docente può cercare gruppi pubblici e inviare una richiesta di accesso al gruppo desiderato.
4.  **Approvazione Owner:** L'Owner del gruppo riceve la richiesta e può approvarla o rifiutarla.
5.  **Accesso Condiviso:** Se approvato, il Docente richiedente ottiene accesso al gruppo (visualizzazione studenti, assegnazione contenuti).
6.  **Tracciamento Assegnazioni:** Quando un Docente (owner o con accesso approvato) assegna una lezione o un quiz, il sistema registra chi ha effettuato l'assegnazione.
7.  **Visualizzazione Studente:** Lo studente vede chi ha assegnato ogni lezione/quiz.

## Piano Dettagliato

### Fase 1: Modifiche ai Modelli del Database (Backend) - [COMPLETATA]

1.  **Modello `User` (`apps/users/models.py`):** Aggiunto `can_create_public_groups`.
2.  **Modello `StudentGroup` (`apps/student_groups/models.py`):** Rinominato `teacher` in `owner`, aggiunto `is_public`.
3.  **Nuovo Modello `GroupAccessRequest` (`apps/student_groups/models.py`):** Creato.
4.  **Modello `Student` (`apps/users/models.py`):** Rimosso `teacher`.
5.  **Modello `LessonAssignment` (`lezioni/models.py`):** Aggiunto `assigned_by`.
6.  **Modello `QuizAssignment` (`apps/education/models.py`):** Aggiunto `assigned_by`.

### Fase 2: Aggiornamento Logica Backend - [COMPLETATA]

1.  **API & Serializers:**
    *   **Serializers (`apps/student_groups/serializers.py`):** Aggiornati/Aggiunti. - **[COMPLETATO]**
    *   **Views (`apps/student_groups/views.py`):** - **[COMPLETATO]**
        *   Aggiornare `StudentGroupViewSet`:
            *   `perform_create`: Impostare `owner=request.user`. - **[COMPLETATO]**
            *   `get_queryset`: Filtrare per `owner` e accessi approvati. - **[COMPLETATO]**
            *   `perform_update`: Controllare `can_create_public_groups` se `is_public` viene modificato. - **[COMPLETATO]**
            *   Aggiungere/Aggiornare azioni custom (`generate_token`, `delete_token`, `add_student`, `remove_student`) per usare i nuovi permessi (owner o accesso approvato). - **[COMPLETATO]**
            *   Aggiungere azione `@action` `list_access_requests` (solo owner). - **[COMPLETATO]**
            *   Aggiungere azione `@action` `respond_access_request` (solo owner, usa `RespondGroupAccessRequestSerializer`). - **[COMPLETATO]**
        *   Creare `GroupAccessRequestViewSet`:
            *   `perform_create`: Impostare `requesting_teacher=request.user`. - **[COMPLETATO]**
            *   `get_queryset`: Filtrare per `requesting_teacher=request.user`. - **[COMPLETATO]**
            *   Definire permessi (solo creazione/lettura proprie richieste). - **[COMPLETATO]**
        *   Creare/Aggiornare View Admin per `User` per gestire `can_create_public_groups`. - **[COMPLETATO]**
        *   Aggiornare ViewSet Assegnazioni (`LessonAssignmentViewSet`, `QuizAssignmentViewSet` - in `lezioni/views.py` e `apps/education/views.py`) per:
            *   Popolare `assigned_by=request.user`. - **[COMPLETATO]**
            *   Verificare permessi (owner o accesso approvato al gruppo target). - **[COMPLETATO]**
2.  **Permessi (`apps/student_groups/permissions.py`):** - **[COMPLETATO]**
    *   Creare classi di permesso personalizzate (`IsGroupOwner`, `HasGroupAccess`, `IsOwnerOrHasAccess`, `IsRequestingTeacher`) per le ViewSet e le azioni.

### Fase 3: Aggiornamento Interfaccia Frontend - [IN CORSO]

1.  **Frontend Admin:** UI per `can_create_public_groups`. - **[COMPLETATO]**
2.  **Frontend Docente (`frontend-teacher`):** UI per `is_public`, UI per sfoglia/richiedi accesso, UI gestione richieste, aggiornare liste gruppi. - **[COMPLETATO]**
3.  **Frontend Studente (`frontend-student`):** Visualizzare "Assegnato da: ...". - **[COMPLETATO]**

### Fase 4: Migrazioni e Test - [MIGRAZIONI COMPLETATE]

1.  **Migrazioni Django:** Generate e applicate. - **[COMPLETATO]**
2.  **Test:** - **[DA FARE]**

## Diagramma di Flusso (Mermaid)

```mermaid
graph TD
    subgraph Backend Changes
        direction LR
        M_User[User Model - OK]:::done
        M_StudentGroup[StudentGroup Model - OK]:::done
        M_New_Request[NEW: GroupAccessRequest Model - OK]:::done
        M_Student[Student Model - OK]:::done
        M_LessonAssign[LessonAssignment Model - OK]:::done
        M_QuizAssign[QuizAssignment Model - OK]:::done
        API[API Views/Serializers/Permessi - OK]:::done
        Mig[Django Migrations - OK]:::done
    end

    subgraph Frontend Changes
        direction LR
        FE_Admin[Frontend Admin - OK]:::done
        FE_Teacher[Frontend Docente - OK]:::done
        FE_Student[Frontend Studente - TODO]:::todo
    end

    M_User --> API;
    M_StudentGroup --> API;
    M_New_Request --> API;
    M_Student --> API;
    M_LessonAssign --> API;
    M_QuizAssign --> API;
    API -- Genera --> Mig;
    API -- Interagisce con --> FE_Admin;
    API -- Interagisce con --> FE_Teacher;
    API -- Interagisce con --> FE_Student;

    classDef done fill:#dff,stroke:#333,stroke-width:2px;
    classDef inprogress fill:#f9f,stroke:#333,stroke-width:2px;
    classDef todo fill:#fef,stroke:#333,stroke-width:1px,stroke-dasharray: 5 5;

    class M_User,M_StudentGroup,M_New_Request,M_Student,M_LessonAssign,M_QuizAssign,Mig,API,FE_Admin,FE_Teacher done;
    class FE_Student todo;