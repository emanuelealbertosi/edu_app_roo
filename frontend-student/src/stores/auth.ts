import { defineStore } from 'pinia';
import AuthService from '@/api/auth';

// Interfaccia aggiornata per riflettere i dati dello studente dalla risposta API
interface StudentData {
  id: number;
  first_name: string;
  last_name: string;
  student_code: string;
  full_name: string;
  teacher: number;
  teacher_username: string;
  is_active: boolean;
  created_at: string;
  // Aggiungere altri campi se necessario
}

interface AuthState {
  user: StudentData | null; // Usa la nuova interfaccia
  token: string | null; // Manteniamo 'token' per l'access token
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: AuthService.getUser(),
    token: localStorage.getItem('auth_token'),
    isAuthenticated: AuthService.isAuthenticated(),
    loading: false,
    error: null
  }),
  
  getters: {
    // Ottiene il nome completo dell'utente (first_name + last_name)
    userFullName(state): string {
      if (!state.user) return '';
      return `${state.user.first_name} ${state.user.last_name}`;
    },
    
    // Verifica se l'utente è autenticato
    isUserAuthenticated(state): boolean {
      return state.isAuthenticated;
    }
  },
  
  actions: {
    /**
     * Effettua il login dell'utente
     */
    async login(studentCode: string, pin: string): Promise<void> { // Parametri cambiati
      this.loading = true;
      this.error = null;
      
      try {
        const response = await AuthService.login({ student_code: studentCode, pin: pin }); // Passa i parametri corretti
        
        // Aggiorna lo stato con i dati corretti dalla risposta
        this.user = response.student; // Usa response.student
        this.token = response.access; // Usa response.access per il token
        this.isAuthenticated = true;
      } catch (error) {
        this.error = 'Errore di autenticazione. Verifica le tue credenziali.';
        console.error('Authentication error:', error);
        throw error;
      } finally {
        this.loading = false;
      }
    },
    
    /**
     * Effettua il logout dell'utente
     */
    logout(): void {
      AuthService.logout();
      this.user = null;
      this.token = null;
      this.isAuthenticated = false;
    },
    
    /**
     * Verifica se il token dell'utente è ancora valido
     */
    async checkAuth(): Promise<boolean> {
      this.loading = true;
      try {
        const isValid = await AuthService.checkTokenValidity();
        this.isAuthenticated = isValid;
        
        if (!isValid) {
          this.user = null;
          this.token = null;
        }
        
        return isValid;
      } catch (error) {
        this.isAuthenticated = false;
        this.user = null;
        this.token = null;
        return false;
      } finally {
        this.loading = false;
      }
    }
  }
});