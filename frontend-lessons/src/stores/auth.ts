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
 
       // Attendere che sharedAuthStore sia idratato prima di leggere i suoi valori
       if (sharedAuthStore.$persistedState && typeof sharedAuthStore.$persistedState.isReady === 'function') {
           try {
               console.log('[AuthStore refreshTokenAction] Waiting for sharedAuthStore to be ready...');
               await sharedAuthStore.$persistedState.isReady();
               console.log('[AuthStore refreshTokenAction] sharedAuthStore is ready.');
           } catch (e) {
               console.error('[AuthStore refreshTokenAction] Error waiting for sharedAuthStore to be ready:', e);
               // Nonostante l'errore, proviamo a procedere, ma potrebbe usare dati obsoleti.
               // Considerare il logout qui se isReady() è cruciale e fallisce.
           }
       } else {
            if (import.meta.env.MODE !== 'production') {
                console.warn(
                  '[AuthStore refreshTokenAction] sharedAuthStore.$persistedState.isReady() non disponibile. ' +
                  'Procedendo senza attendere esplicitamente l\'idratazione.'
                );
            }
       }
 
       console.log('[AuthStore refreshTokenAction] Called. Current shared state (after potential ready wait):', {
           user: sharedAuthStore.user ? JSON.parse(JSON.stringify(sharedAuthStore.user)) : null, // Deep copy for logging
           role: sharedAuthStore.userRole,
           hasAccessToken: !!sharedAuthStore.accessToken,
           hasRefreshToken: !!sharedAuthStore.refreshToken,
       });
 
       if (!sharedAuthStore.refreshToken) {
         console.warn("[AuthStore refreshTokenAction] Refresh token action skipped: no refresh token in shared store (after ready wait). Logging out.");
         this.logout();
         return false;
       }
 
       const currentRole = sharedAuthStore.userRole;
       if (!currentRole) {
           console.error("[AuthStore refreshTokenAction] Cannot refresh token: user role is missing in sharedAuthStore (after ready wait). Logging out.");
           this.logout();
           return false;
       }
 
       const isStudent = currentRole === 'STUDENT';
       const refreshEndpoint = isStudent ? '/auth/student/token/refresh/' : '/auth/token/refresh/';
       
       console.log(`[AuthStore refreshTokenAction] Attempting token refresh. Endpoint: ${refreshEndpoint}, Role: ${currentRole}, RefreshToken Exists: ${!!sharedAuthStore.refreshToken}`);
 
       try {
         // apiClient è importato da '@/services/api' a livello di modulo
         const response = await apiClient.post(refreshEndpoint, {
           refresh: sharedAuthStore.refreshToken,
         });
         const { access, refresh: newRefreshToken } = response.data;
 
         // Aggiorna lo store condiviso con il nuovo access token e potenzialmente nuovo refresh token
         sharedAuthStore.setAuthData(access, newRefreshToken || sharedAuthStore.refreshToken!, sharedAuthStore.user!);
         console.log("[AuthStore refreshTokenAction] Token refreshed successfully. New access token set.");
         return true;
       } catch (error) {
         console.error(`[AuthStore refreshTokenAction] Failed to refresh token for role ${currentRole} using endpoint ${refreshEndpoint}:`, error);
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
         const sharedAuthStoreKey = 'sharedAuth'; // Chiave usata da pinia-plugin-persistedstate
 
         console.log('[AuthStore checkInitialAuth] Inizio checkInitialAuth.');
 
         // Tenta di attendere l'idratazione automatica
         if (sharedAuthStore.$persistedState && typeof sharedAuthStore.$persistedState.isReady === 'function') {
             try {
                 console.log('[AuthStore checkInitialAuth] Waiting for sharedAuthStore.$persistedState.isReady()...');
                 await sharedAuthStore.$persistedState.isReady();
                 console.log('[AuthStore checkInitialAuth] sharedAuthStore.$persistedState.isReady() completato.');
             } catch (e) {
                 console.error('[AuthStore checkInitialAuth] Errore durante sharedAuthStore.$persistedState.isReady():', e);
             }
         } else {
              if (import.meta.env.MODE !== 'production') {
                  console.warn('[AuthStore checkInitialAuth] sharedAuthStore.$persistedState.isReady() non disponibile.');
              }
         }
 
         console.log('[AuthStore checkInitialAuth] Stato sharedAuthStore DOPO isReady (o tentativo): AccessToken:', sharedAuthStore.accessToken ? 'Sì' : 'No', 'User:', sharedAuthStore.user ? 'Sì' : 'No');
 
         // Funzione helper per tentare l'idratazione
         const attemptManualHydration = (attemptNumber: number) => {
             console.log(`[AuthStore checkInitialAuth] Tentativo di idratazione manuale da localStorage (Tentativo #${attemptNumber}).`);
             try {
                 const persistedStateJSON = localStorage.getItem(sharedAuthStoreKey);
                 if (persistedStateJSON) {
                     console.log(`[AuthStore checkInitialAuth Attempt #${attemptNumber}] Trovato stato persistito in localStorage per la chiave`, sharedAuthStoreKey, ':', persistedStateJSON);
                     const persistedState = JSON.parse(persistedStateJSON);
                     if (persistedState && persistedState.accessToken && persistedState.user && persistedState.user.role) {
                         console.log(`[AuthStore checkInitialAuth Attempt #${attemptNumber}] Parsed persistedState:`, persistedState);
                         sharedAuthStore.setAuthData(persistedState.accessToken, persistedState.refreshToken, persistedState.user);
                         console.log(`[AuthStore checkInitialAuth Attempt #${attemptNumber}] Idratazione manuale COMPLETATA. Nuovo stato: AccessToken:`, sharedAuthStore.accessToken ? 'Sì' : 'No', 'User:', sharedAuthStore.user ? 'Sì' : 'No', 'Role:', sharedAuthStore.userRole);
                         return true; // Idratazione riuscita
                     } else {
                         console.log(`[AuthStore checkInitialAuth Attempt #${attemptNumber}] Stato persistito in localStorage invalido.`);
                         if(persistedState && persistedState.accessToken && persistedState.user && !persistedState.user.role){
                            console.warn(`[AuthStore checkInitialAuth Attempt #${attemptNumber}] User object from localStorage is missing "role".`);
                         }
                         sharedAuthStore.clearAuthData(); // Pulisci se i dati sono incompleti
                         return false; // Idratazione fallita
                     }
                 } else {
                     console.log(`[AuthStore checkInitialAuth Attempt #${attemptNumber}] Nessuno stato persistito trovato in localStorage per la chiave:`, sharedAuthStoreKey);
                     return false; // Idratazione fallita
                 }
             } catch (e) {
                 console.error(`[AuthStore checkInitialAuth Attempt #${attemptNumber}] Errore durante idratazione manuale:`, e);
                 sharedAuthStore.clearAuthData();
                 return false; // Idratazione fallita
             }
         };
 
         // Se lo store è ancora vuoto o incompleto, tenta un'idratazione manuale
         if (!sharedAuthStore.accessToken || !sharedAuthStore.user) {
             if (!attemptManualHydration(1)) {
                 // Se il primo tentativo fallisce, attendi un breve periodo e riprova
                 // Questo potrebbe dare a localStorage il tempo di sincronizzarsi se è un problema di timing.
                 console.log('[AuthStore checkInitialAuth] Primo tentativo di idratazione manuale fallito. Attendo 500ms per un secondo tentativo.');
                 await new Promise(resolve => setTimeout(resolve, 500)); // Attendi 500ms
                 attemptManualHydration(2);
             }
         }
 
         console.log("[AuthStore checkInitialAuth] Stato finale prima della logica di fetch/verifica. AccessToken:", sharedAuthStore.accessToken ? "Sì" : "No", "User:", sharedAuthStore.user ? "Sì" : "No", "Role:", sharedAuthStore.userRole);
 
         if (sharedAuthStore.accessToken && sharedAuthStore.user) {
             console.log("[AuthStore checkInitialAuth] Access token e user data presenti in sharedAuthStore:", JSON.parse(JSON.stringify(sharedAuthStore.user)));
             // Se l'utente è uno studente, i suoi dati dovrebbero essere completi.
             // Se è un admin/docente e manca l'email (o altri campi specifici), fetchUser potrebbe essere necessario.
             // Tuttavia, fetchUser è pensato per recuperare i dati DOPO un login token-based, non per idratare.
             // La logica qui assume che se user esiste, è sufficientemente idratato da localStorage.
             // Un controllo aggiuntivo sulla validità del token potrebbe essere fatto qui se necessario,
             // ma l'interceptor di risposta dovrebbe gestire i 401.
         } else if (sharedAuthStore.accessToken && !sharedAuthStore.user) {
             // Questo scenario (token presente ma utente assente) dopo il tentativo di idratazione manuale
             // è meno probabile se localStorage conteneva dati utente validi.
             // Potrebbe comunque verificarsi se localStorage aveva solo il token o dati utente corrotti.
             console.log("[AuthStore checkInitialAuth] Access token presente, ma no user data (o user data incompleto dopo idratazione). Tentativo fetchUser (principalmente per Admin/Teacher).");
             await this.fetchUser(); // fetchUser è specifico per Admin/Docente.
         } else {
             console.log("[AuthStore checkInitialAuth] Nessun access token o user data validi in sharedAuthStore dopo tutti i tentativi di idratazione. Utente considerato non autenticato.");
         }
         console.log('[AuthStore checkInitialAuth] Fine checkInitialAuth.');
     }
   },
 }); // Rimosso { persist: true } - la persistenza è gestita da sharedAuthStore