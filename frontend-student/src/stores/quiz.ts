import { defineStore } from 'pinia';
import QuizService from '@/api/quiz';
import type { 
  QuizDetails, 
  QuizAttempt, 
  AttemptDetails, 
  Question,
  Answer
} from '@/api/quiz';

interface QuizState {
  currentQuiz: QuizDetails | null;
  currentAttempt: QuizAttempt | null;
  attemptDetails: AttemptDetails | null;
  currentQuestion: Question | null;
  loading: {
    quiz: boolean;
    attempt: boolean;
    question: boolean;
    answer: boolean;
  };
  error: string | null;
  lastAnswerResult: {
    is_correct: boolean | null;
    message?: string;
  } | null;
}

export const useQuizStore = defineStore('quiz', {
  state: (): QuizState => ({
    currentQuiz: null,
    currentAttempt: null,
    attemptDetails: null,
    currentQuestion: null,
    loading: {
      quiz: false,
      attempt: false,
      question: false,
      answer: false
    },
    error: null,
    lastAnswerResult: null
  }),
  
  getters: {
    // Stato del tentativo corrente
    attemptStatus(state): string | null {
      return state.currentAttempt?.status || null;
    },
    
    // Verifica se il tentativo è in corso
    isAttemptInProgress(state): boolean {
      return state.currentAttempt?.status === 'in_progress';
    },
    
    // Verifica se il tentativo è completato
    isAttemptCompleted(state): boolean {
      return state.currentAttempt?.status === 'completed';
    },
    
    // Verifica se il tentativo è in attesa di correzione manuale
    isAttemptPendingGrading(state): boolean {
      return state.currentAttempt?.status === 'pending_manual_grading';
    },
    
    // Calcola il punteggio corrente in percentuale
    currentScorePercentage(state): number | null {
      if (state.currentAttempt?.score === null) return null;
      return state.currentAttempt ? (state.currentAttempt.score || 0) * 100 : null;
    }
  },
  
  actions: {
    /**
     * Carica i dettagli di un quiz
     */
    async loadQuiz(quizId: number) {
      this.loading.quiz = true;
      this.error = null;
      
      try {
        this.currentQuiz = await QuizService.getQuizDetails(quizId);
      } catch (error) {
        console.error(`Error loading quiz ${quizId}:`, error);
        this.error = 'Errore nel caricamento del quiz';
      } finally {
        this.loading.quiz = false;
      }
    },
    
    /**
     * Inizia un nuovo tentativo del quiz
     */
    async startAttempt(quizId: number) {
      this.loading.attempt = true;
      this.error = null;
      
      try {
        this.currentAttempt = await QuizService.startAttempt(quizId);
        // Dopo aver iniziato il tentativo, carichiamo la prima domanda
        await this.loadCurrentQuestion();
      } catch (error) {
        console.error(`Error starting attempt for quiz ${quizId}:`, error);
        this.error = 'Errore nell\'iniziare il tentativo';
      } finally {
        this.loading.attempt = false;
      }
    },
    
    /**
     * Carica i dettagli completi del tentativo
     */
    async loadAttemptDetails() {
      if (!this.currentAttempt) {
        this.error = 'Nessun tentativo corrente';
        return;
      }
      
      this.loading.attempt = true;
      
      try {
        this.attemptDetails = await QuizService.getAttemptDetails(this.currentAttempt.id);
      } catch (error) {
        console.error(`Error loading attempt details for attempt ${this.currentAttempt.id}:`, error);
        this.error = 'Errore nel caricamento dei dettagli del tentativo';
      } finally {
        this.loading.attempt = false;
      }
    },
    
    /**
     * Carica la domanda corrente/successiva
     */
    async loadCurrentQuestion() {
      if (!this.currentAttempt) {
        this.error = 'Nessun tentativo corrente';
        return;
      }
      
      this.loading.question = true;
      
      try {
        this.currentQuestion = await QuizService.getCurrentQuestion(this.currentAttempt.id);
      } catch (error) {
        console.error(`Error loading current question for attempt ${this.currentAttempt.id}:`, error);
        this.error = 'Errore nel caricamento della domanda';
      } finally {
        this.loading.question = false;
      }
    },
    
    /**
     * Invia una risposta ad una domanda
     */
    async submitAnswer(questionId: number, answer: Answer) {
      if (!this.currentAttempt) {
        this.error = 'Nessun tentativo corrente';
        return;
      }
      
      this.loading.answer = true;
      this.lastAnswerResult = null;
      
      try {
        this.lastAnswerResult = await QuizService.submitAnswer(
          this.currentAttempt.id,
          questionId,
          answer
        );
        
        // Dopo aver inviato la risposta, carichiamo la prossima domanda
        await this.loadCurrentQuestion();
      } catch (error) {
        console.error(`Error submitting answer for question ${questionId}:`, error);
        this.error = 'Errore nell\'invio della risposta';
      } finally {
        this.loading.answer = false;
      }
    },
    
    /**
     * Completa il tentativo corrente
     */
    async completeAttempt() {
      if (!this.currentAttempt) {
        this.error = 'Nessun tentativo corrente';
        return;
      }
      
      this.loading.attempt = true;
      
      try {
        this.attemptDetails = await QuizService.completeAttempt(this.currentAttempt.id);
        this.currentAttempt = {
          ...this.currentAttempt,
          status: this.attemptDetails.status,
          score: this.attemptDetails.score,
          points_earned: this.attemptDetails.points_earned,
          completed_at: this.attemptDetails.completed_at
        };
      } catch (error) {
        console.error(`Error completing attempt ${this.currentAttempt.id}:`, error);
        this.error = 'Errore nel completamento del tentativo';
      } finally {
        this.loading.attempt = false;
      }
    },
    
    /**
     * Reset dello store
     */
    resetStore() {
      this.currentQuiz = null;
      this.currentAttempt = null;
      this.attemptDetails = null;
      this.currentQuestion = null;
      this.error = null;
      this.lastAnswerResult = null;
    }
  }
});