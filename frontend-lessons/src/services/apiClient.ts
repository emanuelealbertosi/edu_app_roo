import axios from 'axios';
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa lo store condiviso

// Assumendo che l'URL base dell'API sia configurato nelle variabili d'ambiente
// o che sia lo stesso server che serve il frontend.
// Per questo esempio, lo imposteremo direttamente.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    // Potresti voler aggiungere qui la logica per includere i token di autenticazione,
    // ad esempio leggendoli dallo localStorage o da uno store Pinia.
  },
});

// Interceptor per aggiungere il token JWT alle richieste, se disponibile
apiClient.interceptors.request.use(
  async (config) => { // Modificato in async per attendere l'inizializzazione dello store se necessario
    const sharedAuthStore = useSharedAuthStore();
    // Controlla se $persistedState e isReady esistono prima di chiamarli
    if (sharedAuthStore.$persistedState && typeof sharedAuthStore.$persistedState.isReady === 'function') {
      try {
        await sharedAuthStore.$persistedState.isReady();
      } catch (e) {
        console.error('[apiClient] Errore durante sharedAuthStore.$persistedState.isReady():', e);
        // Potresti voler gestire questo errore in modo più specifico
      }
    } else {
      // Se $persistedState o isReady non sono disponibili, potrebbe esserci un problema
      // con l'inizializzazione della persistenza o la sua configurazione asincrona.
      // Logga un avviso se non in ambiente di produzione.
      if (import.meta.env.MODE !== 'production') {
        console.warn(
          '[apiClient] sharedAuthStore.$persistedState.isReady() non disponibile o non è una funzione. ' +
          'Procedendo senza attendere esplicitamente l\'idratazione della persistenza. ' +
          'Questo potrebbe portare a problemi di autenticazione se il token non è ancora caricato.'
        );
      }
    }
    const accessToken = sharedAuthStore.accessToken;
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Puoi aggiungere interceptor per le risposte qui, ad esempio per gestire errori globali
// apiClient.interceptors.response.use(...)

export default apiClient;