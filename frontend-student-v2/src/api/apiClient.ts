import axios from 'axios';

// Configura l'URL base dell'API. Dovrebbe puntare al backend Django.
// Potrebbe essere letto da variabili d'ambiente.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor per aggiungere il token JWT STUDENTE alle richieste (se necessario per altre parti dell'app)
// Questo interceptor è diverso da quello del docente
apiClient.interceptors.request.use(
  async (config) => { // Rendi la funzione async
    // Importa lo store qui per evitare dipendenze circolari a livello di modulo
    // Correggi il percorso del file dello store
    const { useAuthStore } = await import('@/stores/authStore'); // Usa import() dinamico e percorso corretto
    const authStore = useAuthStore();
    const token = authStore.accessToken; // Prendi il token di accesso STUDENTE dallo store

    // Aggiungi il token solo se esiste e la richiesta non è per endpoint pubblici noti
    // (come login o registrazione)
    const publicPaths = ['/auth/student/login', '/register/student'];
    if (token && !publicPaths.some(path => config.url?.startsWith(path))) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


// Interceptor per gestire le risposte (opzionale per ora, potrebbe gestire errori comuni)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    // Correggi il percorso del file dello store
    const { useAuthStore } = await import('@/stores/authStore'); // Usa import() dinamico e percorso corretto
    const authStore = useAuthStore();

    // Gestione specifica per errori 401 (token studente scaduto)
    // Nota: Il refresh del token studente non è implementato nel backend fornito.
    // Se fosse implementato, la logica sarebbe simile a quella del docente.
    if (error.response?.status === 401 && !originalRequest._retry && authStore.isAuthenticated) {
       console.error('Student API request Unauthorized (401). Logging out.');
       // Non tentiamo il refresh (non implementato), eseguiamo il logout
       originalRequest._retry = true; // Evita loop se il logout fallisce o causa un altro 401
       authStore.logout(); // Esegui il logout dello studente
       // Reindirizza al login (potrebbe essere gestito da un navigation guard)
       // import router from '@/router'; // Importa il router se necessario
       // router.push({ name: 'Login' });
       return Promise.reject(new Error('Sessione studente scaduta. Effettuare nuovamente il login.'));
    }

    // Per altri errori, rigetta la promise
    return Promise.reject(error);
  }
);


export default apiClient;