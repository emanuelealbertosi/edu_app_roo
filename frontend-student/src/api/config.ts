import axios from 'axios';
import { useUiStore } from '@/stores/ui';
import AuthService from './auth'; // Importa AuthService per il refresh
import router from '@/router'; // Importa il router per il redirect al login

// Crea un'istanza axios configurata per l'API
const apiClient = axios.create({
  // URL base del backend. Viene letto dalla variabile d'ambiente VITE_API_BASE_URL
  // che viene impostata durante il build Docker.
  // In sviluppo locale (npm run dev), Vite usa il file .env.development o simili.
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/',
  
  // Headers di default per tutte le richieste
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  // Timeout per le richieste in ms (aumentato a 30 secondi per server con risorse limitate)
  timeout: 30000
});

// Interceptor per aggiungere automaticamente il token JWT alle richieste
// Interceptor per aggiungere token JWT e tracciare inizio richiesta
apiClient.interceptors.request.use(
  config => {
    // Ottieni lo store solo quando serve (all'interno dell'interceptor)
    // Questo evita problemi di inizializzazione di Pinia prima dell'app Vue
    const uiStore = useUiStore();
    uiStore.apiRequestStarted(); // Segnala inizio richiesta

    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    // Anche in caso di errore nella configurazione della richiesta, segnala la fine
    const uiStore = useUiStore();
    uiStore.apiRequestEnded();
    return Promise.reject(error);
  }
);

// Interceptor per gestire le risposte e gli errori
// Interceptor per gestire le risposte e tracciare fine richiesta
apiClient.interceptors.response.use(
  response => {
    // Segnala fine richiesta in caso di successo
    const uiStore = useUiStore();
    uiStore.apiRequestEnded();
    return response;
  },
  async error => { // Trasforma in async per await su refreshToken
    const originalRequest = error.config;
    const uiStore = useUiStore(); // Ottieni lo store UI

    // Gestione degli errori standard
    if (error.response) {
      console.error('API Error:', error.response.data);

      // Gestione specifica per 401 Unauthorized (Token scaduto/invalido)
      // Aggiungi _retry per evitare loop infiniti se anche il refresh fallisce con 401
      if (error.response.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true; // Marca la richiesta come ritentata
        try {
          console.log('Tentativo di refresh del token...');
          const newAccessToken = await AuthService.refreshToken();
          console.log('Refresh token riuscito.');
          // Aggiorna l'header di Axios per le richieste future
          axios.defaults.headers.common['Authorization'] = 'Bearer ' + newAccessToken;
          // Aggiorna l'header della richiesta originale fallita
          originalRequest.headers['Authorization'] = 'Bearer ' + newAccessToken;
          // Ritenta la richiesta originale con il nuovo token
          return apiClient(originalRequest);
        } catch (refreshError: any) {
          console.error('Refresh token fallito:', refreshError.message || refreshError);
          // Se il refresh fallisce, esegui il logout e reindirizza al login
          AuthService.logout(); // Assicura pulizia localStorage
          // Usa l'istanza del router importata
          router.push({ name: 'login', query: { sessionExpired: 'true' } });
          // Reietta l'errore originale o quello del refresh per fermare la catena
          uiStore.apiRequestEnded(); // Segnala fine richiesta
          return Promise.reject(refreshError);
        }
      } else if (error.response.status === 401 && originalRequest._retry) {
         // Se anche il refresh ritorna 401, evita loop e fai logout
         console.error('Refresh token ha restituito 401. Logout forzato.');
         AuthService.logout();
         router.push({ name: 'login', query: { sessionExpired: 'true' } });
      }
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Request error:', error.message);
    }

    // Segnala fine richiesta anche in caso di errore non gestito dal refresh
    uiStore.apiRequestEnded();
    return Promise.reject(error);
  }
);

// Crea una seconda istanza axios SENZA interceptor per il token
// Utile per endpoint pubblici come la registrazione o la validazione del token
export const publicApiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 30000
});

// Interceptor solo per tracciare inizio/fine richiesta (senza token)
publicApiClient.interceptors.request.use(
  config => {
    const uiStore = useUiStore();
    uiStore.apiRequestStarted();
    return config;
  },
  error => {
    const uiStore = useUiStore();
    uiStore.apiRequestEnded();
    return Promise.reject(error);
  }
);

publicApiClient.interceptors.response.use(
  response => {
    const uiStore = useUiStore();
    uiStore.apiRequestEnded();
    return response;
  },
  error => {
    // Gestione errori simile, ma senza logout automatico su 401
    if (error.response) {
      console.error('Public API Error:', error.response.data);
    } else if (error.request) {
      console.error('No response received (Public API):', error.request);
    } else {
      console.error('Request error (Public API):', error.message);
    }
    const uiStore = useUiStore();
    uiStore.apiRequestEnded();
    return Promise.reject(error);
  }
);

export default apiClient; // Esporta l'istanza principale come default