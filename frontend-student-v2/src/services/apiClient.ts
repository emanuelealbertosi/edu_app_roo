import axios from 'axios';
import useAuthStore from '../stores/authStore'; // Import auth store per accedere al token

// Configura l'URL base dell'API.
// Assumiamo che il backend Django sia in esecuzione su localhost:8000
// e che le rotte API siano sotto /api/
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/';

// Crea un'istanza di axios con configurazioni predefinite
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // Potremmo aggiungere altri header di default qui se necessario
  },
});

// Aggiungi un interceptor per includere il token JWT (se presente) in ogni richiesta
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    console.log('[API Interceptor] Token from store:', token ? `***${token.slice(-6)}` : null); // Logga parte del token o null
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('[API Interceptor] Authorization header set for URL:', config.url);
    } else {
      console.log('[API Interceptor] No token found, Authorization header NOT set for URL:', config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Potremmo aggiungere anche interceptor per le risposte (es. per gestire errori 401/403 globalmente)
// apiClient.interceptors.response.use(...)

export default apiClient;