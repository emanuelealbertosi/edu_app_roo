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
        // Passa entrambi i token a fetchUserProfile per salvare nello store condiviso
        await fetchUserProfile(tokenResponse.access, tokenResponse.refresh);
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

  // Action to fetch user profile (ora usa e aggiorna lo store condiviso)
  async function fetchUserProfile(newAccessToken: string, newRefreshToken: string | null) {
    // Non serve più controllare il token qui, lo fa chi chiama (login o inizializzazione)
    sharedAuth.setLoading(true);
    sharedAuth.setError(null);
    console.log("[fetchUserProfile Teacher] Attempting to fetch profile...");

    // Salva temporaneamente i token nello store condiviso per usarli nella chiamata API
    // L'interceptor userà sharedAuth.accessToken
    const oldAccessToken = sharedAuth.accessToken;
    sharedAuth.accessToken = newAccessToken; // Imposta per la chiamata API

    try {
      const fetchedUser = await authService.getTeacherProfile(); // Chiamata API

      // Mappa i dati TeacherUser a SharedUser
      const sharedUserData: SharedUser = {
          id: fetchedUser.id,
          username: fetchedUser.username,
          email: fetchedUser.email,
          first_name: fetchedUser.first_name,
          last_name: fetchedUser.last_name,
          // Assicurati che il ruolo sia nel formato corretto per SharedUser
          role: fetchedUser.role === 'TEACHER' ? 'TEACHER' : fetchedUser.role === 'ADMIN' ? 'ADMIN' : null,
      };

      // Salva tutto nello store condiviso
      sharedAuth.setAuthData(newAccessToken, newRefreshToken, sharedUserData);
      console.log("[fetchUserProfile Teacher] Profile fetched and shared auth data set:", sharedUserData);

    } catch (fetchError: any) {
      console.error("[fetchUserProfile Teacher] Failed to fetch user profile:", fetchError);
      sharedAuth.setError(fetchError.message || 'Recupero profilo fallito');
      sharedAuth.clearAuthData(); // Pulisci store condiviso in caso di errore
      // Ripristina il token precedente se necessario? No, clearAuthData lo fa.
      // sharedAuth.accessToken = oldAccessToken;
      throw fetchError; // Rilancia l'errore per chi ha chiamato (es. login)
    } finally {
      // Ripristina il token precedente se la chiamata è fallita? No, clearAuthData lo fa.
      // if (sharedAuth.accessToken !== oldAccessToken) { // Se fallito, accessToken sarà null
      //    sharedAuth.accessToken = oldAccessToken;
      // }
      sharedAuth.setLoading(false);
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
    // fetchUserProfile non serve più esporlo, è un helper interno per login
    refreshTokenAction
  }
})