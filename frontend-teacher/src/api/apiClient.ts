import axios from 'axios';
import { useAuthStore } from '@/stores/auth'; // Assumendo che lo store sia qui
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
    const authStore = useAuthStore();
    const token = authStore.accessToken; // Prendi il token di accesso dallo store
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
    const authStore = useAuthStore();

    // Controlla se l'errore è 401 e non è una richiesta di refresh fallita
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Marca la richiesta per evitare loop infiniti

      try {
        console.log('Access token expired, attempting refresh...');
        await authStore.refreshToken(); // Tenta di rinnovare il token
        console.log('Token refreshed successfully.');
        // Riprova la richiesta originale con il nuovo token
        originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        console.error('Unable to refresh token:', refreshError);
        // Se il refresh fallisce, esegui il logout
        authStore.logout();
        // Reindirizza alla pagina di login
        router.push({ name: 'Login' }); // Assicurati che 'Login' sia il nome corretto della rotta
        return Promise.reject(refreshError); // Rifiuta la promise
      }
    }

    // Per altri errori, rigetta la promise
    return Promise.reject(error);
  }
);

export default apiClient;