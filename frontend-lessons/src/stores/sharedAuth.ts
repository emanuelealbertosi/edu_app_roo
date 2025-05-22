import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

// Interfaccia unificata per i dati utente essenziali
// Indipendentemente da Studente o Docente/Admin
export interface SharedUser { // Aggiunto export
  id: number; // ID utente (dal modello User o Student)
  username?: string; // Presente per Teacher/Admin
  student_code?: string; // Presente per Student
  first_name: string;
  last_name: string;
  email?: string; // Presente per Teacher/Admin
  role: 'STUDENT' | 'TEACHER' | 'ADMIN' | null; // Ruolo unificato
}

// Nome univoco per lo store condiviso
export const useSharedAuthStore = defineStore('sharedAuth', () => {
  // --- State ---
  const user = ref<SharedUser | null>(null)
  const accessToken = ref<string | null>(null) // Lascia che pinia-plugin-persistedstate gestisca l'inizializzazione
  const refreshToken = ref<string | null>(null) // Lascia che pinia-plugin-persistedstate gestisca l'inizializzazione
  const loading = ref(false) // Stato di caricamento generico
  const error = ref<string | null>(null) // Errore generico

  // --- Getters (Computed) ---
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const userRole = computed(() => user.value?.role || null)
  const userId = computed(() => user.value?.id || null)

  // --- Actions ---

  /**
   * Imposta i dati di autenticazione nello store e in localStorage.
   * @param access - Access Token JWT
   * @param refresh - Refresh Token JWT
   * @param userData - Dati utente conformi a SharedUser
   */
  function setAuthData(access: string, refresh: string | null, userData: SharedUser) {
    console.log('[SharedAuthStore] Setting auth data:', { access: '***', refresh: refresh ? '***' : null, user: userData });
    accessToken.value = access
    refreshToken.value = refresh
    user.value = userData

    // Rimosso accesso manuale a localStorage - gestito da pinia-plugin-persistedstate

    error.value = null // Resetta errori precedenti
  }

  /**
   * Pulisce i dati di autenticazione dallo store e da localStorage.
   */
  function clearAuthData() {
    console.log('[SharedAuthStore] Clearing auth data.');
    accessToken.value = null
    refreshToken.value = null
    user.value = null

    // Rimosso accesso manuale a localStorage - gestito da pinia-plugin-persistedstate
  }

  /**
   * Imposta lo stato di caricamento.
   * @param value - true se in caricamento, false altrimenti
   */
  function setLoading(value: boolean) {
    loading.value = value;
  }

   /**
   * Imposta un messaggio di errore.
   * @param message - Messaggio di errore
   */
  function setError(message: string | null) {
    error.value = message;
  }

  /**
   * Logica di inizializzazione (opzionale):
   * Potrebbe tentare di recuperare il ruolo o verificare il token all'avvio.
   * Per ora, lasciamo che gli store specifici gestiscano l'inizializzazione.
   */
  // function initialize() {
  //   if (accessToken.value) {
  //     // Potrebbe provare a decodificare il token per ottenere il ruolo
  //     // o chiamare un endpoint /me generico se esistesse.
  //   }
  // }
  // initialize();


  return {
    // State
    user,
    accessToken,
    refreshToken,
    loading,
    error,

    // Getters
    isAuthenticated,
    userRole,
    userId,

    // Actions
    setAuthData,
    clearAuthData,
    setLoading,
    setError,
    /**
     * Aggiorna lo stato dello store basandosi sui dati ricevuti da un evento 'storage'.
     * Questo è utile per la sincronizzazione cross-tab/iframe quando localStorage cambia.
     * @param persistedState - Lo stato deserializzato da event.newValue.
     */
    hydrateFromStorageEvent(persistedState: any) {
      console.log('[SharedAuthStore] Attempting to hydrate from storage event:', persistedState);

      const newAccessToken = persistedState.accessToken || null;
      const newRefreshToken = persistedState.refreshToken || null;
      const newUser = persistedState.user || null;

      let changed = false;
      if (accessToken.value !== newAccessToken) {
        accessToken.value = newAccessToken;
        console.log('[SharedAuthStore] Access token updated from storage event.');
        changed = true;
      }
      if (refreshToken.value !== newRefreshToken) {
        refreshToken.value = newRefreshToken;
        console.log('[SharedAuthStore] Refresh token updated from storage event.');
        changed = true;
      }
      // Confronto JSON per l'oggetto utente per semplicità,
      // potrebbe essere necessario un confronto più granulare se le prestazioni diventano un problema.
      if (JSON.stringify(user.value) !== JSON.stringify(newUser)) {
        user.value = newUser;
        console.log('[SharedAuthStore] User data updated from storage event.');
        changed = true;
      }

      if (changed) {
        console.log('[SharedAuthStore] State successfully updated based on storage event.');
      } else {
        console.log('[SharedAuthStore] No changes applied from storage event; state was already consistent.');
      }
    }
  }
}, { persist: true }) // Abilita la persistenza per questo store