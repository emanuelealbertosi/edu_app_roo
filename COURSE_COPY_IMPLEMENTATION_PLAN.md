# Piano di Implementazione: Funzionalità di Copia Corso

**Versione:** 1.0
**Data:** 29 Giugno 2025

## 1. Obiettivo

Introdurre una funzionalità "one-click" che permetta a un docente di duplicare un intero corso, incluse tutte le Unità Didattiche di Apprendimento (UDA) associate. L'interfaccia utente per questa funzionalità dovrà essere un'icona "copia" nella lista dei corsi, per coerenza con funzionalità simili esistenti (es. copia UDA).

## 2. Modifiche al Backend (Django)

**File di riferimento:** `apps/uda/views.py`

L'implementazione si concentrerà sull'aggiunta di una nuova azione al `CourseViewSet` esistente.

### 2.1. Estrazione della Logica di Copia UDA

Per migliorare la manutenibilità e la riusabilità del codice, la logica di business per la copia di una singola UDA verrà estratta in una funzione helper dedicata.

*   **Azione:** Creare una funzione di supporto `_copy_uda_instance(original_uda, new_course, teacher)`.
*   **Logica:** Questa funzione conterrà la logica attualmente presente nell'azione `copy_uda` del `UDAViewSet`. La differenza chiave sarà che questa funzione accetterà un'istanza di `Course` (`new_course`) a cui associare la nuova UDA creata.
*   **Refactoring:** L'azione `copy_uda` esistente nel `UDAViewSet` verrà modificata per chiamare semplicemente questa nuova funzione helper, passando `new_course=None`.

### 2.2. Implementazione dell'Azione `copy` nel `CourseViewSet`

*   **Azione:** Aggiungere una nuova azione `copy` decorata con `@action(detail=True, methods=['post'], url_path='copy')` e `@transaction.atomic` al `CourseViewSet`.
*   **URL:** `POST /api/courses/{course_id}/copy/`
*   **Logica Dettagliata:**
    1.  Recuperare l'istanza del corso originale (`original_course`) usando `self.get_object()`.
    2.  Creare una nuova istanza di `Course` (`new_course`), duplicando i dati rilevanti. Il nome verrà prefissato con "Copia di " per distinguerlo.
    3.  Recuperare tutte le UDA associate al corso originale, mantenendo l'ordine (`original_course.uda_set.all().order_by('order_in_course')`).
    4.  Iterare su ciascuna UDA originale.
    5.  All'interno del ciclo, chiamare la funzione helper `_copy_uda_instance`, passando l'UDA originale, la `new_course` appena creata e l'utente (`request.user`).
    6.  Al termine del ciclo, serializzare l'istanza `new_course` e restituirla in una `Response` con status `HTTP_201_CREATED`.

## 3. Modifiche al Frontend (Vue.js)

### 3.1. Servizio API

*   **File:** `frontend-lessons/src/services/courseService.ts`
*   **Azione:** Aggiungere una nuova funzione asincrona `copyCourse(courseId: number)` che esegue una richiesta `POST` all'endpoint `/api/courses/{courseId}/copy/`.

### 3.2. Store Management (Pinia)

*   **File:** `frontend-lessons/src/stores/courseStore.ts`
*   **Azione:** Creare una nuova action `copyCourse(courseId: number)`.
*   **Logica:**
    1.  Impostare uno stato di `loading` a `true`.
    2.  Chiamare la funzione `courseService.copyCourse(courseId)`.
    3.  In caso di successo (blocco `try`):
        *   Mostrare una notifica globale di successo (es. "Corso copiato con successo").
        *   Chiamare l'azione `fetchCourses()` per aggiornare la lista dei corsi nella UI.
    4.  In caso di errore (blocco `catch`):
        *   Mostrare una notifica di errore.
    5.  Impostare lo stato di `loading` a `false` nel blocco `finally`.

### 3.3. Interfaccia Utente (UI)

*   **File:** `frontend-lessons/src/views/courses/CourseListView.vue`
*   **Azione:**
    *   Nella tabella o lista che mostra i corsi, aggiungere una colonna "Azioni".
    *   Per ogni riga del corso, inserire un componente icona (es. da FontAwesome) che rappresenti la copia (`fa-copy`).
*   **Logica di Interazione:**
    1.  Associare un evento `@click` all'icona di copia.
    2.  Il metodo chiamato dal click mostrerà una modale di conferma per prevenire azioni accidentali (es. "Sei sicuro di voler copiare il corso 'Nome Corso'?").
    3.  Se l'utente conferma, il metodo chiamerà l'azione dello store: `courseStore.copyCourse(course.id)`.

## 4. Diagramma del Flusso

```mermaid
graph TD
    A[Utente clicca icona "Copia" su CourseListView.vue] --> B{Mostra modale di conferma};
    B -- Conferma --> C[Chiama action `copyCourse` in courseStore.ts];
    C --> D[Chiama `copyCourse` in courseService.ts];
    D --> E[Invia POST a `/api/courses/{id}/copy/`];

    subgraph Backend (Django)
        E --> F[CourseViewSet riceve la richiesta nell'azione `copy`];
        F --> G[Crea una nuova istanza di Course (es. "Nome Corso (Copia)")];
        G --> H[Recupera tutte le UDA del corso originale];
        H --> I{Itera su ogni UDA};
        I -- Per ogni UDA --> J[Chiama la funzione helper `_copy_uda_instance`];
        J -- Associa la nuova UDA al nuovo Corso --> I;
        I -- Fine iterazione --> K[Salva il nuovo corso e le nuove UDA];
        K --> L[Restituisce il nuovo Course serializzato];
    end

    subgraph Frontend (Vue.js)
        L -- Risposta 201 Created --> M[courseService riceve la risposta];
        M --> N[courseStore gestisce il successo];
        N --> O[Mostra notifica di successo];
        N --> P[Chiama `fetchCourses` per aggiornare la lista];
        P --> Q[La UI si aggiorna mostrando il corso copiato];
    end