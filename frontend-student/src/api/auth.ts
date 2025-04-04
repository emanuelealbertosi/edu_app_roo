import apiClient from './config';
import axios, { AxiosError } from 'axios';

// Tipi per TypeScript
interface LoginCredentials {
  student_code: string; // Cambiato da email
  pin: string;          // Cambiato da password
}

interface LoginResponse {
  access: string; // Cambiato da token
  refresh: string; // Aggiunto refresh token (anche se non lo usiamo subito)
  student: { // Cambiato da user
    id: number;
    // email: string; // Lo studente non ha email nel modello
    first_name: string;
    last_name: string;
    student_code: string; // Aggiunto student_code
    // Aggiungere altri campi restituiti da StudentSerializer se necessario
    full_name: string;
    teacher: number; // ID del docente
    teacher_username: string;
    is_active: boolean;
    created_at: string;
  };
}

/**
 * Servizio per l'autenticazione degli utenti
 */
const AuthService = {
  /**
   * Effettua il login di uno studente
   * @param credentials - Credenziali login (email e password)
   * @returns Promise con la risposta contenente token e dati utente
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      // Aggiunto prefisso completo relativo a /api/
      const response = await apiClient.post<LoginResponse>('student/auth/student/login/', credentials);
      
      // Salviamo il token e i dati utente in localStorage per uso futuro
      if (response.data && response.data.access && response.data.student) { // Verifica 'access' e 'student'
        localStorage.setItem('auth_token', response.data.access); // Usa 'access'
        localStorage.setItem('user', JSON.stringify(response.data.student)); // Usa 'student'
      }
      
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      // Rilanciamo l'errore per gestirlo nel componente
      throw error;
    }
  },
  
  /**
   * Effettua il logout dell'utente
   */
  logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    // In un'app reale potremmo anche fare una chiamata al backend per invalidare il token
  },
  
  /**
   * Verifica se l'utente è autenticato
   * @returns true se l'utente è autenticato, false altrimenti
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('auth_token');
  },
  
  /**
   * Ottiene i dati dell'utente autenticato
   * @returns dati dell'utente o null se non autenticato
   */
  getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
  
  /**
   * Verifica se il token è ancora valido
   * In una implementazione completa questo dovrebbe verificare se il token è scaduto
   * o fare una chiamata al backend per verificare la validità
   */
  async checkTokenValidity(): Promise<boolean> {
    try {
      if (!this.isAuthenticated()) {
        return false;
      }
      
      // Possiamo fare una chiamata a un endpoint protetto per verificare
      // che il token sia ancora valido
      // Aggiunto prefisso completo relativo a /api/
      await apiClient.get('student/test-auth/');
      return true;
    } catch (error) {
      console.error('Token validation error:', error);
      // Se riceviamo un 401, il token non è valido
      if (axios.isAxiosError(error) && error.response && error.response.status === 401) {
        this.logout();
      }
      return false;
    }
  }
};

export default AuthService;