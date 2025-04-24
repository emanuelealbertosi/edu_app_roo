import { defineStore } from 'pinia'
// Rimosso import axios, useremo l'istanza centralizzata
import apiClient from '@/services/api'; // Importa l'istanza Axios centralizzata
// Definiremo un tipo per l'utente più avanti
// import type { User } from '@/types/user';
import router from '@/router'; // Importa l'istanza del router

// Rimosse definizione locale di apiClient e interceptor, ora sono in services/api.ts

// Definizione dello store di autenticazione
export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem('accessToken') || null as string | null,
    refreshToken: localStorage.getItem('refreshToken') || null as string | null,
    // Definire un tipo User appropriato (es. { id: number, username: string, role: string })
    user: JSON.parse(localStorage.getItem('user') || 'null') as any | null,
    loginError: null as string | null,
    isLoading: false,
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.accessToken && !!state.user,
    // Aggiungere altri getters se necessario (es. isAdmin, isTeacher, isStudent)
    userRole: (state): string | null => state.user?.role || null,
  },

  actions: {
    setTokens(access: string, refresh: string) {
      this.accessToken = access;
      this.refreshToken = refresh;
      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);
      // Aggiorna l'header di default per le chiamate future con questo apiClient
      // apiClient.defaults.headers.common['Authorization'] = `Bearer ${access}`;
    },

    setUser(userData: any) {
      this.user = userData;
      localStorage.setItem('user', JSON.stringify(userData));
    },

    clearAuth() {
      this.accessToken = null;
      this.refreshToken = null;
      this.user = null;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      // Rimuovi l'header di default
      // delete apiClient.defaults.headers.common['Authorization'];
    },

    // Modifica la firma per accettare il tipo di login esplicitamente
    async login(credentials: { identifier: string; password?: string; pin?: string }, loginType: 'student' | 'teacher-admin') {
      this.isLoading = true;
      this.loginError = null;
      this.clearAuth(); // Pulisce stato precedente prima del tentativo

      console.log(`Attempting login. Type: ${loginType}, Identifier: ${credentials.identifier}`); // Debug

      try {
        let response;
        // Usa loginType invece di indovinare dal formato dell'identifier
        if (loginType === 'student') {
            // --- Login Studente ---
            if (!credentials.pin) throw new Error("PIN mancante per login studente.");
            console.log("Calling student login endpoint..."); // Debug
            // Usa l'istanza apiClient importata
            // Il percorso è relativo al baseURL definito in api.ts
            response = await apiClient.post('/auth/student/login/', {
                student_code: credentials.identifier,
                pin: credentials.pin
            });
            console.log("Student login response:", response.data); // Debug
            // La risposta contiene già i token e i dati dello studente
            const { access, refresh, student } = response.data;
            if (!access || !refresh || !student) {
                 throw new Error("Risposta non valida dal server di login studente.");
            }
            this.setTokens(access, refresh);
            // Imposta l'utente con i dati dello studente e aggiungi il ruolo manualmente
            this.setUser({ ...student, role: 'Studente' }); // Assumiamo che 'Studente' sia il ruolo corretto

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
             const { access, refresh } = response.data;
             if (!access || !refresh) {
                 throw new Error("Risposta non valida dal server token.");
            }
             this.setTokens(access, refresh);

             // Dopo aver ottenuto il token, recupera le informazioni dell'utente (Admin/Docente)
             await this.fetchUser(); // fetchUser ora è solo per Admin/Docenti
        }

        // Se fetchUser fallisce per Admin/Docente, l'errore viene gestito lì e fa logout.
        // Se siamo qui, il login (e fetchUser se applicabile) è andato a buon fine.
        if (this.user) { // Controlla se l'utente è stato impostato correttamente
             console.log('Login successful, user:', this.user); // Debug
             return true; // Indica successo
        } else {
             // Questo non dovrebbe accadere se fetchUser non fallisce, ma per sicurezza
             throw new Error("Dati utente non caricati dopo il login.");
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

        this.clearAuth(); // Pulisce lo stato in caso di errore
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

    async fetchUser() { // Questa funzione ora è solo per Admin/Docenti
       if (!this.accessToken) {
            console.warn("Fetch user skipped: no access token (Admin/Teacher)"); // Log aggiornato
            return; // Non fare nulla se non c'è token
       }
       console.log("Fetching Admin/Teacher user data..."); // Log aggiornato
      try {
        // L'endpoint corretto per ottenere i dati dell'utente Admin/Docente loggato è relativo al baseURL
        // Assumendo che il baseURL sia http://localhost:8000/api, il percorso relativo corretto è /admin/users/me/
        // Se il baseURL fosse solo http://localhost:8000, il percorso sarebbe /api/admin/users/me/
        // Dato che baseURL è /api, il percorso relativo è /admin/users/me/
        const response = await apiClient.get('/admin/users/me/'); // Usa apiClient importato
        // Assicurati che la risposta contenga i dati attesi (incluso il ruolo)
        if (!response.data || !response.data.role) {
             throw new Error("Dati utente Admin/Docente incompleti ricevuti dal server.");
        }
        this.setUser(response.data);
        console.log("Admin/Teacher user data fetched:", response.data); // Debug
      } catch (error: any) { // Aggiunto tipo any per accedere a response
        console.error("Failed to fetch Admin/Teacher user data:", error);
        // Se riceviamo 401 qui, il token potrebbe essere scaduto o invalido
        if (error.response?.status === 401) {
             console.log("Token might be expired or invalid, attempting refresh...");
             const refreshed = await this.refreshTokenAction();
             if (refreshed) {
                 // Riprova fetchUser con il nuovo token
                 console.log("Retrying fetchUser after token refresh...");
                 await this.fetchUser(); // Chiamata ricorsiva (attenzione ai loop infiniti)
                 // Se anche questo fallisce, l'errore verrà catturato di nuovo e farà logout
                 return; // Esce per evitare il logout immediato sotto
             }
        }
        // Se non è 401 o il refresh fallisce, fai logout
        this.logout();
      }
    },

    async refreshTokenAction() {
      if (!this.refreshToken) {
        return false; // Non si può fare refresh senza refresh token
      }

      // Determina l'endpoint corretto in base al ruolo (se disponibile)
      // Se il ruolo non è noto, proviamo prima quello studente se il token contiene 'is_student'?
      // O assumiamo che se c'è un refresh token, l'utente DOVREBBE essere nello stato?
      // Approccio più sicuro: basarsi sul ruolo nello stato.
      const isStudent = this.userRole === 'Studente';
      const refreshEndpoint = isStudent ? '/auth/student/token/refresh/' : '/auth/token/refresh/';
      console.log(`Attempting token refresh using endpoint: ${refreshEndpoint} for role: ${this.userRole}`); // Debug

      try {
        // Usa apiClient importato
        const response = await apiClient.post(refreshEndpoint, {
          refresh: this.refreshToken,
        });
        const { access } = response.data;
        // Il refresh token potrebbe essere ruotato, ma per ora assumiamo di no
        this.setTokens(access, this.refreshToken);
        return true;
      } catch (error) {
        console.error("Failed to refresh token:", error);
        this.logout(); // Logout se il refresh fallisce
        return false;
      }
    },

    logout() {
      console.log("Logging out..."); // Debug
      // Idealmente, dovremmo invalidare il token sul backend se usiamo blacklist
      // Ma con Simple JWT senza blacklist, basta rimuovere i token dal frontend
      this.clearAuth();
      // Reindirizza alla pagina di login di default (docente/admin)
      router.push({ name: 'teacher-admin-login' });
    },

    // Azione per controllare lo stato iniziale (es. all'avvio dell'app)
    async checkInitialAuth() {
        console.log("Checking initial auth state..."); // Debug
        if (this.accessToken && !this.user) {
            // Se abbiamo un token ma non i dati utente, prova a recuperarli
            await this.fetchUser();
        } else if (this.accessToken && this.user) {
            console.log("User already loaded from localStorage:", this.user); // Debug
            // Potremmo voler verificare la validità del token qui con /api/auth/token/verify/
            // o semplicemente lasciare che le chiamate API falliscano e gestiscano il refresh/logout
        } else {
            console.log("No initial token found."); // Debug
        }
    }
  },
})