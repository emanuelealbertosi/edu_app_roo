import { defineStore } from 'pinia';
import apiClient from '@/services/api'; // Assumiamo che apiClient sia configurato per le chiamate API
import type { Quiz } from '@/types/quiz'; // Importa il tipo Quiz
import type { QuizTemplate } from '@/types/quizTemplate'; // Importa il tipo QuizTemplate

// Interfaccia per i filtri opzionali della funzione fetchQuizzes e fetchQuizTemplates
interface FetchQuizItemsFilters {
  subjectId?: number;
  topicId?: number;
  // Altri filtri futuri potrebbero essere aggiunti qui (es. per titolo, stato, ecc.)
}

export const useQuizStore = defineStore('quiz', {
  state: () => ({
    quizzes: [] as Quiz[],
    currentQuiz: null as Quiz | null,
    quizTemplates: [] as QuizTemplate[],
    currentQuizTemplate: null as QuizTemplate | null,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchQuizzes(filters?: FetchQuizItemsFilters) {
      this.loading = true;
      this.error = null;
      try {
        // Costruisci i parametri della query in base ai filtri forniti
        const params = new URLSearchParams();
        if (filters?.subjectId) {
          params.append('subject_id', filters.subjectId.toString());
        }
        if (filters?.topicId) {
          params.append('topic_id', filters.topicId.toString());
        }
        
        // L'endpoint API per i quiz del docente.
        // Usiamo /api/quizzes/ come da design doc per le operazioni CRUD del docente
        const response = await apiClient.get(`/quizzes/${params.toString() ? '?' + params.toString() : ''}`);
        this.quizzes = response.data as Quiz[];
      } catch (err) {
        const error = err as any;
        this.error = error.response?.data?.detail || error.message || 'Failed to fetch quizzes';
        this.quizzes = [];
        console.error('Error fetching quizzes:', err);
      } finally {
        this.loading = false;
      }
    },

    async fetchQuizTemplates(filters?: FetchQuizItemsFilters) {
      this.loading = true;
      this.error = null;
      try {
        const params = new URLSearchParams();
        if (filters?.subjectId) {
          params.append('subject_id', filters.subjectId.toString());
        }
        if (filters?.topicId) {
          params.append('topic_id', filters.topicId.toString());
        }
        // Endpoint corretto per i docenti per recuperare i template quiz.
        const response = await apiClient.get(`/education/teacher/quiz-templates/${params.toString() ? '?' + params.toString() : ''}`);
        console.log('[quizStore] fetchQuizTemplates API response.data:', JSON.parse(JSON.stringify(response.data)));
        this.quizTemplates = response.data as QuizTemplate[];
      } catch (err) {
        const error = err as any;
        this.error = error.response?.data?.detail || error.message || 'Failed to fetch quiz templates';
        this.quizTemplates = [];
        console.error('Error fetching quiz templates:', err);
      } finally {
        this.loading = false;
      }
    },

    async fetchQuiz(quizId: number) {
      this.loading = true;
      this.error = null;
      try {
        const response = await apiClient.get(`/quizzes/${quizId}/`);
        this.currentQuiz = response.data as Quiz;
        // TODO: Potrebbe essere necessario caricare anche le domande del quiz qui,
        // se non sono incluse di default nella risposta e se servono.
        // Esempio: this.currentQuiz.questions = await this.fetchQuizQuestions(quizId);
      } catch (err) {
        const error = err as any;
        this.error = error.response?.data?.detail || error.message || `Failed to fetch quiz ${quizId}`;
        this.currentQuiz = null;
        console.error(`Error fetching quiz ${quizId}:`, err);
      } finally {
        this.loading = false;
      }
    },

    async fetchQuizTemplate(templateId: number) {
      this.loading = true;
      this.error = null;
      try {
        // Endpoint corretto per i docenti per recuperare un singolo template quiz.
        const response = await apiClient.get(`/education/teacher/quiz-templates/${templateId}/`);
        this.currentQuizTemplate = response.data as QuizTemplate;
      } catch (err) {
        const error = err as any;
        this.error = error.response?.data?.detail || error.message || `Failed to fetch quiz template ${templateId}`;
        this.currentQuizTemplate = null;
        console.error(`Error fetching quiz template ${templateId}:`, err);
      } finally {
        this.loading = false;
      }
    },

    // Placeholder per le azioni CRUD
    async createQuiz(quizData: Partial<Omit<Quiz, 'id' | 'teacher' | 'created_at' >>): Promise<Quiz | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const response = await apiClient.post('/quizzes/', quizData);
        const newQuiz = response.data as Quiz;
        this.quizzes.push(newQuiz);
        return newQuiz;
      } catch (err) {
        const error = err as any;
        this.error = error.response?.data?.detail || error.message || 'Failed to create quiz';
        console.error('Error creating quiz:', err);
        throw err; // Rilancia l'errore per gestirlo nel componente chiamante se necessario
      } finally {
        this.loading = false;
      }
    },

    async createQuizFromTemplate(
      templateId: number,
      quizOverrides: Partial<Omit<Quiz, 'id' | 'teacher' | 'created_at' | 'source_template_id'>>
    ): Promise<Quiz | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const payload = {
          template_id: templateId,
          ...quizOverrides,
        };
        const response = await apiClient.post('/education/quizzes/create-from-template/', payload);
        const newQuiz = response.data as Quiz;
        // Aggiungiamo il nuovo quiz alla lista dei quiz concreti, se necessario
        // this.quizzes.push(newQuiz); // Commentato perché potrebbe non essere desiderato aggiornare la lista qui
        return newQuiz;
      } catch (err) {
        const error = err as any;
        this.error = error.response?.data?.detail || error.message || 'Failed to create quiz from template';
        console.error('Error creating quiz from template:', err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async updateQuiz(quizId: number, quizData: Partial<Omit<Quiz, 'id' | 'teacher' | 'created_at'>>): Promise<Quiz | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const response = await apiClient.patch(`/quizzes/${quizId}/`, quizData);
        const updatedQuiz = response.data as Quiz;
        const index = this.quizzes.findIndex(q => q.id === quizId);
        if (index !== -1) {
          this.quizzes[index] = updatedQuiz;
        }
        if (this.currentQuiz?.id === quizId) {
          this.currentQuiz = updatedQuiz;
        }
        return updatedQuiz;
      } catch (err) {
        const error = err as any;
        this.error = error.response?.data?.detail || error.message || `Failed to update quiz ${quizId}`;
        console.error(`Error updating quiz ${quizId}:`, err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async deleteQuiz(quizId: number): Promise<boolean> {
      this.loading = true;
      this.error = null;
      try {
        await apiClient.delete(`/quizzes/${quizId}/`);
        this.quizzes = this.quizzes.filter(q => q.id !== quizId);
        if (this.currentQuiz?.id === quizId) {
          this.currentQuiz = null;
        }
        return true;
      } catch (err) {
        const error = err as any;
        this.error = error.response?.data?.detail || error.message || `Failed to delete quiz ${quizId}`;
        console.error(`Error deleting quiz ${quizId}:`, err);
        return false;
      } finally {
        this.loading = false;
      }
    },
  },
  getters: {
    getQuizById: (state) => (id: number): Quiz | undefined => {
      return state.quizzes.find(quiz => quiz.id === id);
    },
    getQuizTemplateById: (state) => (id: number): QuizTemplate | undefined => {
      return state.quizTemplates.find(template => template.id === id);
    },
    // Altri getters utili potrebbero essere aggiunti qui
  },
});