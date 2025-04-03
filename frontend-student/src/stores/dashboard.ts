import { defineStore } from 'pinia';
import DashboardService from '@/api/dashboard';
import type { Quiz, Pathway, WalletInfo } from '@/api/dashboard';

interface DashboardState {
  quizzes: Quiz[];
  pathways: Pathway[];
  wallet: WalletInfo | null;
  loading: {
    quizzes: boolean;
    pathways: boolean;
    wallet: boolean;
  };
  error: string | null;
}

export const useDashboardStore = defineStore('dashboard', {
  state: (): DashboardState => ({
    quizzes: [],
    pathways: [],
    wallet: null,
    loading: {
      quizzes: false,
      pathways: false,
      wallet: false
    },
    error: null
  }),
  
  getters: {
    // Quiz disponibili (non scaduti)
    availableQuizzes(state): Quiz[] {
      const now = new Date();
      return state.quizzes.filter(quiz => {
        // Escludi se l'ultimo tentativo è COMPLETED (superato) o PENDING_GRADING.
        // Se è FAILED o IN_PROGRESS (o non esiste tentativo), il quiz rimane disponibile (se le date lo permettono).
        const lastStatus = quiz.latest_attempt?.status;
        if (lastStatus === 'COMPLETED' || lastStatus === 'PENDING_GRADING') {
             return false;
        }
        // Se lo stato è 'FAILED' o 'IN_PROGRESS' o non c'è un tentativo, procedi con i controlli data.

        const availableFrom = quiz.available_from ? new Date(quiz.available_from) : null;
        const availableUntil = quiz.available_until ? new Date(quiz.available_until) : null;
        
        // Se non c'è una data di inizio, è disponibile
        if (!availableFrom) return true;
        
        // Se c'è una data di inizio ma è nel futuro, non è disponibile
        if (availableFrom > now) return false;
        
        // Se c'è una data di fine ed è passata, non è disponibile
        if (availableUntil && availableUntil < now) return false;
        
        return true;
      });
    },
    
    // Quiz completati (solo quelli superati)
    completedQuizzes(state): Quiz[] {
      return state.quizzes.filter(quiz =>
        quiz.latest_attempt?.status === 'COMPLETED' // Mostra solo quelli passati
      );
    },
    
    // Quiz in corso, falliti o in attesa di correzione
    inProgressOrFailedQuizzes(state): Quiz[] {
      return state.quizzes.filter(quiz =>
        quiz.latest_attempt &&
        ['IN_PROGRESS', 'PENDING_GRADING', 'FAILED'].includes(quiz.latest_attempt.status) // Includi FAILED qui
      );
    },
    
    // Percorsi completati
    completedPathways(state): Pathway[] {
      return state.pathways.filter(pathway => 
        pathway.progress && 
        pathway.progress.status === 'completed'
      );
    },
    
    // Percorsi in corso
    inProgressPathways(state): Pathway[] {
      return state.pathways.filter(pathway => 
        pathway.progress && 
        pathway.progress.status === 'in_progress'
      );
    }
  },
  
  actions: {
    /**
     * Carica i dati della dashboard
     */
    async loadDashboard() {
      this.error = null;
      await Promise.all([
        this.fetchQuizzes(),
        this.fetchPathways(),
        this.fetchWallet()
      ]);
    },
    
    /**
     * Recupera i quiz assegnati
     */
    async fetchQuizzes() {
      this.loading.quizzes = true;
      try {
        this.quizzes = await DashboardService.getAssignedQuizzes();
      } catch (error) {
        console.error('Error in fetchQuizzes:', error);
        this.error = 'Errore nel caricamento dei quiz';
      } finally {
        this.loading.quizzes = false;
      }
    },
    
    /**
     * Recupera i percorsi assegnati
     */
    async fetchPathways() {
      this.loading.pathways = true;
      try {
        this.pathways = await DashboardService.getAssignedPathways();
      } catch (error) {
        console.error('Error in fetchPathways:', error);
        this.error = 'Errore nel caricamento dei percorsi';
      } finally {
        this.loading.pathways = false;
      }
    },
    
    /**
     * Recupera le informazioni sul wallet
     */
    async fetchWallet() {
      this.loading.wallet = true;
      try {
        this.wallet = await DashboardService.getWalletInfo();
      } catch (error) {
        console.error('Error in fetchWallet:', error);
        this.error = 'Errore nel caricamento delle informazioni sul wallet';
      } finally {
        this.loading.wallet = false;
      }
    }
  }
});