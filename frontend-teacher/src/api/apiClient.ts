import axios from 'axios';
import { useAuthStore } from '@/stores/auth'; // Store specifico Teacher (per azione refresh?)
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa store condiviso
import router from '@/router'; // Importa il router per i redirect

// Configura l'URL base dell'API. Dovrebbe puntare al backend Django.
// Potrebbe essere letto da variabili d'ambiente in un'app reale.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor per aggiungere il token JWT alle richieste
apiClient.interceptors.request.use(
  (config) => {
    // Usa lo store condiviso per prendere il token
    const sharedAuth = useSharedAuthStore();
    const token = sharedAuth.accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor per gestire le risposte, in particolare gli errori 401 (Unauthorized)
apiClient.interceptors.response.use(
  (response) => {
    // Se la risposta è OK, restituiscila
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    // Usa store condiviso per stato e store teacher per azione refresh specifica
    const sharedAuth = useSharedAuthStore();
    const authTeacherStore = useAuthStore(); // Per chiamare refreshTokenAction specifica del teacher

    // Controlla se l'errore è 401 e non è una richiesta di refresh fallita
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Marca la richiesta per evitare loop infiniti

      try {
        console.log('[API Interceptor Teacher] Access token expired or invalid, attempting refresh...');
        // Chiama l'azione di refresh specifica dello store teacher,
        // che a sua volta aggiornerà lo store condiviso.
        await authTeacherStore.refreshTokenAction();
        console.log('[API Interceptor Teacher] Token refreshed successfully via teacher action.');
        // Riprova la richiesta originale con il nuovo token dallo store condiviso
        originalRequest.headers.Authorization = `Bearer ${sharedAuth.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        console.error('[API Interceptor Teacher] Unable to refresh token:', refreshError);
        // Se il refresh fallisce, lo store teacher (o shared) dovrebbe aver già gestito il logout/clear.
        // Non chiamare logout() di nuovo qui per evitare doppioni.
        // sharedAuth.clearAuthData(); // Già fatto da refreshTokenAction in caso di errore
        // Reindirizza alla pagina di login del teacher (o alla root?)
        // La guardia di navigazione dovrebbe comunque intercettare e mandare al login corretto.
        // router.push({ name: 'login' }); // Usa il nome corretto della rotta login teacher
        // Meglio reindirizzare alla root e lasciare che le guardie facciano il loro lavoro
        window.location.href = '/';
        return Promise.reject(refreshError); // Rifiuta la promise
      }
    }

    // Per altri errori, rigetta la promise
    return Promise.reject(error);
  }
);

export default apiClient;