import apiClient from './config';
import type { Badge } from './rewards'; // Importa il tipo Badge da rewards.ts

// Definisci l'interfaccia per la risposta dell'endpoint dei conteggi
export interface NewContentCountsResponse {
  new_quizzes_count: number;
  new_lessons_count: number;
}

// Interfacce per TypeScript
// NUOVA Interfaccia per i dati dei tentativi restituiti dalla dashboard API
export interface QuizAttemptDashboardItem {
  // Campi specifici del tentativo
  attempt_id: number; // ID del tentativo
  status: string; // Stato del tentativo (es. PENDING, IN_PROGRESS, COMPLETED, FAILED)
  score: number | null;
  started_at: string;
  completed_at: string | null;
  assignment_type: 'student' | 'group' | 'unknown' | null; // Tipo di assegnazione

  // Campi dal Quiz associato
  quiz_id: number;
  title: string;
  description: string;
  available_from: string | null;
  available_until: string | null;
  image_url?: string | null; // Aggiunto come da design doc
  subject_id?: number | null; // Aggiunto
  subject_name?: string | null; // Sostituisce metadata.subject
  subject_color_placeholder?: string | null; // Aggiunto
  topic_id?: number | null; // Aggiunto
  topic_name?: string | null; // Aggiunto
  metadata: { // Metadata ora non contiene più subject, ma può avere altro
    difficulty?: string;
    points_on_completion?: number;
    completion_threshold?: number;
    [key: string]: any;
  };
  teacher_username: string;
  teacher_first_name: string; // NUOVO
  teacher_last_name: string;  // NUOVO
  card_background_color?: string | null; // NUOVO: Colore sfondo card
}


// Interfaccia per i dettagli dei quiz all'interno di un percorso (invariata)
export interface PathwayQuizDetail {
    id: number;
    quiz_id: number;
    quiz_title: string;
    order: number;
}

// Interfaccia aggiornata per Pathway
export interface Pathway {
  id: number;
  title: string;
  description: string;
  metadata: {
    points_on_completion?: number;
    [key: string]: any;
  };
  teacher_username: string; // NUOVO: Aggiunto username del docente che ha assegnato
  quiz_details: PathwayQuizDetail[]; // Aggiunto: dettagli dei quiz nel percorso
  latest_progress?: {
    id: number; // Aggiunto ID del progresso
    status: string;
    last_completed_quiz_order: number | null;
    completed_orders: number[]; // Aggiunto: lista ordini completati
    started_at: string; // Aggiunto started_at
    completed_at: string | null;
    points_earned: number | null; // Mantenuto se presente in SimplePathwayProgressSerializer
  } | null;
}

export interface WalletInfo {
  current_points: number;
  total_earned_points?: number; // Aggiunto per i punti totali guadagnati
  recent_transactions: {
    id: number;
    points_change: number;
    reason: string;
    timestamp: string;
  }[];
}

// RIDEFINISCI PreferredBadgeData usando Badge
export type PreferredBadgeData = Badge; // PreferredBadgeData è ora un alias di Badge

/**
* Servizio per recuperare i dati della dashboard dello studente
 */
const DashboardService = {
  /**
   * Recupera tutti i quiz assegnati allo studente
   */
  async getAssignedQuizzes(): Promise<QuizAttemptDashboardItem[]> { // Aggiornato tipo restituito
    try {
      // L'endpoint API rimane lo stesso, ma ora restituisce tentativi
      const response = await apiClient.get('student/dashboard/quizzes/');
      // Assicurati che la risposta corrisponda alla nuova interfaccia
      return response.data as QuizAttemptDashboardItem[];
    } catch (error) {
      console.error('Error fetching assigned quiz attempts:', error); // Messaggio errore aggiornato
      throw error;
    }
  },

  /**
   * Recupera tutti i percorsi assegnati allo studente
   */
  async getAssignedPathways(): Promise<Pathway[]> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.get('student/dashboard/pathways/');
      return response.data;
    } catch (error) {
      console.error('Error fetching assigned pathways:', error);
      throw error;
    }
  },

  /**
   * Recupera le informazioni sul wallet dello studente
   */
  async getWalletInfo(): Promise<WalletInfo> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.get('student/dashboard/wallet/');
      return response.data;
    } catch (error) {
      console.error('Error fetching wallet info:', error);
      throw error;
    }
  },

  /**
   * Recupera il badge preferito dello studente
   */
  async getPreferredBadge(): Promise<PreferredBadgeData | null> {
    try {
      const response = await apiClient.get('student/profile/preferred-badge/');
      if (response.status === 204) {
        return null; // Nessun badge preferito o fallback
      }
      return response.data as PreferredBadgeData;
    } catch (error) {
      // Se l'API restituisce 404 o 204, potrebbe essere gestito come null
      // Qui gestiamo errori di rete o altri errori server
      console.error('Error fetching preferred badge:', error);
      // Non rilanciare l'errore per non bloccare il caricamento di altre parti della dashboard
      // Lo store gestirà il caso di dati nulli.
      return null;
    }
  },

  /**
   * Imposta il badge preferito per lo studente
   * @param badgeId - L'ID del badge da impostare come preferito, o null per deselezionare.
   */
  async setPreferredBadge(badgeId: number | null): Promise<PreferredBadgeData | null> { // La risposta potrebbe contenere il nuovo badge o i dati studente
    try {
      const response = await apiClient.patch('student/profile/set-preferred-badge/', { badge_id: badgeId }); // Modificato reward_id in badge_id
      // L'API PATCH /api/student/profile/set-preferred-badge/ dovrebbe restituire
      // i dati del badge aggiornato (PreferredBadgeData) o null se deselezionato.
      // Estraiamo il badge dalla risposta se presente, o potremmo dover chiamare getPreferredBadge di nuovo.
      // Per ora, assumiamo che la risposta del PATCH non sia direttamente il badge,
      // quindi lo store potrebbe dover ricaricare il badge o usare i dati studente.
      // Idealmente, il backend PATCH potrebbe restituire direttamente il nuovo PreferredBadgeData o null.
      // La view Django ora dovrebbe restituire direttamente l'oggetto Badge serializzato
      // (tramite StudentCurrentBadgeSerializer) o 200 OK con null/oggetto vuoto se deselezionato e fallback.
      if (response.status === 200) {
        if (response.data && response.data.id) { // Assumendo che il badge serializzato abbia un id
            return response.data as PreferredBadgeData;
        } else if (response.data && Object.keys(response.data).length === 0 && !badgeId) { // Oggetto vuoto per deselezione senza fallback esplicito
            return null;
        } else if (!response.data && !badgeId){ // Nessun dato e deselezione
             return null;
        } else if (response.data && !response.data.id && !badgeId) { // Dati vuoti e deselezione
            return null;
        }
        // Se badgeId era fornito ma response.data non è un badge valido, potrebbe essere un problema.
        // Tuttavia, lo store Pinia ricaricherà lo stato da GET /preferred-badge/ se necessario.
        // Per ora, se la risposta non è chiaramente un badge, restituiamo null per forzare il re-fetch
        // o affidarci all'aggiornamento dello store basato sulla GET.
        console.warn('setPreferredBadge: La risposta non era un oggetto badge atteso, si affida al re-fetch o allo stato esistente.');
        return null; // O la view PATCH dovrebbe garantire una risposta PreferredBadgeData
      }
      // Se lo status non è 200, l'errore sarà gestito dal blocco catch.
      // Questo return non dovrebbe essere raggiunto se c'è un errore HTTP.
      return null;
    } catch (error) {
      console.error('Error setting preferred badge:', error);
      throw error; // Rilancia l'errore per gestirlo nel componente/store chiamante
    }
  },

  /**
   * Recupera i conteggi dei nuovi quiz e delle nuove lezioni per lo studente autenticato.
   */
  async getNewContentCounts(): Promise<NewContentCountsResponse> {
    try {
      // L'URL completo sarà gestito da baseURL di apiClient e dal path specificato qui.
      // Il path corrisponde a quello definito in apps/education/urls.py
      const response = await apiClient.get<NewContentCountsResponse>('student/new-content-counts/');
      return response.data;
    } catch (error) {
      console.error('Errore durante il recupero dei conteggi dei nuovi contenuti:', error);
      // Restituisci valori di default o gestisci l'errore come preferisci
      // In questo caso, rilanciamo l'errore per farlo gestire dallo store chiamante
      throw error;
    }
  }
};
 
export default DashboardService;
