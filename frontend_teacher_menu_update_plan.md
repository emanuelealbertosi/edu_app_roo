# Piano di Modifica del Menu in `frontend-teacher` (Confermato)

**Data:** 26 Maggio 2025
**Autore:** Roo (Architect AI)
**Obiettivo:** Riorganizzare il menu di navigazione nell'applicazione `frontend-teacher`, introducendo sezioni contraibili per "Gestisci Quiz" e "Gestione Didattica", con entrambe che nascono contratte.

**File da Modificare:** `frontend-teacher/src/App.vue`

**Icone Scelte:**
*   "Gestisci Quiz": `WrenchScrewdriverIcon`
*   Indicatori Espandi/Contrai: `ChevronUpIcon` / `ChevronDownIcon`

**Passaggi di Implementazione:**

## 1. Modifiche alla Sezione `<script setup lang="ts">`

1.  **Importare Nuove Icone:**
    *   Aggiungere `ChevronUpIcon`, `ChevronDownIcon` e `WrenchScrewdriverIcon` da `@heroicons/vue/24/outline`.
    ```typescript
    import {
      // ... altre icone ...
      ChevronUpIcon,
      ChevronDownIcon,
      WrenchScrewdriverIcon,
      // ... altre icone ...
    } from '@heroicons/vue/24/outline';
    ```

2.  **Definire Stati per le Sezioni Contraibili:**
    *   Aggiungere due nuove variabili reattive (`ref`) per gestire lo stato (espanso/contratto) delle nuove sezioni. Entrambe devono iniziare come `false` (contratte).
    ```typescript
    const isManageQuizExpanded = ref(false);
    const isGestioneDidatticaExpanded = ref(false);
    ```

3.  **Definire Funzioni per Commutare lo Stato:**
    *   Aggiungere funzioni per commutare lo stato di espansione delle sezioni.
    ```typescript
    const toggleManageQuiz = () => {
      isManageQuizExpanded.value = !isManageQuizExpanded.value;
    };

    const toggleGestioneDidattica = () => {
      isGestioneDidatticaExpanded.value = !isGestioneDidatticaExpanded.value;
    };
    ```

## 2. Modifiche alla Sezione `<template>` (Navigazione Desktop e Mobile)

Le modifiche andranno replicate in modo simile sia per la navigazione Desktop (a partire da riga `320` circa del file `App.vue`) sia per quella Mobile (a partire da riga `475` circa).

1.  **Riorganizzazione Generale delle Voci di Menu:**
    *   Spostare le voci esistenti secondo il nuovo ordine.

2.  **Implementazione Sezione "Gestisci Quiz" (Contraibile):**
    *   Posizionare questa sezione dopo "Sfoglia Gruppi".
    *   L'elemento `<li>` principale sarà cliccabile per espandere/contrarre.
    *   Utilizzare `v-if="isManageQuizExpanded"` per mostrare/nascondere le sotto-voci "Quiz Templates" e "Quiz Assegnati".

    ```html
    <!-- Dopo Sfoglia Gruppi -->
    <li class="mb-2">
      <button @click="toggleManageQuiz" class="flex items-center justify-between w-full p-2 rounded hover:bg-secondary-light" title="Gestisci Quiz" :aria-expanded="isManageQuizExpanded.toString()">
        <div class="flex items-center">
          <WrenchScrewdriverIcon class="h-5 w-5 flex-shrink-0" />
          <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Gestisci Quiz</span>
        </div>
        <ChevronDownIcon v-if="!isManageQuizExpanded" class="h-4 w-4 flex-shrink-0 transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }" />
        <ChevronUpIcon v-else class="h-4 w-4 flex-shrink-0 transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }" />
      </button>
      <ul v-if="isManageQuizExpanded" class="pl-4 mt-1">
        <!-- Quiz Templates -->
        <li class="mb-2">
          <router-link :to="{ name: 'quiz-templates' }" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Quiz Templates">
            <ClipboardDocumentListIcon class="h-5 w-5 flex-shrink-0" />
            <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Quiz Templates</span>
          </router-link>
        </li>
        <!-- Quiz Assegnati -->
        <li class="mb-2">
          <router-link :to="{ name: 'assigned-quizzes' }" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Quiz Assegnati">
            <ClipboardDocumentCheckIcon class="h-5 w-5 flex-shrink-0" />
            <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Quiz Assegnati</span>
          </router-link>
        </li>
      </ul>
    </li>
    ```

3.  **Modifica Sezione "Gestione Didattica" (Contraibile):**
    *   Trasformare l'attuale titolo della sezione (attorno a riga `413` del file `App.vue`) in un elemento cliccabile.
    *   Utilizzare `v-if="isGestioneDidatticaExpanded"` per mostrare/nascondere le sotto-voci.

    ```html
    <!-- Sezione Gestione Didattica -->
    <li class="mt-4 mb-1">
      <button @click="toggleGestioneDidattica" class="flex items-center justify-between w-full p-2 rounded hover:bg-secondary-light" title="Gestione Didattica" :aria-expanded="isGestioneDidatticaExpanded.toString()">
        <span class="text-xs font-semibold text-neutral-400 whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Gestione Didattica</span>
        <ChevronDownIcon v-if="!isGestioneDidatticaExpanded" class="h-4 w-4 flex-shrink-0 text-neutral-400 transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }" />
        <ChevronUpIcon v-else class="h-4 w-4 flex-shrink-0 text-neutral-400 transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }" />
      </button>
      <ul v-if="isGestioneDidatticaExpanded" class="pl-4 mt-1">
        <li class="mb-2">
          <router-link :to="{ name: 'EmbeddedTeacherSubjects' }" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Materie">
            <TagIcon class="h-5 w-5 flex-shrink-0" />
            <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Materie</span>
          </router-link>
        </li>
        <li class="mb-2">
          <router-link :to="{ name: 'EmbeddedTeacherTopics' }" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Argomenti">
            <LightBulbIcon class="h-5 w-5 flex-shrink-0" />
            <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Argomenti</span>
          </router-link>
        </li>
        <li class="mb-2">
          <router-link :to="{ name: 'EmbeddedTeacherLessonsList' }" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Lezioni">
            <AcademicCapIcon class="h-5 w-5 flex-shrink-0" />
            <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Lezioni</span>
          </router-link>
        </li>
        <li class="mb-2">
          <router-link :to="{ name: 'EmbeddedTeacherCourses' }" class="flex items-center p-2 rounded hover:bg-secondary-light" title="Corsi">
            <FolderIcon class="h-5 w-5 flex-shrink-0" />
            <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">Corsi</span>
          </router-link>
        </li>
        <li class="mb-2">
          <router-link :to="{ name: 'EmbeddedTeacherUdas' }" class="flex items-center p-2 rounded hover:bg-secondary-light" title="UDA">
            <PuzzlePieceIcon class="h-5 w-5 flex-shrink-0" />
            <span class="ml-3 text-sm whitespace-nowrap transition-opacity duration-200 ease-in-out" :class="{ 'opacity-100': isEffectivelyExpanded, 'opacity-0': !isEffectivelyExpanded }">UDA</span>
          </router-link>
        </li>
      </ul>
    </li>
    ```

4.  **Adattamenti per Menu Mobile:**
    *   La logica di `toggleManageQuiz` e `toggleGestioneDidattica` sarà la stessa.
    *   Gli elementi cliccabili e la visualizzazione condizionale (`v-if`) delle sotto-voci andranno implementati in modo simile all'interno della struttura del menu mobile.

## Diagramma Mermaid (Struttura Menu Post-Modifica)

```mermaid
graph TD
    A[Dashboard]
    B[Studenti]
    C[Gruppi]
    D[Sfoglia Gruppi]
    E[Gestisci Quiz (Contraibile)]
    E1[-- Quiz Templates --]
    E2[-- Quiz Assegnati --]
    F[Ricompense]
    G[Valutazioni]
    H[Consegne]
    I[Progressi]
    J[Gestione Didattica (Contraibile)]
    J1[-- Materie --]
    J2[-- Argomenti --]
    J3[-- Lezioni --]
    J4[-- Corsi --]
    J5[-- UDA --]

    A --> B
    B --> C
    C --> D
    D --> E
    E -- Contr./Esp. --> E1
    E -- Contr./Esp. --> E2
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J -- Contr./Esp. --> J1
    J -- Contr./Esp. --> J2
    J -- Contr./Esp. --> J3
    J -- Contr./Esp. --> J4
    J -- Contr./Esp. --> J5