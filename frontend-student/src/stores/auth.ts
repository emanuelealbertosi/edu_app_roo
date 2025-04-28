import { defineStore } from 'pinia';
import { computed } from 'vue'; // Rimosso ref e useRouter non più necessari qui
// import { useRouter } from 'vue-router'; // Non serve più qui
import AuthService from '@/api/auth'; // Manteniamo per la chiamata API specifica
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
  async function login(studentCode: string, pin: string): Promise<void> {
    sharedAuth.setLoading(true);
    sharedAuth.setError(null);
    try {
      // 1. Chiama l'API specifica per il login studente
      const response = await AuthService.login({ student_code: studentCode, pin: pin });

      // 2. Mappa i dati ricevuti (StudentData) a SharedUser
      const studentData = response.student; // Assumendo che la risposta abbia la chiave 'student'
      const sharedUserData: SharedUser = {
          id: studentData.id,
          student_code: studentData.student_code, // Campo specifico studente
          first_name: studentData.first_name,
          last_name: studentData.last_name,
          role: 'STUDENT' // Imposta ruolo esplicitamente
          // username e email saranno undefined
      };

      // 3. Salva nello store condiviso
      // Passa null per refresh token se non è restituito dall'API studente
      sharedAuth.setAuthData(response.access, response.refresh || null, sharedUserData);

      // Redirect gestito dal componente UI

    } catch (err: any) {
      sharedAuth.setError(err.response?.data?.detail || 'Errore di autenticazione. Verifica le tue credenziali.');
      console.error('Authentication error (Student):', err);
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

      } catch (error) {
        console.error('[AuthStudentStore] Failed to fetch student data during init:', error);
        // Se fallisce (es. token scaduto), pulisci lo store condiviso
        sharedAuth.clearAuthData();
      } finally {
        sharedAuth.setLoading(false);
      }
    } else {
       console.log('[AuthStudentStore] No token found or user already loaded, skipping init fetch.');
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

    // Azioni specifiche studente
    login,
    logout,
    // checkAuth rimosso
    initializeAuth // Aggiunta nuova azione
  };
});