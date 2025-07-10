# Specifica Tecnica: Funzionalità di Raggruppamento per Studenti e Template Quiz

## 1. Sommario

Questo documento descrive i requisiti tecnici per implementare una funzionalità di raggruppamento nelle viste "Student Progress" e "Quiz Templates" all'interno del `frontend-teacher`. L'obiettivo è permettere ai docenti di visualizzare gli studenti e i template di quiz raggruppati per i gruppi di appartenenza, replicando l'aspetto e il comportamento della funzionalità esistente nella vista `UdaListView` del `frontend-lessons`.

## 2. Prerequisiti: Modifiche al Backend

Le modifiche al frontend dipendono da aggiornamenti agli endpoint API esistenti per fornire i dati necessari sui gruppi.

### 2.1. Endpoint `student-progress-summary`

-   **Endpoint**: `/api/teacher/student-progress-summary/`
-   **Serializer da modificare**: `StudentProgressSummarySerializer` (presumibilmente in `apps/users/serializers.py` o un file correlato).
-   **Modifica richiesta**: Aggiungere un campo `groups` al serializer.
    -   **Nome campo**: `groups`
    -   **Tipo**: `serializers.SerializerMethodField` o un `NestedSerializer` se la relazione è diretta.
    -   **Struttura dati di ritorno**: Un array di oggetti, dove ogni oggetto rappresenta un gruppo a cui lo studente è associato per il docente che effettua la richiesta.
        ```json
        {
          "id": "integer",
          "name": "string"
        }
        ```
-   **Esempio di risposta per un singolo studente**:
    ```json
    {
      "student_id": 101,
      "full_name": "Mario Rossi",
      "student_code": "MR001",
      "completed_quizzes_count": 5,
      "completed_pathways_count": 2,
      "total_points_earned": 150,
      "groups": [
        { "id": 1, "name": "Gruppo A - Matematica" },
        { "id": 5, "name": "Recupero Pomeridiano" }
      ]
    }
    ```

### 2.2. Endpoint `teacher-quiz-templates`

-   **Endpoint**: `/api/teacher/quiz-templates/`
-   **Serializer da modificare**: `QuizTemplateSerializer` (presumibilmente in `apps/education/serializers.py`).
-   **Modifica richiesta**: Aggiungere un campo `group` per rappresentare il gruppo a cui il template è associato. I template, a differenza delle UDA, possono appartenere a un solo gruppo o a nessuno.
    -   **Nome campo**: `group`
    -   **Tipo**: `NestedSerializer` sulla base del modello `Group`.
    -   **Struttura dati di ritorno**: Un oggetto che rappresenta il gruppo, o `null` se il template non è in un gruppo.
        ```json
        {
          "id": "integer",
          "name": "string"
        }
        ```
-   **Esempio di risposta per un singolo template**:
    ```json
    {
      "id": 42,
      "title": "Verifica di Storia - Capitolo 3",
      "description": "La civiltà romana.",
      "subject": "Storia",
      "topic": "Impero Romano",
      "created_at": "2024-07-09T10:00:00Z",
      "group": {
        "id": 2,
        "name": "Template di Storia - Classe 3B"
      }
    }
    ```

## 3. Modifiche al Frontend (`frontend-teacher`)

### 3.1. Vista `StudentProgressView.vue`

1.  **Data Layer**:
    -   Aggiornare l'interfaccia `StudentProgressSummary` in `<script setup>` per includere il nuovo campo:
        ```typescript
        interface StudentProgressSummary {
          // ... campi esistenti
          groups: { id: number; name: string; }[];
        }
        ```

2.  **UI Layer**:
    -   Aggiungere una nuova colonna `<th>Gruppi</th>` nell'intestazione della tabella.
    -   Nella riga dello studente (`<tr>`), aggiungere una cella `<td>` che mostri i nomi dei gruppi a cui lo studente appartiene (es. `summary.groups.map(g => g.name).join(', ')`). Questa colonna sarà visibile solo nella vista non raggruppata.

3.  **Logic Layer (Raggruppamento)**:
    -   Introdurre una variabile reattiva per lo stato di espansione: `const expandedGroups = ref<Set<number>>(new Set());`.
    -   Introdurre una funzione `toggleGroup(groupId: number)` per gestire l'aggiunta/rimozione di ID dal set `expandedGroups`.
    -   Creare una `computed property` `groupedStudents` che processi `progressSummaries.value` e restituisca un oggetto con due proprietà: `grouped` e `ungrouped`.
        -   `grouped`: Un array di `{ group: Group, students: StudentProgressSummary[] }`.
        -   `ungrouped`: Un array di `StudentProgressSummary` (studenti senza gruppo).
        -   La logica dovrà gestire studenti che appartengono a più gruppi, potenzialmente duplicandoli sotto ogni gruppo di appartenenza.

4.  **Template Rework**:
    -   Il `<tbody>` della tabella dovrà essere modificato per iterare prima su `groupedStudents.grouped`.
    -   Per ogni gruppo, renderizzare una riga `<tr>` cliccabile (`@click="toggleGroup(group.id)"`) che funge da intestazione del gruppo. Questa riga mostrerà il nome del gruppo e un'icona (es. `FolderPlusIcon`/`FolderMinusIcon`).
    -   Subito dopo la riga del gruppo, usare un `<template v-if="expandedGroups.has(group.id)">` per renderizzare le righe `<tr>` degli studenti appartenenti a quel gruppo.
    -   Dopo il loop dei gruppi, renderizzare le righe per gli studenti in `groupedStudents.ungrouped`.

5.  **Styling**:
    -   Copiare le classi CSS e la logica di stile da `UdaListView.vue` per evidenziare visivamente i gruppi espansi e i loro elementi figli.

### 3.2. Vista `QuizTemplatesView.vue`

1.  **Data Layer**:
    -   Aggiornare il tipo `QuizTemplate` (importato da `@/api/quizzes`) per includere il nuovo campo:
        ```typescript
        interface QuizTemplate {
          // ... campi esistenti
          group: { id: number; name: string; } | null;
        }
        ```

2.  **Logic Layer (Raggruppamento)**:
    -   L'implementazione seguirà fedelmente quella di `UdaListView.vue`.
    -   Introdurre `const expandedGroups = ref<Set<number>>(new Set());`.
    -   Introdurre `toggleGroup(groupId: number)`.
    -   Creare una `computed property` `groupedTemplates` che processi `templates.value` e restituisca `{ grouped: { group: Group, templates: QuizTemplate[] }[], ungrouped: QuizTemplate[] }`.

3.  **Template Rework**:
    -   Rifattorizzare il `<tbody>` per renderizzare prima i gruppi e poi i template al loro interno, in modo identico a quanto descritto per `StudentProgressView.vue`.

4.  **Styling**:
    -   Copiare e adattare gli stili da `UdaListView.vue`.

## 4. Riferimento Visivo e Comportamentale

Tutte le nuove funzionalità di raggruppamento devono replicare fedelmente l'implementazione presente in `frontend-lessons/src/views/uda/UdaListView.vue`. Questo include:
-   Stile delle righe di intestazione dei gruppi.
-   Animazione di apertura/chiusura (implicita tramite transizioni Vue se presenti).
-   Icone per lo stato espanso/collassato.
-   Bordo visivo che racchiude il gruppo espanso e i suoi elementi.