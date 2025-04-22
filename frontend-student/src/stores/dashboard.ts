import { defineStore } from 'pinia';
import DashboardService from '@/api/dashboard';
import RewardsService, { type EarnedBadge, type Badge } from '@/api/rewards'; // Importa RewardsService e tipi
import type { Quiz, Pathway, WalletInfo } from '@/api/dashboard';

// Interfaccia BadgeInfo (se non importata da altrove)
interface BadgeInfo extends Badge { // Estende Badge per includere potenzialmente animation_class
  animation_class?: string | null;
}
// Interfaccia EarnedBadge (assicurati che abbia earned_at)
interface EarnedBadgeInfo extends EarnedBadge {
  badge: BadgeInfo; // Usa BadgeInfo estesa
  earned_at: string; // Assicurati che esista questo campo
}


interface DashboardState {
  quizzes: Quiz[];
  pathways: Pathway[];
  wallet: WalletInfo | null;
  earnedBadges: EarnedBadgeInfo[]; // Aggiunto stato per badge guadagnati
  loading: {
    quizzes: boolean;
    pathways: boolean;
    wallet: boolean;
    badges: boolean; // Aggiunto loading per badge
  };
  error: string | null;
}

export const useDashboardStore = defineStore('dashboard', {
  state: (): DashboardState => ({
    quizzes: [],
    pathways: [],
    wallet: null,
    earnedBadges: [], // Inizializza array vuoto
    loading: {
      quizzes: false,
      pathways: false,
      wallet: false,
      badges: false, // Inizializza loading badge
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
        pathway.latest_progress && 
        pathway.latest_progress.status === 'COMPLETED' // Usa lo stato corretto dal backend
      );
    },
    
    // Percorsi in corso O NON INIZIATI
    inProgressPathways(state): Pathway[] {
      return state.pathways.filter(pathway => 
        // Include percorsi senza progress (non iniziati) O quelli con stato IN_PROGRESS
        !pathway.latest_progress || pathway.latest_progress.status === 'IN_PROGRESS'
      );
   },

   // Nuovo getter per l'ultimo badge guadagnato
   latestEarnedBadge(state): BadgeInfo | null {
     if (!state.earnedBadges || state.earnedBadges.length === 0) {
       return null;
     }
     // Ordina i badge per data (dal più recente al meno recente)
     const sortedBadges = [...state.earnedBadges].sort((a, b) =>
       new Date(b.earned_at).getTime() - new Date(a.earned_at).getTime()
     );
     // Restituisce le info del badge più recente
     return sortedBadges[0].badge;
   }
 },

 actions: {
    /**
     * Carica i dati della dashboard
     */
    async loadDashboard() {
      this.error = null;
      // Aggiungi fetchEarnedBadges alle chiamate parallele
      await Promise.all([
        this.fetchQuizzes(),
        this.fetchPathways(),
        this.fetchWallet(),
        this.fetchEarnedBadges() // Chiama la nuova action
      ]);
    },

    // Definiamo qui le funzioni fetch esistenti
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
    async fetchPathways() {
      this.loading.pathways = true;
      try {
        const fetchedPathways = await DashboardService.getAssignedPathways();
        console.log('[DashboardStore] Fetched Pathways:', JSON.stringify(fetchedPathways)); // LOG Aggiunto
        this.pathways = fetchedPathways;
      } catch (error) {
        console.error('Error in fetchPathways:', error);
        this.error = 'Errore nel caricamento dei percorsi';
      } finally {
        this.loading.pathways = false;
      }
    },
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
    },

    // Nuova action per recuperare i badge guadagnati
    async fetchEarnedBadges() {
      this.loading.badges = true;
      try {
        // Assicurati che il servizio e il tipo restituito siano corretti
        this.earnedBadges = await RewardsService.getEarnedBadges() as EarnedBadgeInfo[];
      } catch (error) {
        console.error('Error in fetchEarnedBadges:', error);
        // Non bloccare l'intera dashboard per errore badge, ma segnalalo
        // this.error = 'Errore nel caricamento dei badge guadagnati';
        console.warn('Errore nel caricamento dei badge guadagnati, la dashboard continuerà a caricarsi.');
      } finally {
        this.loading.badges = false;
      }
    }
  }
}); // Chiusura defineStore