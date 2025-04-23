import { defineStore } from 'pinia';
import axios from 'axios';
import type { Lesson, LessonContent, LessonAssignment, Student, AssignmentResult } from '@/types/lezioni'; // Importa i tipi definiti

// Istanza Axios (idealmente condivisa)
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/lezioni',
  headers: {
    'Content-Type': 'application/json',
  }
});

// Interceptor per token (idealmente globale)
import { useAuthStore } from './auth';
apiClient.interceptors.request.use(config => {
  const authStore = useAuthStore();
  const token = authStore.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// Le interfacce locali sono state rimosse, usiamo quelle importate da @/types/lezioni.ts


export const useLessonStore = defineStore('lessons', {
  state: () => ({
    lessons: [] as Lesson[], // Lista lezioni (es. quelle create dal docente)
    assignedLessons: [] as LessonAssignment[], // Lezioni assegnate allo studente
    currentLesson: null as Lesson | null, // Lezione attualmente visualizzata/modificata
    isLoading: false,
    isLoadingContents: false, // Loading specifico per i contenuti
    isLoadingAssignments: false, // Loading specifico per le assegnazioni
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

     async assignLessonToStudents(lessonId: number, studentIds: number[]): Promise<AssignmentResult[]> {
        this.isLoadingAssignments = true;
        this.error = null;
        try {
            // Usa l'azione custom definita nel LessonViewSet
            // Aggiunto prefisso /lezioni/
            const response = await apiClient.post(`/lezioni/lessons/${lessonId}/assign/`, { student_ids: studentIds });
            console.log("Risposta assegnazione:", response.data);

            // Estrai i dati dalla risposta strutturata del backend
            const createdAssignments: { student: number }[] = response.data.assignments || []; // Array di oggetti assegnazione creati
            const alreadyAssignedIds: number[] = response.data.already_assigned || []; // Array di ID già assegnati

            // Costruisci l'array AssignmentResult[] che il componente si aspetta
            const results: AssignmentResult[] = studentIds.map(id => {
                const isCreated = createdAssignments.some(a => a.student === id); // Verifica se l'ID è tra quelli creati
                const isAlreadyAssigned = alreadyAssignedIds.includes(id);

                if (isCreated) {
                    return { studentId: id, success: true };
                } else if (isAlreadyAssigned) {
                    // Marcato come fallimento ma con messaggio specifico
                    return { studentId: id, success: false, error: 'Studente già assegnato' };
                } else {
                    // Se non è né creato né già assegnato, assumiamo un fallimento generico
                    // (potrebbe essere uno studente non trovato dal backend, ma la risposta non lo specifica qui)
                    return { studentId: id, success: false, error: 'Assegnazione fallita' };
                }
            });

            return results; // Restituisce l'array costruito
        } catch (err: any) {
            console.error("Errore nell'assegnazione della lezione:", err);
            this.error = err.response?.data?.detail || JSON.stringify(err.response?.data) || err.message || 'Errore sconosciuto';
            // In caso di errore generale della richiesta, restituiamo un array di fallimenti per tutti gli studenti
            return studentIds.map(id => ({ studentId: id, success: false, error: this.error || 'Errore API' }));
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

  },
});