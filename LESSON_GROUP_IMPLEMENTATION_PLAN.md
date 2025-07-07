# Piano di Implementazione: Raggruppamento Lezioni

Questo documento traccia l'implementazione della funzionalità di raggruppamento delle lezioni.

## 1. Piano Iniziale

L'obiettivo è permettere ai docenti di raggruppare logicamente le lezioni.

### 1.1 Modifiche Backend (Django)

- **Modello:**
    - [x] Creare il modello `LessonGroup` in `lezioni/models.py`.
    - [x] Aggiungere una `ForeignKey` da `Lesson` a `LessonGroup` in `lezioni/models.py`.
- **Migrazioni:**
    - [x] Creare la migrazione per i nuovi modelli.
    - [x] Applicare la migrazione al database.
- **API (DRF):**
    - [x] Creare `LessonGroupSerializer` in `lezioni/serializers.py`.
    - [x] Aggiornare `LessonSerializer` e `LessonWriteSerializer` per includere il campo `group`.
    - [x] Creare `LessonGroupViewSet` in un nuovo file `lezioni/views/group_views.py`.
    - [x] Registrare il nuovo `LessonGroupViewSet` in `lezioni/urls.py`.

### 1.2 Modifiche Frontend (Vue.js)

- **Store (Pinia):**
    - [x] Aggiungere lo stato `lessonGroups` e `isLoadingLessonGroups` in `frontend-lessons/src/stores/lessons.ts`.
    - [x] Aggiungere le azioni per CRUD sui gruppi (`fetchLessonGroups`, `createLessonGroup`, `deleteLessonGroup`).
    - [x] Aggiungere le azioni per assegnare/rimuovere lezioni dai gruppi (`assignLessonsToGroup`, `removeLessonFromGroup`).
- **Tipi (TypeScript):**
    - [x] Creare l'interfaccia `LessonGroup` in `frontend-lessons/src/types/lezioni.ts`.
    - [x] Aggiornare l'interfaccia `Lesson` per includere il campo opzionale `group`.
- **UI (Viste/Componenti):**
    - [x] Aggiornare `TeacherLessonListView.vue` per mostrare i gruppi.
    - [x] Implementare la selezione multipla delle lezioni.
    - [x] Creare una modale per la creazione/nomina del gruppo.
    - [x] Aggiungere i controlli per espandere/collassare, eliminare un gruppo e rimuovere una lezione da un gruppo.

## 2. Miglioramenti Successivi

Oltre al piano iniziale, sono state implementate le seguenti funzionalità aggiuntive per migliorare l'esperienza utente:

- **Evidenziazione Gruppo Espanso**: [x] Aggiunto un bordo CSS per distinguere visivamente i gruppi espansi.
- **Assegnazione a Gruppo Esistente**: [x] Creata la modale `AssignToGroupModal.vue` e integrata la logica per aggiungere lezioni a gruppi preesistenti.
- **Rimozione Multipla da Gruppo**: [x] Aggiunta la possibilità di rimuovere più lezioni da un gruppo con un'unica azione.
- **Eliminazione Automatica Gruppi Vuoti**: [x] Implementata la logica nello store per cui un gruppo viene eliminato se rimane senza lezioni.
- **Gestione Errori Migliorata**: [x] Modificata la creazione dei gruppi per gestire errori (es. nomi duplicati) tramite notifiche specifiche.

## 3. Stato Attuale e Problemi Aperti

### Completato

- **Backend**: Tutte le funzionalità del backend sono complete e funzionanti.
- **Frontend**: Tutte le funzionalità dell'interfaccia utente e la logica dello store Pinia sono state implementate come da piano iniziale e successivi miglioramenti.

### Problema da Risolvere

- **Errore di Tipo in `TeacherLessonListView.vue`**:
  - **Descrizione**: L'ultima modifica alla gestione degli errori nello store (`lessons.ts`) ha causato una desincronizzazione con il componente `TeacherLessonListView.vue`. Il componente non interpreta correttamente la nuova struttura dati restituita dalla funzione `createLessonGroup`, generando un errore di compilazione TypeScript che blocca il rendering.
  - **Obiettivo**: Risolvere l'errore di tipo nel componente per allinearlo alla logica aggiornata dello store e rendere l'applicazione nuovamente funzionante.