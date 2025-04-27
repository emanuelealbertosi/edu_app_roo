import { defineStore } from 'pinia';
import apiClient, { fetchGroups, assignLesson } from '@/services/api'; // Importa l'istanza Axios e le funzioni API specifiche
import type { Lesson, LessonContent, LessonAssignment, Student, AssignmentResult } from '@/types/lezioni'; // Importa i tipi definiti
import type { StudentGroup } from '@/types/groups'; // Importa il tipo per i gruppi

// Le interfacce locali sono state rimosse, usiamo quelle importate da @/types/lezioni.ts


export const useLessonStore = defineStore('lessons', {
  state: () => ({
    lessons: [] as Lesson[], // Lista lezioni (es. quelle create dal docente)
    assignedLessons: [] as LessonAssignment[], // Lezioni assegnate allo studente
    currentLesson: null as Lesson | null, // Lezione attualmente visualizzata/modificata
    isLoading: false,
    isLoadingContents: false, // Loading specifico per i contenuti
    isLoadingAssignments: false, // Loading specifico per le assegnazioni
    groups: [] as StudentGroup[], // Lista dei gruppi disponibili per l'assegnazione
    isLoadingGroups: false, // Loading specifico per i gruppi
    error: null as string | null,
  }),

  getters: {
    // Getter per trovare una lezione per ID nello stato locale
    getLessonById: (state) => {
      return (lessonId: number): Lesson | undefined => {
        // Cerca prima nella lezione corrente, poi nella lista generale
        if (state.currentLesson?.id === lessonId) {
            return state.currentLesson;
        }
        return state.lessons.find(lesson => lesson.id === lessonId);
      }
    },
  },

  actions: {
    // --- Azioni Lezioni ---
    async fetchLessons(topicId: number | null = null) { // Filtro opzionale per argomento
      this.isLoading = true;
      this.error = null;
      // Aggiunto prefisso /lezioni/
      let url = '/lezioni/lessons/';
       if (topicId !== null) {
        url += `?topic_id=${topicId}`; // Endpoint backend deve supportare questo filtro
      }
      try {
        // Questo endpoint restituirà le lezioni in base ai permessi (es. solo quelle del docente)
        const response = await apiClient.get(url);
        this.lessons = response.data;
      } catch (err: any) {
        console.error("Errore nel caricamento delle lezioni:", err);
        this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
        this.lessons = [];
      } finally {
        this.isLoading = false;
      }
    },

    // Rinominata da fetchLessonDetail a fetchLesson
    async fetchLesson(lessonId: number) {
      this.isLoading = true;
      this.error = null;
      this.currentLesson = null; // Resetta prima di caricare
      try {
        // Aggiunto prefisso /lezioni/
        const response = await apiClient.get(`/lezioni/lessons/${lessonId}/`);
        // Il serializer LessonSerializer dovrebbe includere i contenuti in lettura
        this.currentLesson = response.data;
      } catch (err: any) {
        console.error(`Errore nel caricamento dettaglio lezione ${lessonId}:`, err);
        this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
      } finally {
        this.isLoading = false;
      }
    },

    async addLesson(lessonData: { title: string; topic: number; description?: string; is_published?: boolean }) {
      this.isLoading = true;
      this.error = null;
      try {
        // Usa l'endpoint e il LessonWriteSerializer (senza contents)
        // Aggiunto prefisso /lezioni/
        const response = await apiClient.post('/lezioni/lessons/', lessonData);
        this.lessons.push(response.data); // Aggiunge alla lista locale
        return response.data as Lesson; // Restituisce la lezione creata
      } catch (err: any) {
        console.error("Errore nell'aggiunta della lezione:", err);
        this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
        return null;
      } finally {
        this.isLoading = false;
      }
    },

    async updateLesson(lessonId: number, lessonData: { title?: string; topic?: number; description?: string; is_published?: boolean }) {
        this.isLoading = true;
        this.error = null;
        try {
            // Usa PATCH e LessonWriteSerializer
            // Aggiunto prefisso /lezioni/
            const response = await apiClient.patch(`/lezioni/lessons/${lessonId}/`, lessonData);
            // Aggiorna la lista locale
            const index = this.lessons.findIndex(l => l.id === lessonId);
            if (index !== -1) {
                this.lessons[index] = { ...this.lessons[index], ...response.data };
            }
            // Aggiorna anche currentLesson se è quella modificata
            if (this.currentLesson?.id === lessonId) {
                 this.currentLesson = { ...this.currentLesson, ...response.data };
            }
            return true;
        } catch (err: any) {
            console.error("Errore nell'aggiornamento della lezione:", err);
            this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
            return false;
        } finally {
            this.isLoading = false;
        }
    },

     async deleteLesson(lessonId: number) {
        this.isLoading = true;
        this.error = null;
        try {
            // Aggiunto prefisso /lezioni/
            await apiClient.delete(`/lezioni/lessons/${lessonId}/`);
            this.lessons = this.lessons.filter(l => l.id !== lessonId);
            if (this.currentLesson?.id === lessonId) {
                this.currentLesson = null;
            }
            return true;
        } catch (err: any) {
            console.error("Errore nell'eliminazione della lezione:", err);
            this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
            return false;
        } finally {
            this.isLoading = false;
        }
    },

    // --- Azioni Contenuti Lezione (usano URL annidato) ---
    // Nota: lo stato dei contenuti è gestito dentro currentLesson.contents

    async addLessonContent(lessonId: number, contentData: FormData | { content_type: string; html_content?: string; url?: string; title?: string; order?: number }) {
        this.isLoadingContents = true; // Usa loading specifico
        this.error = null;
        try {
            // Determina se inviare come FormData (per file) o JSON
            const headers = contentData instanceof FormData
                ? { 'Content-Type': 'multipart/form-data' }
                : { 'Content-Type': 'application/json' };

            // Aggiunto prefisso /lezioni/
            const response = await apiClient.post(`/lezioni/lessons/${lessonId}/contents/`, contentData, { headers });

            // Aggiorna i contenuti della lezione corrente se caricata
            if (this.currentLesson?.id === lessonId) {
                if (!this.currentLesson.contents) this.currentLesson.contents = [];
                this.currentLesson.contents.push(response.data);
                // Riordina se necessario
                this.currentLesson.contents.sort((a, b) => a.order - b.order);
            }
            return response.data as LessonContent;
        } catch (err: any) {
            console.error("Errore nell'aggiunta del contenuto:", err);
            this.error = err.response?.data?.detail || JSON.stringify(err.response?.data) || err.message || 'Errore sconosciuto';
            return null;
        } finally {
            this.isLoadingContents = false;
        }
    },

    async updateLessonContent(lessonId: number, contentId: number, contentData: FormData | { content_type?: string; html_content?: string; url?: string; title?: string; order?: number; file?: File | null }) {
        this.isLoadingContents = true;
        this.error = null;
        try {
             const headers = contentData instanceof FormData
                ? { 'Content-Type': 'multipart/form-data' }
                : { 'Content-Type': 'application/json' };

            // Usa PATCH per aggiornamenti parziali
            // Aggiunto prefisso /lezioni/
            const response = await apiClient.patch(`/lezioni/lessons/${lessonId}/contents/${contentId}/`, contentData, { headers });

            if (this.currentLesson?.id === lessonId && this.currentLesson.contents) {
                const index = this.currentLesson.contents.findIndex(c => c.id === contentId);
                if (index !== -1) {
                    this.currentLesson.contents[index] = { ...this.currentLesson.contents[index], ...response.data };
                    this.currentLesson.contents.sort((a, b) => a.order - b.order);
                }
            }
            return true;
        } catch (err: any) {
            console.error("Errore nell'aggiornamento del contenuto:", err);
            this.error = err.response?.data?.detail || JSON.stringify(err.response?.data) || err.message || 'Errore sconosciuto';
            return false;
        } finally {
            this.isLoadingContents = false;
        }
    },

    async deleteLessonContent(lessonId: number, contentId: number) {
        this.isLoadingContents = true;
        this.error = null;
        try {
            // Aggiunto prefisso /lezioni/
            await apiClient.delete(`/lezioni/lessons/${lessonId}/contents/${contentId}/`);
            if (this.currentLesson?.id === lessonId && this.currentLesson.contents) {
                this.currentLesson.contents = this.currentLesson.contents.filter(c => c.id !== contentId);
            }
            return true;
        } catch (err: any) {
            console.error("Errore nell'eliminazione del contenuto:", err);
            this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
            return false;
        } finally {
            this.isLoadingContents = false;
        }
    },

    // --- Azioni Assegnazioni ---
     // Aggiunta azione per caricare gli studenti del docente
     async fetchStudentsForTeacher(): Promise<Student[]> {
        // Assumiamo che l'endpoint /students/ restituisca gli studenti associati al docente autenticato
        // Questo potrebbe richiedere aggiustamenti lato backend o un endpoint dedicato
        this.isLoading = true; // Potremmo usare un loading specifico per studenti se necessario
        this.error = null;
        try {
            // Usiamo il path completo e sovrascriviamo temporaneamente il baseURL per accedere all'endpoint degli utenti
            // Rimosso calcolo rootApiBase e override baseURL.
            // Il percorso relativo corretto per l'istanza apiClient è /students/
            // perché /api/ è già nel baseURL e l'URL completo è /api/students/
            const response = await apiClient.get('/students/');
            return response.data as Student[];
        } catch (err: any) {
            console.error("Errore nel caricamento degli studenti:", err);
            this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
            return []; // Restituisce array vuoto in caso di errore
        } finally {
            this.isLoading = false;
        }
     },

      // Rinominata e modificata per gestire studenti E gruppi
      async assignLessonToTargets(lessonId: number, studentIds: number[], groupIds: number[]): Promise<AssignmentResult[]> {
        this.isLoadingAssignments = true;
        this.error = null;
        try {
          // Chiama la nuova funzione API unificata
          const response = await assignLesson(lessonId, studentIds, groupIds);
          console.log("Risposta assegnazione (studenti/gruppi):", response);

          // Gestione della risposta API (DA VERIFICARE E ADATTARE ALLA RISPOSTA REALE)
          // Assumiamo una struttura di risposta che separi i risultati per studenti e gruppi
          // NOTA: La struttura esatta della risposta da `assignLesson` deve essere confermata dal backend.
          // Questa è un'ipotesi basata sulla logica precedente e sulla necessità di distinguere.
          const createdStudentAssignments: { student: number }[] = response?.student_assignments?.created || [];
          const alreadyAssignedStudentIds: number[] = response?.student_assignments?.already_assigned || [];
          const failedStudentIds: number[] = response?.student_assignments?.failed || []; // Ipotetico

          const createdGroupAssignments: { group: number }[] = response?.group_assignments?.created || [];
          const alreadyAssignedGroupIds: number[] = response?.group_assignments?.already_assigned || [];
          const failedGroupIds: number[] = response?.group_assignments?.failed || []; // Ipotetico

          // Costruiamo i risultati per gli studenti
          const studentResults: AssignmentResult[] = studentIds.map(id => {
            if (createdStudentAssignments.some(a => a.student === id)) {
              return { targetId: id, targetType: 'student', success: true };
            } else if (alreadyAssignedStudentIds.includes(id)) {
              return { targetId: id, targetType: 'student', success: false, error: 'Studente già assegnato' };
            } else if (failedStudentIds.includes(id)) {
              return { targetId: id, targetType: 'student', success: false, error: 'Assegnazione studente fallita (specifico)' };
            } else {
                // Caso non coperto dalla risposta? Fallimento generico
               return { targetId: id, targetType: 'student', success: false, error: 'Assegnazione studente fallita (generico)' };
            }
          });

          // Costruiamo i risultati per i gruppi
          const groupResults: AssignmentResult[] = groupIds.map(id => {
            if (createdGroupAssignments.some(a => a.group === id)) {
              return { targetId: id, targetType: 'group', success: true };
            } else if (alreadyAssignedGroupIds.includes(id)) {
              return { targetId: id, targetType: 'group', success: false, error: 'Gruppo già assegnato' };
            } else if (failedGroupIds.includes(id)) {
              return { targetId: id, targetType: 'group', success: false, error: 'Assegnazione gruppo fallita (specifico)' };
            } else {
               return { targetId: id, targetType: 'group', success: false, error: 'Assegnazione gruppo fallita (generico)' };
            }
          });

          return [...studentResults, ...groupResults]; // Uniamo i risultati

        } catch (err: any) {
          console.error("Errore nell'assegnazione della lezione a studenti/gruppi:", err);
          const apiError = err.response?.data?.detail || JSON.stringify(err.response?.data) || err.message || 'Errore API';
          this.error = apiError;
          // Restituisce fallimento per tutti i target richiesti
          const studentErrors = studentIds.map(id => ({ targetId: id, targetType: 'student' as const, success: false, error: apiError }));
          const groupErrors = groupIds.map(id => ({ targetId: id, targetType: 'group' as const, success: false, error: apiError }));
          return [...studentErrors, ...groupErrors];
        } finally {
          this.isLoadingAssignments = false;
        }
      },

    async fetchAssignedLessons() { // Per lo studente loggato
        this.isLoadingAssignments = true;
        this.error = null;
        try {
            // Assumiamo un endpoint specifico o usiamo il ViewSet delle assegnazioni filtrato
            // Se usiamo LessonAssignmentViewSet, il backend filtra in base all'utente
            // Aggiunto prefisso /lezioni/
            const response = await apiClient.get(`/lezioni/assignments/`); // L'endpoint filtra per studente loggato
            this.assignedLessons = response.data;
        } catch (err: any) {
            console.error("Errore nel caricamento delle lezioni assegnate:", err);
            this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
            this.assignedLessons = [];
        } finally {
            this.isLoadingAssignments = false;
        }
    },

     async markAssignmentAsViewed(assignmentId: number) {
         // Non serve loading specifico qui, è un'azione rapida
         try {
             // Usa l'azione custom definita in LessonAssignmentViewSet
             // Aggiunto prefisso /lezioni/
             const response = await apiClient.post(`/lezioni/assignments/${assignmentId}/mark-viewed/`);
             // Aggiorna lo stato locale dell'assegnazione
             const index = this.assignedLessons.findIndex(a => a.id === assignmentId);
             if (index !== -1) {
                 this.assignedLessons[index].viewed_at = response.data.viewed_at;
             }
             // Aggiorna anche se la lezione è caricata in currentLesson? Meno probabile.
             return true;
         } catch (err: any) {
             console.error("Errore nel marcare l'assegnazione come vista:", err);
             // Non impostiamo l'errore globale per questa azione minore
             return false;
         }
     },

    // --- Azioni Gruppi ---
    async fetchGroupsAction() {
      this.isLoadingGroups = true;
      this.error = null;
      try {
        const fetchedGroups = await fetchGroups(); // Chiama la funzione API
        this.groups = fetchedGroups;
        console.log("[lessons.ts] Groups loaded:", this.groups);
      } catch (err: any) {
        console.error("Errore nel caricamento dei gruppi:", err);
        this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto durante caricamento gruppi';
        this.groups = [];
      } finally {
        this.isLoadingGroups = false;
      }
    },

  },
});