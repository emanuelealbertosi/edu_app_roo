import { defineStore } from 'pinia';
import { ref, computed } from 'vue'; // Importa ref e computed
import { useRouter } from 'vue-router'; // Importa useRouter
import AuthService from '@/api/auth';
import routerInstance from '@/router'; // Importa l'istanza del router per coerenza

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
}

// Usa la sintassi setup store
export const useAuthStore = defineStore('auth', () => {
  // State (usando ref)
  const user = ref<StudentData | null>(AuthService.getUser());
  const token = ref<string | null>(localStorage.getItem('auth_token'));
  const isAuthenticated = ref<boolean>(AuthService.isAuthenticated());
  const loading = ref<boolean>(false);
  const error = ref<string | null>(null);
  const router = useRouter(); // Ottieni l'istanza del router qui

  // Getters (come computed properties)
  const userFullName = computed((): string => {
    if (!user.value) return '';
    return `${user.value.first_name} ${user.value.last_name}`;
  });

  const isUserAuthenticated = computed((): boolean => {
    return isAuthenticated.value;
  });

  // Actions (come funzioni)
  async function login(studentCode: string, pin: string): Promise<void> {
    loading.value = true;
    error.value = null;
    try {
      const response = await AuthService.login({ student_code: studentCode, pin: pin });
      user.value = response.student;
      token.value = response.access;
      isAuthenticated.value = true;
      // Salva in localStorage (AuthService lo fa già, ma per sicurezza)
      localStorage.setItem('auth_token', response.access);
      localStorage.setItem('user', JSON.stringify(response.student));
    } catch (err) {
      error.value = 'Errore di autenticazione. Verifica le tue credenziali.';
      console.error('Authentication error:', err);
      // Pulisci stato in caso di errore
      user.value = null;
      token.value = null;
      isAuthenticated.value = false;
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // Logout action (ora async e usa il router definito sopra)
  async function logout(): Promise<void> {
    console.log("Logging out student...");
    AuthService.logout(); // Rimuove da localStorage
    user.value = null;
    token.value = null;
    isAuthenticated.value = false;
    try {
      // Usiamo l'istanza del router ottenuta con useRouter()
      await router.push({ name: 'login' }); 
    } catch (e) {
        console.error("Errore durante il redirect post-logout:", e);
        // Fallback o gestione alternativa se il push fallisce
        // Potrebbe essere necessario usare window.location se il router ha problemi
        // window.location.href = '/login'; 
    }
  }

  async function checkAuth(): Promise<boolean> {
    loading.value = true;
    try {
      const isValid = await AuthService.checkTokenValidity();
      isAuthenticated.value = isValid;
      if (!isValid) {
        user.value = null;
        token.value = null;
        // AuthService.logout() è già chiamato in checkTokenValidity in caso di 401
      } else {
         // Se valido ma user non è nello stato, prova a caricarlo da localStorage
         if (!user.value) {
             user.value = AuthService.getUser();
         }
      }
      return isValid;
    } catch (err) {
      isAuthenticated.value = false;
      user.value = null;
      token.value = null;
      return false;
    } finally {
      loading.value = false;
    }
  }

  // Inizializzazione (simile a quella del teacher store)
  if (token.value && !user.value) {
     console.warn("Auth Store Studente: Token trovato ma user non presente. Caricamento da localStorage.");
     user.value = AuthService.getUser();
     // Idealmente, verifica il token qui
  }


  // Ritorna stato, getters (computed) e actions
  return {
    user,
    token,
    isAuthenticated: isUserAuthenticated, // Esponi il computed getter
    loading,
    error,
    userFullName, // Esponi il computed getter
    login,
    logout,
    checkAuth
  };
});