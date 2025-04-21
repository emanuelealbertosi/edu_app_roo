import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import apiClient from '../services/apiClient'; // Importa il client API

// TODO: Definire un tipo appropriato per Student invece di 'any'
// import type { Student } from '../types/user';

interface LoginCredentials {
  studentCode: string;
  pin: string;
}

// Interfaccia per la parte dello stato che verrà persistita
interface PersistedAuthState {
  isAuthenticated: boolean;
  student: any | null; // TODO: Sostituire 'any' con tipo Student
  token: string | null;
}

// Interfaccia per lo stato completo (persistito + non persistito)
interface AuthState extends PersistedAuthState {
  loading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => void;
  // checkAuthState?: () => void; // Opzionale
}

// Specifichiamo entrambi i tipi (completo e persistito) nel middleware persist
// persist<StatoCompleto, SetState, GetState, StatoPersistito>
const useAuthStore = create(
  persist<AuthState, [], [], PersistedAuthState>(
    (set, get) => ({
      // Stato iniziale (include tutti i campi, anche quelli non persistiti)
      isAuthenticated: false,
      student: null,
      token: null,
      loading: false,
      error: null,

      // Azione Login con chiamata API
      login: async (credentials) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.post('/student/auth/student/login/', { // URL corretto dall'analisi urls.py
            student_code: credentials.studentCode,
            pin: credentials.pin,
          });

          if (response.data && response.data.access && response.data.student) {
            const { access, student } = response.data;
            set({
              isAuthenticated: true,
              student: student,
              token: access,
              error: null,
              loading: false,
            });
            console.log('[AuthStore] Login successful');
            return true; // Indica successo
          } else {
            // Risposta inattesa dal backend
            throw new Error('Risposta API non valida durante il login.');
          }
        } catch (err: any) {
          console.error('[AuthStore] Login failed:', err);
          const errorMessage = err.response?.data?.detail || err.message || 'Login fallito. Riprova.';
          set({
            isAuthenticated: false,
            student: null,
            token: null,
            error: errorMessage,
            loading: false,
          });
          return false; // Indica fallimento
        }
      },

      // Azione Logout
      logout: () => {
        set({
          isAuthenticated: false,
          student: null,
          token: null,
          error: null,
          loading: false, // Assicura che loading sia false
        });
        // Non è necessario chiamare clearStorage manualmente se si usa persist con storage corretto
        console.log('[AuthStore] Logged out');
      },

      // checkAuthState: () => {
      //   // Logica per controllare se il token in localStorage è ancora valido all'avvio dell'app
      //   const token = get().token;
      //   if (token) {
      //     // Qui potresti fare una chiamata API per validare il token
      //     // o semplicemente assumere che l'utente sia loggato se il token esiste
      //     // e magari recuperare i dati utente aggiornati.
      //     // Per ora, se c'è un token, consideriamo l'utente loggato.
      //     set({ isAuthenticated: true });
      //     console.log('[AuthStore] Auth state checked, user is authenticated via persisted token.');
      //   } else {
      //      set({ isAuthenticated: false });
      //      console.log('[AuthStore] Auth state checked, no persisted token found.');
      //   }
      // }

    }),
    {
      name: 'auth-storage', // Nome della chiave in localStorage
      storage: createJSONStorage(() => localStorage), // Usa localStorage
      // Non serve più partialize, i tipi generici specificano cosa persistere
    }
  )
);

export default useAuthStore;