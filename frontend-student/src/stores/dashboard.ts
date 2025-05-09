import { defineStore } from 'pinia';
import DashboardService from '@/api/dashboard';
import RewardsService, { type EarnedBadge, type Badge } from '@/api/rewards'; // Importa RewardsService e tipi
// Importa la nuova interfaccia per i tentativi e rimuovi Quiz
import type { QuizAttemptDashboardItem, Pathway, WalletInfo } from '@/api/dashboard';

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
  quizzes: QuizAttemptDashboardItem[]; // Aggiornato tipo a array di tentativi
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
    // Quiz disponibili: tentativi non completati/in attesa e entro le date
    // Tentativi disponibili: stato non COMPLETED/PENDING e entro le date
    availableQuizzes(state): QuizAttemptDashboardItem[] {
      const now = new Date();
      // Filtra l'array di tentativi (state.quizzes) per trovare quelli "nuovi"
      console.log('[DashboardStore] Filtering availableQuizzes. Raw attempts in state:', JSON.parse(JSON.stringify(state.quizzes)));
      return state.quizzes.filter(attempt => {
        console.log(`[DashboardStore] Checking attempt for quiz_id: ${attempt.quiz_id}, attempt_id: ${attempt.attempt_id}, status: ${attempt.status}`);
        // 1. Filtra per stato: deve essere 'PENDING' (quiz assegnato ma non iniziato)
        // Un quiz è "disponibile" o "da iniziare" se il suo stato è 'PENDING'.
        // Tutti gli altri stati (IN_PROGRESS, PENDING_GRADING, COMPLETED, FAILED) lo rendono non "nuovo".
        const isPending = attempt.status === 'PENDING';
        if (!isPending) {
          console.log(`[DashboardStore] Excluding quiz_id: ${attempt.quiz_id} due to status: ${attempt.status}`);
          return false;
        }

        // 2. Filtra per date di disponibilità (invariato)
        const availableFrom = attempt.available_from ? new Date(attempt.available_from) : null;
        const availableUntil = attempt.available_until ? new Date(attempt.available_until) : null;

        // Se c'è una data di inizio ed è nel futuro, non è disponibile
        if (availableFrom && availableFrom > now) {
          return false;
        }

        // Se c'è una data di fine ed è passata, non è disponibile
        if (availableUntil && availableUntil < now) {
          return false;
        }

        // Se passa i controlli di stato e data, il tentativo è disponibile
        return true;
      });
    },

    // Tentativi completati: stato COMPLETED
    completedQuizzes(state): QuizAttemptDashboardItem[] {
      // Filtra i tentativi con stato COMPLETED
      return state.quizzes.filter(attempt => attempt.status === 'COMPLETED');
    },

    // Tentativi in corso, falliti o in attesa di correzione
    inProgressOrFailedQuizzes(state): QuizAttemptDashboardItem[] {
      // Filtra i tentativi con stato IN_PROGRESS, PENDING_GRADING o FAILED
      return state.quizzes.filter(attempt =>
        attempt.status && // Assicurati che lo stato esista
        ['IN_PROGRESS', 'PENDING_GRADING', 'FAILED'].includes(attempt.status)
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
        // La chiamata API ora restituisce QuizAttemptDashboardItem[]
        const fetchedAttempts = await DashboardService.getAssignedQuizzes();
        // Log per debug: vediamo cosa restituisce l'API
        console.log('[DashboardStore] Raw attempts received from API (fetchQuizzes):', JSON.parse(JSON.stringify(fetchedAttempts)));
        this.quizzes = fetchedAttempts;
      } catch (error) {
        console.error('Error in fetchQuizzes (attempts):', error); // Aggiornato log errore
        this.error = 'Errore nel caricamento dei tentativi quiz'; // Aggiornato messaggio errore
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