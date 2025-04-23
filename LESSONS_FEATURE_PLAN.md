# Piano di Progettazione Dettagliato: Funzionalità Lezioni

**Obiettivo:** Integrare una nuova sezione "Lezioni" nell'applicazione educativa Django, permettendo ai Docenti di creare lezioni con contenuti multimediali (PDF, PPT, HTML), organizzarle per materia/argomento e assegnarle agli Studenti. Verrà creato un frontend Vue.js dedicato (`frontend-lessons`) accessibile sia da Studenti che Docenti, con autenticazione condivisa tramite il backend.

**Specifiche Chiave:**

*   **Gestione Materie/Argomenti:** Sia Admin che Docenti.
*   **Editor HTML:** Sostituito WYSIWYG con `<textarea>` per permettere l'inserimento di HTML grezzo (inclusi `<script>`) senza sanitizzazione lato editor. **[FATTO - Modifica]**
*   **Visualizzazione File:** Incorporata con opzione di download per PDF/PPT. Aggiunta opzione download per contenuto HTML nella modale di visualizzazione. **[FATTO - Modifica]**
*   **Frontend Dedicato:** Nuova applicazione Vue.js (`frontend-lessons`). I frontend attuali (`frontend-student`, `frontend-teacher`) avranno solo un link a questa nuova applicazione.

---

## 1. Modifiche al Backend (Django)

*   **Nuova App Django:** Creata app `lezioni` nella root del progetto (a causa di conflitti con `startapp` nella dir `apps/`). **[FATTO]**
    *   Aggiunto `'lezioni.apps.LezioniConfig'` a `INSTALLED_APPS` in `config/settings.py`. **[FATTO]**
*   **Modelli (`lezioni/models.py`):** Definiti e creati. **[FATTO]**
    ```python
    from django.db import models
    from django.conf import settings
    # Assumendo che il modello Studente sia in apps.users.models
    # Se Student è definito altrove, questo import dovrà essere aggiornato.
    # Potrebbe essere necessario verificare la struttura effettiva di apps.users
    try:
        from apps.users.models import Student
    except ImportError:
        # Fallback o gestione alternativa se la struttura è diversa
        # Per ora, assumiamo che Student sia accessibile così o che
        # la relazione verrà definita usando stringhe se necessario.
        # Questo potrebbe richiedere aggiustamenti futuri.
        Student = settings.AUTH_USER_MODEL # Placeholder temporaneo se Student non trovato

    class Subject(models.Model):
        name = models.CharField(max_length=200, unique=True)
        description = models.TextField(blank=True)
        # Permette sia Admin che Docenti (verificare permessi nelle view)
        creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_subjects')
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        def __str__(self):
            return self.name

        class Meta:
            verbose_name = "Materia"
            verbose_name_plural = "Materie"

    class Topic(models.Model):
        name = models.CharField(max_length=200)
        description = models.TextField(blank=True)
        subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')
        # Permette sia Admin che Docenti (verificare permessi nelle view)
        creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_topics')
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)

        class Meta:
            unique_together = ('name', 'subject') # Un argomento deve essere unico all'interno di una materia
            verbose_name = "Argomento"
            verbose_name_plural = "Argomenti"

        def __str__(self):
            # Gestisce il caso in cui subject sia None (anche se non dovrebbe accadere con CASCADE)
            subject_name = self.subject.name if self.subject else "N/A"
            return f"{subject_name} - {self.name}"

    class Lesson(models.Model):
        title = models.CharField(max_length=255)
        description = models.TextField(blank=True)
        # Protegge dalla cancellazione dell'argomento se ci sono lezioni collegate
        topic = models.ForeignKey(Topic, on_delete=models.PROTECT, related_name='lessons')
        # Solo Docente può creare lezioni (verificare permessi nelle view)
        creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_lessons')
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)
        is_published = models.BooleanField(default=False, help_text="Se la lezione è visibile agli studenti assegnati.")

        def __str__(self):
            return self.title

        class Meta:
            verbose_name = "Lezione"
            verbose_name_plural = "Lezioni"

    def lesson_content_upload_path(instance, filename):
        # Salva i file in mediafiles/lezioni_contenuti/<lesson_id>/<filename>
        # Usiamo 'lezioni_contenuti' per evitare conflitti con il nome dell'app
        return f'lezioni_contenuti/{instance.lesson.id}/{filename}'

    class LessonContent(models.Model):
        CONTENT_TYPES = [
            ('html', 'Contenuto HTML'),
            ('pdf', 'Documento PDF'),
            ('ppt', 'Presentazione PPT/PPTX'),
            ('url', 'Link Esterno'),
            # ('video', 'File Video'), # Esempio futuro
            # ('image', 'File Immagine'), # Esempio futuro
        ]
        lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='contents')
        content_type = models.CharField(max_length=10, choices=CONTENT_TYPES, verbose_name="Tipo di Contenuto")
        # Usare un campo per l'editor avanzato, es. CKEditor (da configurare separatamente)
        html_content = models.TextField(blank=True, help_text="Usare per Contenuto HTML.", verbose_name="Contenuto HTML")
        # FileField per PDF, PPT, ecc.
        file = models.FileField(upload_to=lesson_content_upload_path, blank=True, null=True, help_text="Usare per PDF, PPT, ecc.", verbose_name="File Caricato")
        url = models.URLField(blank=True, help_text="Usare per Link Esterno.", verbose_name="URL Esterno")
        title = models.CharField(max_length=255, blank=True, help_text="Titolo opzionale per questo blocco di contenuto", verbose_name="Titolo Contenuto")
        order = models.PositiveIntegerField(default=0, help_text="Ordine di visualizzazione nella lezione.", verbose_name="Ordine")
        created_at = models.DateTimeField(auto_now_add=True)

        class Meta:
            ordering = ['order']
            verbose_name = "Contenuto Lezione"
            verbose_name_plural = "Contenuti Lezione"

        def __str__(self):
             lesson_title = self.lesson.title if self.lesson else "N/A"
             return f"Contenuto per '{lesson_title}' ({self.get_content_type_display()}) - Ordine: {self.order}"

    class LessonAssignment(models.Model):
        lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='assignments')
        # Assicurarsi che l'import di Student sia corretto
        student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lesson_assignments')
        # Docente che ha assegnato
        assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='made_lesson_assignments')
        assigned_at = models.DateTimeField(auto_now_add=True)
        viewed_at = models.DateTimeField(null=True, blank=True, help_text="Data e ora prima visualizzazione da parte dello studente")

        class Meta:
            unique_together = ('lesson', 'student') # Uno studente può essere assegnato a una lezione solo una volta
            ordering = ['-assigned_at']
            verbose_name = "Assegnazione Lezione"
            verbose_name_plural = "Assegnazioni Lezioni"

        def __str__(self):
            # Tentativo di ottenere un nome rappresentativo per lo studente
            student_name = "N/A"
            if self.student:
                 # Prova diversi attributi comuni per rappresentare lo studente
                 student_name = getattr(self.student, 'unique_identifier', None) or \
                                getattr(self.student, 'full_name', None) or \
                                getattr(self.student, 'username', None) or \
                                f"ID: {self.student.id}"

            lesson_title = self.lesson.title if self.lesson else "N/A"
            return f"'{lesson_title}' assegnata a {student_name}"
    ```
*   **Migrazioni:** Create ed eseguite (`makemigrations lezioni`, `migrate`). **[FATTO]**
*   **API (DRF):**
    *   **Struttura View:** Creata directory `lezioni/views/` con file separati (`subject_views.py`, `topic_views.py`, `lesson_views.py`, `assignment_views.py`) e `__init__.py`. **[FATTO]**
    *   **Serializers (`lezioni/serializers.py`):** Creati Serializers base per tutti i modelli. **[FATTO]**
    *   **Views (`lezioni/views/*.py`):** Implementati ViewSets base per `Subject`, `Topic`, `Lesson`, `LessonContent`, `LessonAssignment`. **[FATTO]**
    *   **Permessi (`lezioni/permissions.py`):** Definiti permessi custom base (`IsAdminOrTeacher`, `IsTeacherOwner`, `IsAdminOrTeacherOwner`, `IsAssignedStudentOrTeacherOwner`). Corretto `IsTeacherOwner` per verificare `obj.lesson.creator` su `LessonContent`. **[FATTO - Fix]**
    *   **URLs (`lezioni/urls.py`):** Definiti URL con `DefaultRouter` e `NestedSimpleRouter`. Incluso in `config/urls.py` sotto `/api/lezioni/`. **[FATTO]**
    *   **Endpoint Principali:** (Implementati tramite ViewSet/Router)
        *   `/api/lezioni/subjects/` **[FATTO]**
        *   `/api/lezioni/topics/` **[FATTO]**
        *   `/api/lezioni/lessons/` **[FATTO]**
        *   `/api/lezioni/lessons/{lesson_pk}/contents/` **[FATTO]**
        *   `/api/lezioni/lessons/{lesson_pk}/assign/` (Azione custom) **[FATTO]**
        *   `/api/lezioni/assignments/` (Filtrato per studente/docente/admin nel ViewSet) **[FATTO]**
        *   `/api/lezioni/assignments/{assignment_pk}/mark-viewed/` (Azione custom) **[FATTO]**
*   **Fix Autenticazione:** Disabilitato `UPDATE_LAST_LOGIN` in `settings.py` per risolvere errore 500. **[FATTO]**
*   **Editor HTML Avanzato:** Integrare `django-ckeditor` (o simile) per `LessonContent.html_content`. **[DA FARE]**
*   **Configurazione Media:** Verificare `MEDIA_URL` e `MEDIA_ROOT` in `settings.py`. **[DA FARE - VERIFICARE]**

---

## 2. Nuovo Frontend (`frontend-lessons` - Vue.js 3)

*   **Setup Progetto:**
    *   Creata directory `frontend-lessons`. **[FATTO - VERIFICATO]**
    *   Inizializzato progetto Vue 3 + TypeScript + Vite. **[FATTO - VERIFICATO]**
    *   Installati: `vue-router`, `pinia`, `axios`, `@types/node`. **[FATTO - VERIFICATO]**
    *   Configurati alias `@` in `tsconfig.app.json` e `vite.config.ts`. **[FATTO - VERIFICATO]**
    *   Installati: editor WYSIWYG (TipTap), visualizzatore PDF (vue-pdf-embed), libreria UI (Tailwind CSS). **[FATTO - VERIFICATO]**
*   **Autenticazione:**
    *   Gestione token JWT in `localStorage`. **[FATTO - VERIFICATO]**
    *   Interceptor `axios` per header `Authorization`. **[FATTO - VERIFICATO]**
    *   Viste di login separate (`TeacherAdminLoginView.vue`, `StudentLoginView.vue`) che usano gli endpoint corretti e logica store aggiornata. **[FATTO - VERIFICATO]**
*   **Routing (`src/router/index.ts`):**
    *   Configurazione base con `vue-router`. **[FATTO - VERIFICATO]**
    *   Route definite per: Login (Docente/Admin, Studente), Dashboard, Gestione Materie, Gestione Argomenti, Lista Lezioni Docente, Lista Lezioni Studente, Dettaglio Lezione. **[FATTO - VERIFICATO]**
    *   Route guards base implementate per `requiresAuth` e `requiresGuest`. **[FATTO - VERIFICATO]**
    *   Route per Gestione Contenuti (`lesson-contents`) e Assegnazione Lezione (`lesson-assign`) definite. **[FATTO - VERIFICATO]**
*   **Store (Pinia - `src/stores/`):**
    *   `auth.ts` creato e funzionante per entrambi i tipi di login. **[FATTO - VERIFICATO]**
    *   `subjects.ts` creato con azioni CRUD base. **[FATTO - VERIFICATO]**
    *   `topics.ts` creato con azioni CRUD base e filtro. **[FATTO - VERIFICATO]**
    *   `lessons.ts` creato con azioni CRUD base per lezioni, contenuti e assegnazioni. **[FATTO - VERIFICATO]**
*   **Viste (`src/views/`):**
    *   `TeacherAdminLoginView.vue` creata. **[FATTO - VERIFICATO]**
    *   `StudentLoginView.vue` creata. **[FATTO - VERIFICATO]**
    *   `DashboardView.vue` creata (placeholder). **[FATTO - VERIFICATO]**
    *   `SubjectListView.vue` creata. **[FATTO - VERIFICATO]**
    *   `TopicListView.vue` creata. **[FATTO - VERIFICATO]**
    *   `TeacherLessonListView.vue` creata. **[FATTO - VERIFICATO]**
    *   `StudentLessonListView.vue` creata. **[FATTO - VERIFICATO]**
    *   `LessonDetailView.vue` creata. **[FATTO - VERIFICATO]**
    *   `LessonContentView.vue` creata (gestione contenuti). **[FATTO - VERIFICATO]**
    *   `LessonAssignView.vue` creata. **[FATTO - VERIFICATO]**
*   **Componenti (`src/components/`):**
    *   `SubjectEditModal.vue` creato. **[FATTO - VERIFICATO]**
    *   `TopicEditModal.vue` creato. **[FATTO - VERIFICATO]**
    *   `LessonEditModal.vue` creato. **[FATTO - VERIFICATO]**
    *   `LessonContentDisplay.vue` creato. **[FATTO - VERIFICATO]**
    *   `LessonContentEditModal.vue` creato. Modificato per usare `<textarea>` invece di `WysiwygEditor` per il tipo 'html'. **[FATTO - Modifica]**
    *   Creati e integrati: `WysiwygEditor.vue` (non più usato per HTML), `PdfViewer.vue`. **[FATTO - VERIFICATO]**
    *   Aggiunto pulsante e logica per download contenuto HTML in `LessonDetailView.vue`. **[FATTO - Modifica]**
*   **Stile:** Applicati stili base con Tailwind CSS. **[FATTO - BASE]** (Da migliorare e rendere coerenti)

---

## 3. Modifiche ai Frontend Esistenti (`frontend-student`, `frontend-teacher`)

*   Aggiungere un link/pulsante che punti all'URL della nuova applicazione `frontend-lessons` (es. `/lessons/`). **[FATTO]**

---

## 4. Aggiornamento Documentazione (`design_document.md`)

*   **Schema Database:** Aggiungere i nuovi modelli e relazioni al diagramma Mermaid. **[DA FARE - AGGIORNARE DOC]**
    ```mermaid
    erDiagram
        USER ||--o{ SUBJECT : "creato_da"
        USER ||--o{ TOPIC : "creato_da"
        USER ||--o{ LESSON : "creato_da (Docente)"
        USER ||--o{ LESSON_ASSIGNMENT : "assegnato_da (Docente)"

        SUBJECT ||--o{ TOPIC : "contiene"

        TOPIC ||--o{ LESSON : "appartiene_a"

        LESSON ||--o{ LESSON_CONTENT : "contiene"
        LESSON ||--o{ LESSON_ASSIGNMENT : "ha_assegnazioni"

        STUDENT ||--o{ LESSON_ASSIGNMENT : "assegnato_a"

        SUBJECT {
            int id PK
            string name UK
            string description
            int creator_id FK "(Admin/Docente)"
            datetime created_at
            datetime updated_at
        }

        TOPIC {
            int id PK
            string name
            string description
            int subject_id FK
            int creator_id FK "(Admin/Docente)"
            datetime created_at
            datetime updated_at
            UK (name, subject_id)
        }

        LESSON {
            int id PK
            string title
            string description
            int topic_id FK
            int creator_id FK "(Docente)"
            datetime created_at
            datetime updated_at
            bool is_published
        }

        LESSON_CONTENT {
            int id PK
            int lesson_id FK
            string content_type "'html', 'pdf', 'ppt', 'url', ..."
            string html_content "(for HTML)"
            string file "(for PDF, PPT)"
            string url "(for URL)"
            string title
            int order
            datetime created_at
        }

        LESSON_ASSIGNMENT {
            int id PK
            int lesson_id FK
            int student_id FK
            int assigned_by_id FK "(Docente)"
            datetime assigned_at
            datetime viewed_at NULL
            UK (lesson_id, student_id)
        }

        # ... (altri modelli esistenti) ...
    ```
*   **API REST:** Aggiungere la sezione per gli endpoint `/api/lezioni/`. **[DA FARE - AGGIORNARE DOC]**
*   **Architettura:** Menzionare la nuova app Django `lezioni` (nella root) e il frontend `frontend-lessons`. **[DA FARE - AGGIORNARE DOC]**

---
## 5. Uniformazione Layout Frontend e Correzione Link

*   **Obiettivo:** Rendere coerente l'interfaccia principale (menu/navigazione) tra `frontend-lessons`, `frontend-student` e `frontend-teacher`. Correggere i link tra le applicazioni.
*   **Modifiche Apportate:**
    *   **Refactoring Layout:** I file `App.vue` di `frontend-student` e `frontend-teacher` sono stati riscritti per adottare la struttura di `frontend-lessons`:
        *   Barra laterale sinistra espandibile/collassabile per la navigazione principale.
        *   Header superiore con barra di ricerca (placeholder in `lessons`), pulsanti Notifiche e Profilo.
    *   **Link Inter-App:**
        *   Tutti i link tra le tre applicazioni frontend (`lessons`, `student`, `teacher`) ora utilizzano variabili d'ambiente (`VITE_LESSONS_APP_URL`, `VITE_STUDENT_APP_URL`, `VITE_TEACHER_APP_URL`) definite nei file `.env.local` e `.env.docker`.
        *   Le configurazioni di Vite (`vite.config.ts`) di tutti e tre i frontend sono state aggiornate con `envDir: '../'` per garantire la lettura corretta dei file `.env` dalla root del progetto.
        *   Corrette discrepanze nei nomi delle rotte (`Profile`, `Badges`) in `frontend-student/src/App.vue`.
        *   Corretta la condizione `v-if` per il link "Gestione Quiz" in `frontend-lessons/src/App.vue` per usare il ruolo corretto (`TEACHER`).
    *   **Link Profilo:** Il link alla pagina "Profilo" è stato spostato dalla barra laterale all'icona utente nell'header in `frontend-student` e `frontend-teacher`. Il click diretto sull'icona ora porta alla pagina del profilo.
    *   **Visibilità Layout:** La barra laterale e l'header sono ora correttamente nascosti nelle pagine pubbliche (es. login) e mostrati solo per gli utenti autenticati in tutti e tre i frontend, grazie all'uso della proprietà calcolata `showLayout` (o `authStore.isAuthenticated` in `lessons`).
    *   **Dipendenze:** Aggiunto `@heroicons/vue` a `frontend-teacher`.
*   **Stato:** **[FATTO]**
---
## 6. Bug Fixes Recenti

*   **Obiettivo:** Risolvere problemi emersi durante l'implementazione e il test iniziale.
*   **Modifiche Apportate:**
    *   **Creazione Lezione:** Risolto bug per cui la creazione di una nuova lezione modificava quella esistente. Causa: `id` non era `read_only` in `LessonWriteSerializer`. Soluzione: Aggiunto `read_only_fields = ['id']` a `LessonWriteSerializer` in `lezioni/serializers.py`. **[FATTO - Fix]**
    *   **Assegnazione Lezione (Errore 500):** Risolto `AttributeError: 'Lesson' object has no attribute 'lesson'` che si verificava durante il controllo dei permessi per l'assegnazione. Causa: Errore nel permesso `IsTeacherOwner`. Soluzione: Corretto il controllo in `lezioni/permissions.py` da `obj.lesson.creator == request.user` a `obj.creator == request.user`. **[FATTO - Fix]**
    *   **Eliminazione Lezione (Errore 403):** Risolto errore di permesso che impediva l'eliminazione. Causa: Confronto case-sensitive dei ruoli nel permesso `IsAdminOrTeacherOwner`. Soluzione: Modificato il controllo in `lezioni/permissions.py` per usare `.upper()` e verificare `ADMIN` e `TEACHER`. **[FATTO - Fix]**
    *   **UI Menu Docente:** Risolto problema per cui il link "Gestione Lezioni" non appariva. Causa: La condizione `v-if` in `frontend-lessons/src/App.vue` controllava `authStore.userRole === 'Docente'` invece di `authStore.userRole === 'TEACHER'`. Soluzione: Aggiornata la condizione `v-if` per usare `'TEACHER'`. **[FATTO - Fix]**
    *   **UI Etichetta Filtro Argomenti:** Corretta l'etichetta del filtro materia nella vista elenco argomenti. Causa: Etichetta errata in `frontend-lessons/src/views/TopicListView.vue`. Soluzione: Modificata l'etichetta da "Filtra per Materia:" a "Seleziona materia:". **[FATTO - Fix]**
*   **Stato:** **[FATTO]**