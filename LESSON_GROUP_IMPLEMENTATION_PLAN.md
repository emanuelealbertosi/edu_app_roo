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

## 2. Stato Attuale

### Completato

- **Backend:** Tutte le modifiche pianificate per il backend (modelli, serializers, viste, URL) sono state completate.
- **Tipi Frontend:** I tipi TypeScript (`LessonGroup`, `Lesson`) sono stati aggiornati.
- **Frontend Store (Pinia):** Lo store `lessons.ts` è stato aggiornato con successo con la logica per i gruppi di lezioni.
- **Branch Git:** È stato creato e stiamo lavorando sul branch `lessonsgroup`.

### Da Fare

- **Frontend UI:** Tutta la parte di interfaccia utente è stata implementata con successo.

## 3. Lavoro Completato

L'implementazione della funzionalità di raggruppamento delle lezioni è completa. Sono state apportate le seguenti modifiche all'interfaccia utente in `TeacherLessonListView.vue`:
- Aggiunta la selezione multipla delle lezioni tramite checkbox.
- Creata e integrata una modale (`LessonGroupModal.vue`) per la creazione di nuovi gruppi.
- Implementata la logica per assegnare le lezioni selezionate a un nuovo gruppo.
- Aggiunti i controlli per eliminare un intero gruppo o rimuovere una singola lezione da un gruppo.
Tutte le attività pianificate sono state completate.