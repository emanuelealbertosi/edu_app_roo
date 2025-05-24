import { defineStore } from 'pinia';
import DashboardService, { type PreferredBadgeData } from '@/api/dashboard'; // Importato PreferredBadgeData
import RewardsService, { type EarnedBadge, type Badge } from '@/api/rewards'; // Importa RewardsService e tipi
// Importa la nuova interfaccia per i tentativi e rimuovi Quiz
import type { QuizAttemptDashboardItem, Pathway, WalletInfo } from '@/api/dashboard';

// Interfaccia BadgeInfo (se non importata da altrove)
// Badge (da @/api/rewards) ora include fileUrl, mediaType, thumbnailUrl, isEarned.
// Rimuoviamo animation_class se non più necessaria.
interface BadgeInfo extends Badge {
  // animation_class?: string | null; // Rimosso, non nel piano attuale
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
  preferredBadge: PreferredBadgeData | null; // Nuovo stato per il badge preferito
  loading: {
    quizzes: boolean;
    pathways: boolean;
    wallet: boolean;
    badges: boolean; // Aggiunto loading per badge
    preferredBadge: boolean; // Loading per il badge preferito
  };
  error: string | null;
}

export const useDashboardStore = defineStore('dashboard', {
  state: (): DashboardState => ({
    quizzes: [],
    pathways: [],
    wallet: null,
    earnedBadges: [], // Inizializza array vuoto
    preferredBadge: null, // Inizializza preferredBadge
    loading: {
      quizzes: false,
      pathways: false,
      wallet: false,
      badges: false, // Inizializza loading badge
      preferredBadge: false, // Inizializza loading preferredBadge
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
     // Prende il badge più recente
     const latest = sortedBadges[0].badge;
     // Assicura che isEarned sia true, dato che proviene dalla lista dei badge guadagnati.
     // Questo è più una misura di sicurezza; idealmente, latest.isEarned dovrebbe già essere true.
     return { ...latest, isEarned: true };
  },
  // Getter per il badge preferito
  getPreferredBadge(state): PreferredBadgeData | null {
    return state.preferredBadge;
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
        this.fetchEarnedBadges(), // Chiama la nuova action
        this.fetchPreferredBadge() // Chiama l'action per il badge preferito
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
        const rawEarnedBadgesData = await RewardsService.getEarnedBadges(); // Questo è Array<EarnedBadge> come da servizio
        
        // Eseguiamo la mappatura per assicurarci che le proprietà del badge annidato siano camelCase
        // e conformi a BadgeInfo/Badge.
        this.earnedBadges = rawEarnedBadgesData.map((rawEb: any) => { // rawEb è un singolo EarnedBadge, potenzialmente con badge annidato in snake_case
          const rawInnerBadge = rawEb.badge; // L'oggetto badge annidato
          
          // L'interfaccia Badge (e quindi BadgeInfo) si aspetta camelCase.
          // L'API potrebbe restituire snake_case per l'oggetto badge annidato.
          const mappedInnerBadge: BadgeInfo = {
            id: rawInnerBadge.id,
            name: rawInnerBadge.name,
            description: rawInnerBadge.description,
            fileUrl: rawInnerBadge.fileUrl || rawInnerBadge.file_url || null,
            mediaType: rawInnerBadge.mediaType || rawInnerBadge.media_type || 'IMAGE_STATIC', // Default a un tipo statico se non specificato
            thumbnailUrl: rawInnerBadge.thumbnailUrl || rawInnerBadge.thumbnail_url || null,
            trigger_type: rawInnerBadge.trigger_type,
            trigger_type_display: rawInnerBadge.trigger_type_display,
            trigger_condition: rawInnerBadge.trigger_condition,
            is_active: rawInnerBadge.is_active,
            // isEarned dovrebbe essere gestito dal contesto (es. se è in earnedBadges, è earned)
            // ma l'API per il badge annidato potrebbe avere un suo flag is_earned.
            isEarned: typeof rawInnerBadge.isEarned === 'boolean' ? rawInnerBadge.isEarned : (typeof rawInnerBadge.is_earned === 'boolean' ? rawInnerBadge.is_earned : true),
            created_at: rawInnerBadge.created_at,
            // animation_class: rawInnerBadge.animation_class // Se necessario e definito in BadgeInfo
          };

          return {
            id: rawEb.id,
            student: rawEb.student,
            earned_at: rawEb.earned_at,
            badge: mappedInnerBadge, // Usa l'oggetto badge mappato
          };
        }) as EarnedBadgeInfo[];

      } catch (error) {
        console.error('Error in fetchEarnedBadges:', error);
        // Non bloccare l'intera dashboard per errore badge, ma segnalalo
        // this.error = 'Errore nel caricamento dei badge guadagnati';
        console.warn('Errore nel caricamento dei badge guadagnati, la dashboard continuerà a caricarsi.');
      } finally {
        this.loading.badges = false;
      }
    },

    // Nuova action per recuperare il badge preferito
    async fetchPreferredBadge() {
      this.loading.preferredBadge = true;
      this.error = null; // Resetta l'errore specifico per questa operazione
      try {
        const badgeDataFromService = await DashboardService.getPreferredBadge();
        
        if (badgeDataFromService) {
          // Applica una mappatura robusta simile a quella in fetchEarnedBadges
          // per garantire che tutti i campi siano presenti e correttamente nominati (camelCase).
          // badgeDataFromService è l'equivalente di rawInnerBadge in fetchEarnedBadges.
          this.preferredBadge = {
            id: badgeDataFromService.id,
            name: badgeDataFromService.name,
            description: badgeDataFromService.description,
            fileUrl: (() => {
              let url = badgeDataFromService.fileUrl || (badgeDataFromService as any).file_url || null;
              if (url && !url.startsWith('http') && !url.startsWith('/')) {
                url = '/' + url;
              }
              return url;
            })(),
            mediaType: (() => {
              const rawType = badgeDataFromService.mediaType || (badgeDataFromService as any).media_type;
              if (typeof rawType === 'string') {
                const upperType = rawType.toUpperCase();
                if (upperType === 'VIDEO_MP4') return 'VIDEO_MP4';
                if (upperType === 'IMAGE_GIF') return 'IMAGE_GIF';
                if (upperType === 'IMAGE_STATIC') return 'IMAGE_STATIC';
                return rawType; // Restituisci il tipo originale se non è uno dei noti
              }
              return 'IMAGE_STATIC'; // Default fallback
            })(),
            thumbnailUrl: badgeDataFromService.thumbnailUrl || (badgeDataFromService as any).thumbnail_url || null,
            trigger_type: badgeDataFromService.trigger_type,
            trigger_type_display: badgeDataFromService.trigger_type_display,
            trigger_condition: badgeDataFromService.trigger_condition,
            is_active: badgeDataFromService.is_active,
            // Un badge preferito è per definizione guadagnato.
            // Il backend dovrebbe già fornire isEarned: true tramite BadgeSerializer.
            // Questa è una doppia sicurezza.
            isEarned: typeof badgeDataFromService.isEarned === 'boolean' ? badgeDataFromService.isEarned : true,
            created_at: badgeDataFromService.created_at,
          };
          
          console.log(
            '[DashboardStore] Preferred badge processed (with robust mapping):',
            'ID:', this.preferredBadge.id,
            'Name:', this.preferredBadge.name,
            'isEarned:', this.preferredBadge.isEarned,
            'fileUrl:', this.preferredBadge.fileUrl,
            'mediaType:', this.preferredBadge.mediaType,
            'thumbnailUrl:', this.preferredBadge.thumbnailUrl
          );
        } else {
          this.preferredBadge = null;
          console.log('[DashboardStore] No preferred badge fetched (null).');
        }

      } catch (error) {
        console.error('Error in fetchPreferredBadge:', error);
        // Potresti voler impostare un errore specifico per il badge preferito
        // this.error = 'Errore nel caricamento del badge preferito';
        // Per ora, logghiamo e non blocchiamo altre parti della dashboard
        console.warn('Errore nel caricamento del badge preferito.');
        this.preferredBadge = null; // Assicurati che sia null in caso di errore
      } finally {
        this.loading.preferredBadge = false;
      }
    },

    // Nuova action per impostare il badge preferito
    async setPreferredBadge(rewardId: number | null) {
      // Idealmente, qui si potrebbe impostare uno stato di loading specifico se l'operazione è lunga
      // this.loading.settingPreferredBadge = true;
      this.error = null;
      try {
        const badgeDataFromService = await DashboardService.setPreferredBadge(rewardId);
        
        if (badgeDataFromService) {
          // Applica la stessa mappatura robusta di fetchPreferredBadge
          this.preferredBadge = {
            id: badgeDataFromService.id,
            name: badgeDataFromService.name,
            description: badgeDataFromService.description,
            fileUrl: (() => {
              let url = badgeDataFromService.fileUrl || (badgeDataFromService as any).file_url || null;
              if (url && !url.startsWith('http') && !url.startsWith('/')) {
                url = '/' + url;
              }
              return url;
            })(),
            mediaType: (() => {
              const rawType = badgeDataFromService.mediaType || (badgeDataFromService as any).media_type;
              if (typeof rawType === 'string') {
                const upperType = rawType.toUpperCase();
                if (upperType === 'VIDEO_MP4') return 'VIDEO_MP4';
                if (upperType === 'IMAGE_GIF') return 'IMAGE_GIF';
                if (upperType === 'IMAGE_STATIC') return 'IMAGE_STATIC';
                return rawType; // Restituisci il tipo originale se non è uno dei noti
              }
              return 'IMAGE_STATIC'; // Default fallback
            })(),
            thumbnailUrl: badgeDataFromService.thumbnailUrl || (badgeDataFromService as any).thumbnail_url || null,
            trigger_type: badgeDataFromService.trigger_type,
            trigger_type_display: badgeDataFromService.trigger_type_display,
            trigger_condition: badgeDataFromService.trigger_condition,
            is_active: badgeDataFromService.is_active,
            isEarned: typeof badgeDataFromService.isEarned === 'boolean' ? badgeDataFromService.isEarned : true,
            created_at: badgeDataFromService.created_at,
          };
          // Log per debug
          console.log('[DashboardStore] Preferred badge set and updated in store (with mapping):', JSON.parse(JSON.stringify(this.preferredBadge)));
        } else {
          this.preferredBadge = null; // Se il servizio restituisce null
          console.log('[DashboardStore] setPreferredBadge returned null, preferredBadge set to null.');
        }

        // AGGIUNTA: Richiama fetchEarnedBadges per aggiornare la lista dei trofei
        await this.fetchEarnedBadges();
      } catch (error) {
        console.error('Error in setPreferredBadge:', error);
        this.error = 'Errore nell\'impostazione del badge preferito';
        // Non modifichiamo this.preferredBadge qui, così l'UI riflette ancora il vecchio stato
        // fino a un eventuale refresh o nuovo tentativo riuscito.
        throw error; // Rilancia l'errore per permettere al chiamante di gestirlo (es. UI)
      } finally {
        // this.loading.settingPreferredBadge = false;
      }
    }
  }
}); // Chiusura defineStore