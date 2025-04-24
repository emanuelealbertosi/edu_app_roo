import axios from 'axios';
// Rimosso import non utilizzato: import { useAuthStore } from '@/stores/auth';

// Legge l'URL base dell'API dalla variabile d'ambiente VITE_API_BASE_URL (per sviluppo locale con .env.local).
// Se non definita (es. build Docker senza args), usa '/api' come fallback, affidandosi al proxy Nginx.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

console.log(`[api.ts] Creating Axios instance with effective baseURL: ${API_BASE_URL}`); // Debug

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Interceptor per aggiungere il token JWT alle richieste
apiClient.interceptors.request.use(config => {
  // È più sicuro leggere il token direttamente da localStorage qui,
  // perché lo store potrebbe non essere ancora inizializzato o accessibile facilmente.
  const token = localStorage.getItem('accessToken');
  if (token) {
    // Non loggare il token stesso per sicurezza
    console.log(`[api.ts Interceptor] Adding token from localStorage to request for ${config.url}`);
    config.headers.Authorization = `Bearer ${token}`;
  } else {
    console.log(`[api.ts Interceptor] No token found in localStorage for request to ${config.url}`);
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// Interceptor per gestire errori 401 (Unauthorized) e tentare il refresh del token
// NOTA: Questo aggiunge dipendenza ciclica potenziale se api.ts importa da auth.ts e viceversa.
// Gestire con attenzione o spostare la logica di refresh nello store.
/*
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    // Controlla se l'errore è 401 e non è un tentativo di retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true; // Marca come tentativo di retry
      try {
        console.log('[api.ts Interceptor] Attempting token refresh on 401...');
        const authStore = useAuthStore(); // Ottieni istanza dello store
        const refreshed = await authStore.refreshTokenAction(); // Chiama l'azione di refresh
        if (refreshed) {
          console.log('[api.ts Interceptor] Token refreshed, retrying original request...');
          // Aggiorna l'header della richiesta originale con il nuovo token
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${authStore.accessToken}`;
          originalRequest.headers['Authorization'] = `Bearer ${authStore.accessToken}`;
          // Ritenta la richiesta originale
          return apiClient(originalRequest);
        } else {
           console.log('[api.ts Interceptor] Token refresh failed.');
           // Se il refresh fallisce, il logout viene gestito da refreshTokenAction
        }
      } catch (refreshError) {
        console.error('[api.ts Interceptor] Error during token refresh:', refreshError);
        // Assicurati che il logout avvenga se c'è un errore catastrofico nel refresh
        const authStore = useAuthStore();
        authStore.logout(); // Forza logout
        return Promise.reject(refreshError);
      }
    }
    // Per altri errori o se il refresh fallisce/non è possibile, rigetta l'errore
    return Promise.reject(error);
  }
);
*/

export default apiClient;