import { defineStore } from 'pinia';
import PathwayService from '@/api/pathway';
// Importa l'interfaccia corretta e quella per i quiz
import type { PathwayAttemptDetails, NextQuizInfo } from '@/api/pathway';

// Definisce un tipo per i dettagli del quiz come appaiono in PathwayAttemptDetails
type PathwayQuizDetail = PathwayAttemptDetails['quiz_details'][0] & { is_completed?: boolean; is_available?: boolean };

interface PathwayState {
  currentPathway: PathwayAttemptDetails | null; // Usa l'interfaccia corretta
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
      // Usa quiz_details
      if (!state.currentPathway || !state.currentPathway.quiz_details.length) return 0;
      
      if (this.isPathwayCompleted) return 100;
      
      // Usa quiz_details
      const completedQuizzes = state.currentPathway.quiz_details.filter((quiz: PathwayQuizDetail) => quiz.is_completed).length;
      // Usa quiz_details
      return Math.round((completedQuizzes / state.currentPathway.quiz_details.length) * 100);
    },
    
    // Recupera il prossimo quiz disponibile
    nextAvailableQuiz(state): NextQuizInfo | null { // Usa l'interfaccia importata
      if (!state.currentPathway) return null;
      
      // Usa quiz_details
      const nextQuiz = state.currentPathway.quiz_details.find((quiz: PathwayQuizDetail) =>
        quiz.is_available && !quiz.is_completed
      );
      
      if (!nextQuiz) return null;
      
      // Restituisce l'oggetto NextQuizInfo se trovato
      return nextQuiz ? { id: nextQuiz.quiz_id, title: nextQuiz.quiz_title, description: null } : null;
    },
    
    // Ottiene i quiz completati
    completedQuizzes(state): { id: number; quiz_id: number; title: string; order: number }[] { // Aggiornato tipo restituito
      if (!state.currentPathway) return [];
      
      // Usa quiz_details
      return state.currentPathway.quiz_details
        .filter((quiz: PathwayQuizDetail) => quiz.is_completed) // Aggiunto tipo
        .map((quiz: PathwayQuizDetail) => ({ // Aggiunto tipo
          id: quiz.id,
          quiz_id: quiz.quiz_id, // Aggiunto quiz_id
          title: quiz.quiz_title, // Usa quiz_title
          order: quiz.order
        }))
        // Aggiunti tipi per sort
        .sort((a: { order: number }, b: { order: number }) => a.order - b.order);
    },
    
    // Ottiene i quiz in attesa (disponibili ma non completati)
    pendingQuizzes(state): { id: number; quiz_id: number; title: string; order: number; is_available: boolean }[] { // Aggiornato tipo restituito
      if (!state.currentPathway) return [];
      
      // Usa quiz_details
      return state.currentPathway.quiz_details
        .filter((quiz: PathwayQuizDetail) => !quiz.is_completed) // Aggiunto tipo
        .map((quiz: PathwayQuizDetail) => ({ // Aggiunto tipo
          id: quiz.id,
          quiz_id: quiz.quiz_id, // Aggiunto quiz_id
          title: quiz.quiz_title, // Usa quiz_title
          order: quiz.order,
          is_available: quiz.is_available ?? false // Gestisce undefined
        }))
         // Aggiunti tipi per sort
        .sort((a: { order: number }, b: { order: number }) => a.order - b.order);
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
        // Usa la funzione API corretta
        this.currentPathway = await PathwayService.getPathwayAttemptDetails(pathwayId);
      } catch (error) {
        console.error(`Error loading pathway ${pathwayId}:`, error);
        this.error = 'Errore nel caricamento dei dettagli del percorso';
      } finally {
        this.loading = false;
      }
    },
    
    // /**
    //  * Avvia un quiz specifico all'interno del percorso
    //  * NOTA: Questa logica è probabilmente gestita altrove (es. store dei quiz/tentativi)
    //  */
    // async startQuiz(quizId: number) {
    //   if (!this.currentPathway) {
    //     throw new Error('Nessun percorso corrente');
    //   }
      
    //   this.loading = true;
      
    //   try {
    //     // La funzione API PathwayService.startQuizInPathway è commentata
    //     // const result = await PathwayService.startQuizInPathway(this.currentPathway.id, quizId);
    //     // return result.attempt_id;
    //     console.warn("startQuiz action in pathway store is deprecated.");
    //     return null; // O lancia un errore più specifico
    //   } catch (error) {
    //     console.error(`Error starting quiz ${quizId} in pathway ${this.currentPathway.id}:`, error);
    //     this.error = 'Errore nell\'avvio del quiz';
    //     throw error;
    //   } finally {
    //     this.loading = false;
    //   }
    // },
    
    /**
     * Resetta lo store
     */
    resetStore() {
      this.currentPathway = null;
      this.error = null;
    }
  }
});