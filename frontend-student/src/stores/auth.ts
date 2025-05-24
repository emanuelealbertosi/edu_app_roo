import { defineStore } from 'pinia';
import { computed, ref } from 'vue'; // Aggiunto ref
// import { useRouter } from 'vue-router'; // Non serve più qui
import AuthService from '@/api/auth'; // Manteniamo per la chiamata API specifica
import DashboardService from '@/api/dashboard'; // Importa il servizio Dashboard
import type { NewContentCountsResponse } from '@/api/dashboard'; // Importa l'interfaccia per la risposta
// import routerInstance from '@/router'; // Non serve più qui
// Importa lo store condiviso - Assumendo che sia accessibile tramite un alias o percorso relativo
// Potrebbe essere necessario configurare un alias come '@shared/stores/sharedAuth' in tsconfig/vite config
// Per ora, usiamo un percorso relativo ipotetico. AGGIUSTARE SE NECESSARIO.
import { useSharedAuthStore, type SharedUser } from '@/stores/sharedAuth'; // <-- Usa percorso locale corretto

// Rimuovi interfaccia StudentData locale, useremo SharedUser
// interface StudentData { ... }


// Usa la sintassi setup store
export const useAuthStore = defineStore('authStudent', () => { // Cambiato nome store per evitare conflitti
  const sharedAuth = useSharedAuthStore(); // Usa lo store condiviso
  // const router = useRouter(); // Non serve più qui

  // Stato specifico per i conteggi
  const unreadQuizzesCount = ref(0);
  const unreadLessonsCount = ref(0);

  // Getters (come computed properties, delegati allo store condiviso)
  const userFullName = computed((): string => {
    const currentUser = sharedAuth.user;
    if (!currentUser) return '';
    // Assicurati che first_name e last_name esistano (potrebbero essere opzionali in SharedUser?)
    // Se abbiamo garantito che ci sono sempre per entrambi i tipi, ok.
    return `${currentUser.first_name || ''} ${currentUser.last_name || ''}`.trim();
  });

  const isUserAuthenticated = computed((): boolean => {
    return sharedAuth.isAuthenticated;
  });

  // Actions (come funzioni)

  // Nuova azione unificata per recuperare i conteggi
  async function fetchNewContentCounts(): Promise<void> {
    console.log('[AuthStudentStore] Fetching new content counts...');
    try {
      const response: NewContentCountsResponse = await DashboardService.getNewContentCounts();
      unreadQuizzesCount.value = response.new_quizzes_count;
      // new_lessons_count dal backend è un placeholder, quindi sarà 0 finché non implementato lì
      unreadLessonsCount.value = response.new_lessons_count;
      console.log('[AuthStudentStore] New content counts fetched:', { quizzes: unreadQuizzesCount.value, lessons: unreadLessonsCount.value });
    } catch (error) {
      console.error('[AuthStudentStore] Error fetching new content counts:', error);
      unreadQuizzesCount.value = 0; // Resetta in caso di errore
      unreadLessonsCount.value = 0; // Resetta in caso di errore
    }
  }

  async function login(studentCode: string, pin: string): Promise<void> {
    sharedAuth.setLoading(true);
    sharedAuth.setError(null);
    console.log('[AuthStudentStore login] Inizio azione login per studentCode:', studentCode);
    try {
      console.log('[AuthStudentStore login] Chiamata a AuthService.login...');
      // 1. Chiama l'API specifica per il login studente
      const response = await AuthService.login({ student_code: studentCode, pin: pin });
      console.log('[AuthStudentStore login] Risposta da AuthService.login:', JSON.parse(JSON.stringify(response || {})));

      if (!response || !response.student || !response.access) {
        console.error('[AuthStudentStore login] Risposta API non valida o mancante di dati essenziali.');
        throw new Error('Risposta API non valida per il login studente.');
      }

      // 2. Mappa i dati ricevuti (StudentData) a SharedUser
      const studentData = response.student;
      const sharedUserData: SharedUser = {
          id: studentData.id,
          student_code: studentData.student_code,
          first_name: studentData.first_name,
          last_name: studentData.last_name,
          role: 'STUDENT'
      };
      console.log('[AuthStudentStore login] Dati utente mappati per sharedAuth:', JSON.parse(JSON.stringify(sharedUserData)));

      // 3. Salva nello store condiviso
      console.log('[AuthStudentStore login] Chiamata a sharedAuth.setAuthData con accessToken:', response.access ? 'Presente' : 'Assente', 'refreshToken:', response.refresh ? 'Presente' : 'Assente');
      sharedAuth.setAuthData(response.access, response.refresh || null, sharedUserData);
      console.log('[AuthStudentStore login] sharedAuth.setAuthData completata. Stato sharedAuth.user (in Pinia):', JSON.parse(JSON.stringify(sharedAuth.user || null)));
      
      // DEBUG: Leggi direttamente da localStorage per verificare la scrittura
      try {
        const rawLocalStorage = localStorage.getItem('sharedAuth');
        console.log('[AuthStudentStore login] Contenuto RAW di localStorage per "sharedAuth" SUBITO DOPO setAuthData:', rawLocalStorage);
        if (rawLocalStorage) {
          console.log('[AuthStudentStore login] Contenuto PARSED di localStorage:', JSON.parse(rawLocalStorage));
        }
      } catch (e) {
        console.error('[AuthStudentStore login] Errore leggendo/parsando localStorage:', e);
      }

      // Dopo aver impostato i dati di autenticazione, recupera i conteggi
      await fetchNewContentCounts();

      // Redirect gestito dal componente UI

    } catch (err: any) {
      console.error('[AuthStudentStore login] Errore durante il login:', err);
      sharedAuth.setError(err.response?.data?.detail || err.message || 'Errore di autenticazione. Verifica le tue credenziali.');
      console.log('[AuthStudentStore login] Chiamata a sharedAuth.clearAuthData() a causa di errore.');
      sharedAuth.clearAuthData(); // Pulisci store condiviso
      throw err; // Rilancia per il componente UI
    } finally {
      sharedAuth.setLoading(false);
    }
  }

  // Logout action (delega allo store condiviso e gestisce redirect)
  async function logout(): Promise<void> {
    console.log("Logging out student...");
    sharedAuth.clearAuthData(); // Pulisci store condiviso
    unreadQuizzesCount.value = 0; // Resetta i conteggi al logout
    unreadLessonsCount.value = 0; // Resetta i conteggi al logout
    // Reindirizza alla root del dominio
    window.location.href = '/';
  }

  // Azione per inizializzare lo stato all'avvio dell'app
  async function initializeAuth(): Promise<void> {
    // Controlla se c'è un token nello store condiviso (letto da localStorage)
    if (sharedAuth.accessToken && !sharedAuth.user) {
      console.log('[AuthStudentStore] Token found, attempting to fetch current student...');
      sharedAuth.setLoading(true);
      try {
        // Chiama la nuova funzione API per ottenere i dati dello studente
        const studentData = await AuthService.fetchCurrentStudent();

        // Mappa i dati a SharedUser
        const sharedUserData: SharedUser = {
            id: studentData.id,
            student_code: studentData.student_code,
            first_name: studentData.first_name,
            last_name: studentData.last_name,
            role: 'STUDENT'
        };

        // Aggiorna lo store condiviso (solo utente, token già presente)
        // Potremmo creare un'azione 'setUser' in sharedAuth o riutilizzare setAuthData
        // Riutilizziamo setAuthData per semplicità, passando il token esistente
        sharedAuth.setAuthData(sharedAuth.accessToken, sharedAuth.refreshToken, sharedUserData);
        console.log('[AuthStudentStore] Student data fetched and store updated.');

        // Dopo aver inizializzato l'utente, recupera i conteggi
        await fetchNewContentCounts();

      } catch (error) {
        console.error('[AuthStudentStore] Failed to fetch student data during init:', error);
        // Se fallisce (es. token scaduto), pulisci lo store condiviso
        sharedAuth.clearAuthData();
        unreadQuizzesCount.value = 0; // Resetta i conteggi
        unreadLessonsCount.value = 0; // Resetta i conteggi
      } finally {
        sharedAuth.setLoading(false);
      }
    } else if (sharedAuth.isAuthenticated && sharedAuth.user) {
      // Utente già autenticato e caricato, ma potremmo voler aggiornare i conteggi
      console.log('[AuthStudentStore] User already authenticated, fetching counts...');
      await fetchNewContentCounts();
    }
    else {
       console.log('[AuthStudentStore] No token found or user not loaded, skipping init fetch and counts.');
    }
  }


  // Ritorna stato/getters condivisi e azioni specifiche studente
  return {
    // Stato/Getters condivisi (tramite computed)
    user: computed(() => sharedAuth.user),
    isAuthenticated: isUserAuthenticated, // Già computed
    loading: computed(() => sharedAuth.loading),
    error: computed(() => sharedAuth.error),
    userFullName, // Getter specifico basato su dati condivisi
    userRole: computed(() => sharedAuth.userRole),
    userId: computed(() => sharedAuth.userId),

    // Conteggi specifici studente
    unreadQuizzesCount: computed(() => unreadQuizzesCount.value),
    unreadLessonsCount: computed(() => unreadLessonsCount.value),

    // Azioni specifiche studente
    login,
    logout,
    // checkAuth rimosso
    initializeAuth, // Aggiunta nuova azione
    fetchNewContentCounts // Esponi la nuova azione unificata
  };
});