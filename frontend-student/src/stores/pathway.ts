import { defineStore } from 'pinia';
import PathwayService from '@/api/pathway';
import type { PathwayDetails } from '@/api/pathway';

interface PathwayState {
  currentPathway: PathwayDetails | null;
  loading: boolean;
  error: string | null;
}

export const usePathwayStore = defineStore('pathway', {
  state: (): PathwayState => ({
    currentPathway: null,
    loading: false,
    error: null
  }),
  
  getters: {
    // Verifica se il percorso è stato completato
    isPathwayCompleted(state): boolean {
      return !!state.currentPathway?.progress?.status 
        && state.currentPathway.progress.status === 'completed';
    },
    
    // Calcola la percentuale di completamento
    completionPercentage(state): number {
      if (!state.currentPathway || !state.currentPathway.quizzes.length) return 0;
      
      if (this.isPathwayCompleted) return 100;
      
      const completedQuizzes = state.currentPathway.quizzes.filter(quiz => quiz.is_completed).length;
      return Math.round((completedQuizzes / state.currentPathway.quizzes.length) * 100);
    },
    
    // Recupera il prossimo quiz disponibile
    nextAvailableQuiz(state): { id: number, title: string } | null {
      if (!state.currentPathway) return null;
      
      const nextQuiz = state.currentPathway.quizzes.find(quiz => 
        quiz.is_available && !quiz.is_completed
      );
      
      if (!nextQuiz) return null;
      
      return {
        id: nextQuiz.id,
        title: nextQuiz.title
      };
    },
    
    // Ottiene i quiz completati
    completedQuizzes(state): { id: number, title: string, order: number }[] {
      if (!state.currentPathway) return [];
      
      return state.currentPathway.quizzes
        .filter(quiz => quiz.is_completed)
        .map(quiz => ({
          id: quiz.id,
          title: quiz.title,
          order: quiz.order
        }))
        .sort((a, b) => a.order - b.order);
    },
    
    // Ottiene i quiz in attesa (disponibili ma non completati)
    pendingQuizzes(state): { id: number, title: string, order: number, is_available: boolean }[] {
      if (!state.currentPathway) return [];
      
      return state.currentPathway.quizzes
        .filter(quiz => !quiz.is_completed)
        .map(quiz => ({
          id: quiz.id,
          title: quiz.title,
          order: quiz.order,
          is_available: quiz.is_available
        }))
        .sort((a, b) => a.order - b.order);
    }
  },
  
  actions: {
    /**
     * Carica i dettagli di un percorso formativo
     */
    async loadPathwayDetails(pathwayId: number) {
      this.loading = true;
      this.error = null;
      
      try {
        this.currentPathway = await PathwayService.getPathwayDetails(pathwayId);
      } catch (error) {
        console.error(`Error loading pathway ${pathwayId}:`, error);
        this.error = 'Errore nel caricamento dei dettagli del percorso';
      } finally {
        this.loading = false;
      }
    },
    
    /**
     * Avvia un quiz specifico all'interno del percorso
     */
    async startQuiz(quizId: number) {
      if (!this.currentPathway) {
        throw new Error('Nessun percorso corrente');
      }
      
      this.loading = true;
      
      try {
        const result = await PathwayService.startQuizInPathway(this.currentPathway.id, quizId);
        return result.attempt_id;
      } catch (error) {
        console.error(`Error starting quiz ${quizId} in pathway ${this.currentPathway.id}:`, error);
        this.error = 'Errore nell\'avvio del quiz';
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    /**
     * Resetta lo store
     */
    resetStore() {
      this.currentPathway = null;
      this.error = null;
    }
  }
});