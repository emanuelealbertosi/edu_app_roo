import { computed } from 'vue' // Rimosso ref non più necessario qui
import { defineStore } from 'pinia'
import { useRouter } from 'vue-router' // Importa useRouter
import * as authService from '@/api/auth' // Import auth service (including getTeacherProfile and refreshTokenTeacher)
import { useSharedAuthStore, type SharedUser } from './sharedAuth' // Importa lo store condiviso

// Rimuovi interfaccia TeacherUser locale, useremo SharedUser
// interface TeacherUser { ... }


export const useAuthStore = defineStore('authTeacher', () => { // Cambiato nome store per evitare conflitti ('auth' -> 'authTeacher')
  const router = useRouter(); // Ottieni l'istanza del router qui
  const sharedAuth = useSharedAuthStore(); // Usa lo store condiviso

  // Computed property per l'autenticazione (delegata)
  const isAuthenticated = computed(() => sharedAuth.isAuthenticated)

  // Rimosse funzioni setAuthData e clearAuthData locali


  // Login action
  async function login(usernameInput: string, passwordInput: string) {
    sharedAuth.setLoading(true);
    sharedAuth.setError(null);
    try {
      // 1. Ottieni i token
      const tokenResponse = await authService.loginTeacher({ username: usernameInput, password: passwordInput });

      // 2. Ottieni il profilo utente usando il nuovo access token
      try {
        // Passa entrambi i token a _fetchUserProfile per salvare nello store condiviso
        await _fetchUserProfile(tokenResponse.access, tokenResponse.refresh);
      } catch (fetchError) {
        console.error("Login succeeded but fetching profile failed:", fetchError);
        sharedAuth.clearAuthData(); // Pulisci lo store condiviso
        sharedAuth.setError('Login riuscito ma recupero profilo fallito.');
        // Rilancia l'errore per il componente UI
        throw new Error('Login riuscito ma recupero profilo fallito.');
      }

      // Redirect gestito dal componente UI dopo il successo

    } catch (err: any) {
      // Errore durante la chiamata loginTeacher o rilanciato da fetchUserProfile
      sharedAuth.clearAuthData(); // Assicura pulizia store condiviso
      sharedAuth.setError(err.response?.data?.detail || err.message || 'Login fallito'); // Messaggio più specifico se disponibile
      console.error("Login error:", err);
      throw err; // Rilancia per il componente UI
    } finally {
      sharedAuth.setLoading(false);
    }
  }

  // Logout action
  async function logout() {
    console.log("Logging out teacher...");
    // Potenziale chiamata backend per invalidare token (opzionale)
    // try { await authService.logoutTeacher(sharedAuth.refreshToken); } catch(e) {}
    sharedAuth.clearAuthData(); // Pulisci lo store condiviso
    console.log("Shared auth data cleared, redirecting to domain root...");
    // Reindirizza alla root del dominio
    window.location.href = '/';
  }

  // Action INTERNA to fetch user profile (ora usa e aggiorna lo store condiviso)
  // Non esportata direttamente, usata da login e checkAuthAndFetchProfile
  async function _fetchUserProfile(tokenToUse: string, existingRefreshToken: string | null) {
    sharedAuth.setLoading(true); // Usa setLoading dello store condiviso
    sharedAuth.setError(null);
    console.log("[fetchUserProfile Teacher] Attempting to fetch profile...");

    // Salva temporaneamente i token nello store condiviso per usarli nella chiamata API
    // L'interceptor userà il token passato o quello nello store.
    // Per sicurezza, impostiamo temporaneamente il token nello store condiviso
    // se stiamo usando un token specifico per questa chiamata.
    // NOTA: L'interceptor dovrebbe idealmente usare il token dallo store,
    // quindi assicuriamoci che sia impostato correttamente prima della chiamata.
    // Se tokenToUse è diverso da quello nello store, potrebbe essere un refresh.
    // Se è uguale, è una verifica/fetch iniziale.
    const originalAccessToken = sharedAuth.accessToken;
    if (tokenToUse !== originalAccessToken) {
        sharedAuth.accessToken = tokenToUse; // Imposta temporaneamente per la chiamata API
    }
    // Se non c'è un refresh token esistente, non possiamo aggiornarlo
    const currentRefreshToken = existingRefreshToken ?? sharedAuth.refreshToken;


    try {
      // La chiamata API userà il token impostato nello store (sharedAuth.accessToken)
      // grazie all'interceptor
      const fetchedUser = await authService.getTeacherProfile();
      console.log("[fetchUserProfile Teacher] Raw data received from API:", fetchedUser); // Log dei dati grezzi

      // Mappa i dati TeacherUser a SharedUser
      const sharedUserData: SharedUser = {
          id: fetchedUser.id,
          username: fetchedUser.username,
          email: fetchedUser.email,
          first_name: fetchedUser.first_name,
          last_name: fetchedUser.last_name,
          // Assicurati che il ruolo sia nel formato corretto per SharedUser
          role: fetchedUser.role === 'TEACHER' ? 'TEACHER' : fetchedUser.role === 'ADMIN' ? 'ADMIN' : null,
          // Aggiungi il campo can_create_public_groups (assumendo che l'API lo restituisca)
          can_create_public_groups: fetchedUser.can_create_public_groups ?? false,
      };

      // Salva tutto nello store condiviso usando il token usato per la chiamata
      // e il refresh token esistente (o quello appena ricevuto se fosse un login)
      sharedAuth.setAuthData(tokenToUse, currentRefreshToken, sharedUserData);
      console.log("[_fetchUserProfile Teacher] Profile fetched and shared auth data set:", sharedUserData);

    } catch (fetchError: any) {
      console.error("[_fetchUserProfile Teacher] Failed to fetch user profile:", fetchError);
      sharedAuth.setError(fetchError.message || 'Recupero profilo fallito');
      // Pulisci store condiviso SOLO se l'errore indica token invalido (es. 401)
      // Altri errori (es. rete) non dovrebbero causare logout immediato.
      // L'interceptor potrebbe già gestire il 401 tentando un refresh.
      // Se anche il refresh fallisce o non è possibile, l'interceptor o refreshTokenAction
      // chiameranno clearAuthData. Qui ci limitiamo a loggare e propagare l'errore.
      // sharedAuth.clearAuthData(); // Rimosso clearAuthData da qui
      throw fetchError; // Rilancia l'errore per chi ha chiamato
    } finally {
       // Ripristina il token originale se lo avevamo cambiato temporaneamente
       // e la chiamata non ha aggiornato lo store (cioè ha fallito)
       if (tokenToUse !== originalAccessToken && sharedAuth.accessToken !== tokenToUse) {
           sharedAuth.accessToken = originalAccessToken;
       }
      sharedAuth.setLoading(false); // Usa setLoading dello store condiviso
    }
  }


  // NUOVA AZIONE: Verifica token e recupera profilo se necessario
  async function checkAuthAndFetchProfile() {
    console.log("[checkAuthAndFetchProfile Teacher] Checking authentication status...");
    sharedAuth.setLoading(true); // Imposta loading a true all'inizio
    try {
      const currentAccessToken = sharedAuth.accessToken;
      const currentRefreshToken = sharedAuth.refreshToken; // Prendi anche il refresh token

      if (currentAccessToken) {
        console.log("[checkAuthAndFetchProfile Teacher] Access token found. Attempting to fetch profile...");
        // _fetchUserProfile gestisce il suo setLoading internamente, ma è bene averlo anche qui
        // per coprire il caso in cui _fetchUserProfile non venga chiamato o fallisca prima del suo finally.
        await _fetchUserProfile(currentAccessToken, currentRefreshToken);
        console.log("[checkAuthAndFetchProfile Teacher] Profile fetch successful or already up-to-date.");
      } else {
        console.log("[checkAuthAndFetchProfile Teacher] No access token found. User is not authenticated.");
        // Assicurati che lo store sia pulito se non c'è token
        if (sharedAuth.user || sharedAuth.refreshToken) {
            console.warn("[checkAuthAndFetchProfile Teacher] Inconsistency found: Access token missing but other auth data present. Clearing.");
            sharedAuth.clearAuthData();
        }
      }
    } catch (error: any) {
        // Anche se _fetchUserProfile gestisce i suoi errori, questo catch è per errori imprevisti
        // direttamente in checkAuthAndFetchProfile o se _fetchUserProfile rilancia un errore
        // che non è stato gestito internamente per quanto riguarda setLoading.
        console.error("[checkAuthAndFetchProfile Teacher] General error during auth check:", error);
        // Non pulire i dati qui a meno che non sia specificamente un errore di autenticazione
        // che richiede un logout. sharedAuth.setError potrebbe essere chiamato se necessario.
    } finally {
      sharedAuth.setLoading(false); // Assicura che loading sia false alla fine
    }
  }

  // Action for token refresh (ora usa e aggiorna lo store condiviso)
  async function refreshTokenAction() {
    const currentRefreshToken = sharedAuth.refreshToken;
    if (!currentRefreshToken) {
      console.error("Refresh Token Action: No refresh token available in shared store.");
      sharedAuth.clearAuthData();
      throw new Error("No refresh token available.");
    }

    sharedAuth.setLoading(true);
    sharedAuth.setError(null);

    try {
      console.log("Attempting token refresh (Teacher)...");
      const response = await authService.refreshTokenTeacher({ refresh: currentRefreshToken });

      // Aggiorna solo l'access token nello store condiviso, mantenendo user e refresh token
      if (sharedAuth.user) {
          sharedAuth.setAuthData(response.access, currentRefreshToken, sharedAuth.user);
          console.log("Token refreshed successfully via action (Teacher).");
      } else {
          console.error("Token refreshed, but no user data was present in shared store. Clearing auth.");
          sharedAuth.clearAuthData();
          throw new Error("User data missing after token refresh.");
      }
    } catch (refreshError: any) {
      console.error("Failed to refresh token via action (Teacher):", refreshError);
      sharedAuth.setError(refreshError.message || 'Failed to refresh token');
      sharedAuth.clearAuthData(); // Logout on refresh failure
      throw refreshError;
    } finally {
      sharedAuth.setLoading(false);
    }
  }

  // Rimuovi logica di inizializzazione da qui, verrà gestita centralmente o dall'app principale


  return {
    // Esponi lo stato/getters dallo store condiviso tramite computed per reattività
    user: computed(() => sharedAuth.user),
    accessToken: computed(() => sharedAuth.accessToken),
    // refreshToken non viene solitamente esposto direttamente
    error: computed(() => sharedAuth.error),
    loading: computed(() => sharedAuth.loading),
    isAuthenticated, // Già un computed che usa sharedAuth
    userRole: computed(() => sharedAuth.userRole),
    userId: computed(() => sharedAuth.userId),

    // Mantieni le azioni specifiche di questo store (login/logout/refresh specifici per teacher)
    login,
    logout,
    // fetchUserProfile non è esposto, è un helper interno
    refreshTokenAction,
    checkAuthAndFetchProfile // Esponi la nuova azione
  }
})