import { defineStore } from 'pinia'
// Rimosso import axios, useremo l'istanza centralizzata
import apiClient from '@/services/api'; // Importa l'istanza Axios centralizzata
// Definiremo un tipo per l'utente più avanti
// import type { User } from '@/types/user';
import router from '@/router'; // Importa l'istanza del router
import { useSharedAuthStore, type SharedUser } from './sharedAuth'; // Importa lo store condiviso e il tipo

// Rimosse definizione locale di apiClient e interceptor, ora sono in services/api.ts

// Definizione dello store di autenticazione
export const useAuthStore = defineStore('auth', {
  state: () => ({
    // Lo stato (accessToken, refreshToken, user) è ora gestito da sharedAuthStore
    // Manteniamo solo errori/loading specifici di questo store di azioni
    loginError: null as string | null,
    isLoading: false,
  }),

  getters: {
    // Delega i getter allo store condiviso
    isAuthenticated(): boolean {
      const sharedAuthStore = useSharedAuthStore();
      return sharedAuthStore.isAuthenticated;
    },
    userRole(): string | null {
      const sharedAuthStore = useSharedAuthStore();
      return sharedAuthStore.userRole;
    },
    // Getter per accedere direttamente allo stato condiviso se necessario
    sharedUser(): SharedUser | null {
        const sharedAuthStore = useSharedAuthStore();
        return sharedAuthStore.user;
    },
    sharedAccessToken(): string | null {
        const sharedAuthStore = useSharedAuthStore();
        return sharedAuthStore.accessToken;
    },
    sharedRefreshToken(): string | null {
        const sharedAuthStore = useSharedAuthStore();
        return sharedAuthStore.refreshToken;
    }
  },

  actions: {
    // Rimosse azioni setTokens, setUser, clearAuth - ora si usa sharedAuthStore.setAuthData/clearAuthData
    // Modifica la firma per accettare il tipo di login esplicitamente
    async login(credentials: { identifier: string; password?: string; pin?: string }, loginType: 'student' | 'teacher-admin') {
      this.isLoading = true;
      this.loginError = null;
      const sharedAuthStore = useSharedAuthStore();
      sharedAuthStore.clearAuthData(); // Pulisce lo stato condiviso

      console.log(`Attempting login. Type: ${loginType}, Identifier: ${credentials.identifier}`); // Debug

      try {
        let response;
        let userData: SharedUser | null = null;
        let access: string | null = null;
        let refresh: string | null = null;

        // Usa loginType invece di indovinare dal formato dell'identifier
        if (loginType === 'student') {
            // --- Login Studente ---
            if (!credentials.pin) throw new Error("PIN mancante per login studente.");
            console.log("Calling student login endpoint..."); // Debug
            // Usa l'istanza apiClient importata
            // Il percorso è relativo al baseURL definito in api.ts (/api)
            // L'URL completo corretto è /api/student/auth/student/login/
            response = await apiClient.post('/student/auth/student/login/', { // Corretto: aggiunto /student/
                student_code: credentials.identifier,
                pin: credentials.pin
            });
            console.log("Student login response:", response.data); // Debug
            // La risposta contiene già i token e i dati dello studente
            const studentData = response.data.student;
            access = response.data.access;
            refresh = response.data.refresh;

            if (!access || !refresh || !studentData) {
                 throw new Error("Risposta non valida dal server di login studente.");
            }
            // Mappa i dati dello studente all'interfaccia SharedUser
            userData = {
                id: studentData.id,
                student_code: studentData.student_code, // Usa student_code come identificativo
                first_name: studentData.first_name,
                last_name: studentData.last_name,
                role: 'STUDENT' // Ruolo standardizzato
            };

        } else if (loginType === 'teacher-admin') {
            // --- Login Docente/Admin ---
             if (!credentials.password) throw new Error("Password mancante per login docente/admin.");
             console.log("Calling standard token endpoint..."); // Debug
             // Usa l'istanza apiClient importata
             // Il percorso è relativo al baseURL definito in api.ts
             response = await apiClient.post('/auth/token/', {
                username: credentials.identifier,
                password: credentials.password
             });
             console.log("Standard login response:", response.data); // Debug
             access = response.data.access;
             refresh = response.data.refresh;
             if (!access || !refresh) {
                 throw new Error("Risposta non valida dal server token.");
             }

             // Dopo aver ottenuto il token, recupera le informazioni dell'utente (Admin/Docente)
             // Salva temporaneamente i token per permettere a fetchUser di funzionare
             sharedAuthStore.setAuthData(access, refresh, {} as SharedUser); // Dati utente temporanei
             userData = await this.fetchUser(); // fetchUser ora ritorna SharedUser o null
             if (!userData) {
                 // fetchUser ha fallito e ha già gestito il logout/clear
                 throw new Error("Impossibile recuperare i dati utente dopo il login.");
             }
        }

        // Se fetchUser fallisce per Admin/Docente, l'errore viene gestito lì e fa logout.
        // Se siamo qui, il login (e fetchUser se applicabile) è andato a buon fine.
        if (userData && access) { // Controlla se abbiamo dati utente e token
             // Salva i dati definitivi nello store condiviso
             sharedAuthStore.setAuthData(access, refresh, userData);
             console.log('Login successful, user data saved in shared store:', sharedAuthStore.user); // Debug
             // Reindirizza alla dashboard dopo login successo
             router.push({ name: 'dashboard' });
             return true; // Indica successo
        } else {
             // Questo non dovrebbe accadere se la logica sopra è corretta
             console.error("Login logic completed but user data or token is missing.");
             sharedAuthStore.clearAuthData(); // Pulisce per sicurezza
             throw new Error("Dati utente o token mancanti dopo il tentativo di login.");
        }

      } catch (error: any) {
        // Log più dettagliato dell'errore
        console.error("Login failed. Full error object:", error);
        if (error.response) {
          // Errore con risposta dal server (es. 4xx, 5xx)
          console.error("Login failed - Status:", error.response.status);
          console.error("Login failed - Data:", error.response.data);
          this.loginError = error.response.data.detail || `Errore server: ${error.response.status}`;
        } else if (error.request) {
          // Richiesta inviata ma nessuna risposta ricevuta (problema di rete/backend non raggiungibile)
          console.error("Login failed - No response received. Request details:", error.request);
          this.loginError = 'Nessuna risposta dal server. Verifica che il backend sia in esecuzione e raggiungibile.';
        } else {
          // Errore durante la configurazione della richiesta
          console.error("Login failed - Error setting up request:", error.message);
          this.loginError = `Errore nell'invio della richiesta: ${error.message}`;
        }

        sharedAuthStore.clearAuthData(); // Pulisce lo stato condiviso in caso di errore
        /* Rimosso blocco if precedente, ora gestito sopra
        if (error.response && error.response.data) {
          // Prova a estrarre un messaggio di errore specifico (già gestito sopra)
          // this.loginError = error.response.data.detail || 'Credenziali non valide o errore sconosciuto.';
        } else {
          // this.loginError = 'Errore di connessione o risposta non valida dal server.'; (già gestito sopra)
        }
        */
        return false; // Indica fallimento
      } finally {
        this.isLoading = false;
      }
    },

    // Modificato per ritornare SharedUser | null e usare sharedAuthStore
    async fetchUser(): Promise<SharedUser | null> { // Questa funzione ora è solo per Admin/Docenti
        const sharedAuthStore = useSharedAuthStore();
        if (!sharedAuthStore.accessToken) {
             console.warn("Fetch user skipped: no access token in shared store (Admin/Teacher)"); // Log aggiornato
             return null; // Non fare nulla se non c'è token
        }
        console.log("Fetching Admin/Teacher user data using shared token..."); // Log aggiornato
        this.isLoading = true; // Potrebbe essere utile indicare caricamento
        this.loginError = null; // Resetta errore precedente
       try {
         // L'endpoint corretto per ottenere i dati dell'utente Admin/Docente loggato è relativo al baseURL
         // Assumendo che il baseURL sia http://localhost:8000/api, il percorso relativo corretto è /admin/users/me/
         // Se il baseURL fosse solo http://localhost:8000, il percorso sarebbe /api/admin/users/me/
         // Dato che baseURL è /api, il percorso relativo è /admin/users/me/
         const response = await apiClient.get('/admin/users/me/'); // Usa apiClient importato
         const fetchedUserData = response.data;
         // Assicurati che la risposta contenga i dati attesi (incluso il ruolo)
         if (!fetchedUserData || !fetchedUserData.role) {
              throw new Error("Dati utente Admin/Docente incompleti ricevuti dal server.");
         }
         // Mappa i dati recuperati all'interfaccia SharedUser
         const userData: SharedUser = {
             id: fetchedUserData.id,
             username: fetchedUserData.username,
             first_name: fetchedUserData.first_name,
             last_name: fetchedUserData.last_name,
             email: fetchedUserData.email,
             // Assicurati che il ruolo backend corrisponda a 'TEACHER' o 'ADMIN'
             role: fetchedUserData.role.toUpperCase() as 'TEACHER' | 'ADMIN'
         };
         // Salva nello store condiviso (sovrascrive i dati temporanei se chiamato da login)
         sharedAuthStore.setAuthData(sharedAuthStore.accessToken!, sharedAuthStore.refreshToken, userData);
         console.log("Admin/Teacher user data fetched and saved in shared store:", userData); // Debug
         return userData; // Ritorna i dati utente recuperati
       } catch (error: any) { // Aggiunto tipo any per accedere a response
         console.error("Failed to fetch Admin/Teacher user data:", error);
         // Se riceviamo 401 qui, il token potrebbe essere scaduto o invalido
         if (error.response?.status === 401) {
              console.log("Token might be expired or invalid, attempting refresh...");
              const refreshed = await this.refreshTokenAction();
              if (refreshed) {
                  // Riprova fetchUser con il nuovo token
                  console.log("Retrying fetchUser after token refresh...");
                  return await this.fetchUser(); // Chiamata ricorsiva, ritorna il risultato
              }
         }
         // Se non è 401 o il refresh fallisce, fai logout
         this.logout(); // Logout chiama clearAuthData di sharedAuthStore
         return null; // Ritorna null in caso di fallimento
       }
         finally {
             this.isLoading = false;
         }
     },

     async refreshTokenAction() {
       const sharedAuthStore = useSharedAuthStore();
       if (!sharedAuthStore.refreshToken) {
         console.warn("Refresh token action skipped: no refresh token in shared store.");
         return false; // Non si può fare refresh senza refresh token
       }

       // Determina l'endpoint corretto in base al ruolo (se disponibile)
       // Se il ruolo non è noto, proviamo prima quello studente se il token contiene 'is_student'?
       // O assumiamo che se c'è un refresh token, l'utente DOVREBBE essere nello stato?
       // Approccio più sicuro: basarsi sul ruolo nello stato.
       const isStudent = sharedAuthStore.userRole === 'STUDENT'; // Usa ruolo standardizzato
       const refreshEndpoint = isStudent ? '/auth/student/token/refresh/' : '/auth/token/refresh/';
       console.log(`Attempting token refresh using endpoint: ${refreshEndpoint} for role: ${sharedAuthStore.userRole}`); // Debug

       try {
         // Usa apiClient importato
         const response = await apiClient.post(refreshEndpoint, {
           refresh: sharedAuthStore.refreshToken,
         });
         const { access } = response.data;
         // Il refresh token potrebbe essere ruotato, ma per ora assumiamo di no
         // Aggiorna solo l'access token nello store condiviso, mantenendo l'utente e il refresh token
         sharedAuthStore.setAuthData(access, sharedAuthStore.refreshToken, sharedAuthStore.user!);
         console.log("Token refreshed successfully.");
         return true;
       } catch (error) {
         console.error("Failed to refresh token:", error);
         this.logout(); // Logout se il refresh fallisce
         return false;
       }
     },

     logout() {
       console.log("Logging out..."); // Debug
       const sharedAuthStore = useSharedAuthStore();
       // Idealmente, dovremmo invalidare il token sul backend se usiamo blacklist
       // Ma con Simple JWT senza blacklist, basta rimuovere i token dal frontend
       sharedAuthStore.clearAuthData(); // Usa l'azione dello store condiviso
       // Reindirizza alla root del dominio, non alla root dell'app Vue
       window.location.href = '/';
     },

     // Azione per controllare lo stato iniziale (es. all'avvio dell'app)
     async checkInitialAuth() {
         const sharedAuthStore = useSharedAuthStore();
         console.log("Checking initial auth state..."); // Debug
         if (sharedAuthStore.accessToken && !sharedAuthStore.user) {
             // Se abbiamo un token ma non i dati utente, prova a recuperarli
             // Questo implica che l'utente è un Admin/Docente, altrimenti i dati studente
             // sarebbero stati salvati insieme al token durante il login studente.
             await this.fetchUser();
         } else if (sharedAuthStore.accessToken && sharedAuthStore.user) {
             console.log("User already loaded from shared store:", sharedAuthStore.user); // Debug
             // Potremmo voler verificare la validità del token qui con /api/auth/token/verify/
             // o semplicemente lasciare che le chiamate API falliscano e gestiscano il refresh/logout
         } else {
             console.log("No initial token found."); // Debug
         }
     }
   },
 }); // Rimosso { persist: true } - la persistenza è gestita da sharedAuthStore