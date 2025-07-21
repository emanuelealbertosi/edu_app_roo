import axios from 'axios';
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa lo store condiviso
import { useAuthStore } from '@/stores/auth'; // Importa lo store auth per refreshTokenAction

// Assumendo che l'URL base dell'API sia configurato nelle variabili d'ambiente
// o che sia lo stesso server che serve il frontend.
// Per questo esempio, lo imposteremo direttamente.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export function createApiClient() {
  console.log('[DEBUG apiClient.ts] createApiClient FUNZIONE CHIAMATA.');
  console.log('[DEBUG apiClient.ts] Modulo apiClient.ts in esecuzione (prima della creazione dell\'istanza)');

  const instance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  console.log('[DEBUG apiClient.ts] Istanza Axios creata. Prima della registrazione interceptor richiesta.');
  // Interceptor per aggiungere il token JWT alle richieste, se disponibile
  instance.interceptors.request.use(
    async (config) => {
      console.log('[DEBUG apiClient.ts] Interceptor RICHIESTA eseguito per:', config.url);
      const sharedAuthStore = useSharedAuthStore();
      if (sharedAuthStore.$persistedState && typeof sharedAuthStore.$persistedState.isReady === 'function') {
        try {
          console.log('[apiClient Request Interceptor] Waiting for sharedAuthStore to be ready...');
          await sharedAuthStore.$persistedState.isReady();
          console.log('[apiClient Request Interceptor] sharedAuthStore is ready. AccessToken:', sharedAuthStore.accessToken ? 'Exists' : 'null');
        } catch (e) {
          console.error('[apiClient Request Interceptor] Error waiting for sharedAuthStore to be ready:', e);
        }
      } else {
        if (import.meta.env.MODE !== 'production') {
          console.warn('[apiClient Request Interceptor] sharedAuthStore.$persistedState.isReady() non disponibile.');
        }
      }
      const accessToken = sharedAuthStore.accessToken;
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
        console.log('[apiClient Request Interceptor] Token aggiunto all\'header Authorization.');
      } else {
        console.log('[apiClient Request Interceptor] Nessun accessToken trovato in sharedAuthStore.');
      }
      
      // Se la richiesta contiene FormData, lascia che il browser imposti il Content-Type.
      // Rimuovi l'header 'Content-Type' preimpostato per evitare conflitti.
      if (config.data instanceof FormData) {
        delete config.headers['Content-Type'];
      }
      
      return config;
    },
    (error) => {
      console.error('[apiClient Request Interceptor] Errore:', error);
      return Promise.reject(error);
    }
  );
  console.log('[DEBUG apiClient.ts] Dopo la registrazione interceptor richiesta. Prima della registrazione interceptor risposta.');

  // Interceptor per le risposte per gestire il refresh del token in caso di 401
  instance.interceptors.response.use(
   (response) => {
     return response;
   },
   async (error) => {
     console.log('[DEBUG apiClient Response Interceptor] Interceptor RISPOSTA invoked for error.');
     console.log('[DEBUG apiClient Response Interceptor] Error Status:', error.response?.status);
     console.log('[DEBUG apiClient Response Interceptor] Error Config URL:', error.config?.url);

     const originalRequest = error.config;
     const sharedAuthStore = useSharedAuthStore();

     if (sharedAuthStore.$persistedState && typeof sharedAuthStore.$persistedState.isReady === 'function') {
       try {
         console.log('[apiClient Response Interceptor] Waiting for sharedAuthStore to be ready (in response)...');
         await sharedAuthStore.$persistedState.isReady();
         console.log('[apiClient Response Interceptor] sharedAuthStore is ready (in response). AccessToken:', sharedAuthStore.accessToken ? 'Exists' : 'null', 'RefreshToken:', sharedAuthStore.refreshToken ? 'Exists' : 'null');
       } catch (e) {
         console.error('[apiClient Response Interceptor] Error waiting for sharedAuthStore to be ready (in response):', e);
       }
     } else {
        if (import.meta.env.MODE !== 'production') {
            console.warn('[apiClient Response Interceptor] sharedAuthStore.$persistedState.isReady() non disponibile (in response).');
        }
     }

     if (error.response?.status === 401 && !originalRequest._retry && sharedAuthStore.refreshToken) {
       originalRequest._retry = true;
       console.log('[apiClient Response Interceptor] Condition met for token refresh. Attempting refresh.');
       try {
         const authStore = useAuthStore();
         const refreshed = await authStore.refreshTokenAction();

         if (refreshed) {
           console.log('[apiClient Response Interceptor] Token refreshed successfully. Retrying original request.');
           if (sharedAuthStore.accessToken) {
            originalRequest.headers.Authorization = `Bearer ${sharedAuthStore.accessToken}`;
           } else {
            console.error('[apiClient Response Interceptor] Token refresh reported success, but no access token. Aborting retry.');
            return Promise.reject(error);
           }
           // Usa la STESSA istanza per ritentare, non importare apiClient globalmente qui.
           return instance(originalRequest);
         } else {
           console.log('[apiClient Response Interceptor] Token refresh attempt returned false. Logout should have been handled.');
           return Promise.reject(error);
         }
       } catch (refreshError) {
         console.error('[apiClient Response Interceptor] Exception during token refresh attempt:', refreshError);
         return Promise.reject(error);
       }
     } else if (error.response?.status === 401) {
        console.warn(`[apiClient Response Interceptor] Received 401, but not attempting refresh. Retry: ${originalRequest._retry}, RefreshToken: ${!!sharedAuthStore.refreshToken}`);
        if (!sharedAuthStore.refreshToken) {
            console.log('[apiClient Response Interceptor] No refresh token, attempting logout.');
            try {
                const authStore = useAuthStore();
                authStore.logout();
            } catch (logoutError) {
                console.error("[apiClient Response Interceptor] Error calling logout:", logoutError);
            }
        }
     }
     return Promise.reject(error);
   }
  );
  console.log('[DEBUG apiClient.ts] Dopo la registrazione dell\'interceptor di risposta.');
  return instance;
}

// Esporta una singola istanza creata dalla funzione per mantenere la compatibilità
// con gli import esistenti, ma la funzione createApiClient può essere usata se necessario
// per creare nuove istanze o per forzare la riesecuzione della logica di configurazione.
const apiClient = createApiClient();
export default apiClient;

// Esporta anche le funzioni API specifiche che potrebbero essere state definite qui
// o importate e riesportate. Assicurati che usino l'istanza apiClient corretta.
// Esempio (se fetchGroups e assignLesson fossero definite qui):
// export const fetchGroups = async () => { return apiClient.get(...); }
// export const assignLesson = async (lessonId, studentIds, groupIds) => { return apiClient.post(...); }
// Per ora, assumiamo che siano importate da altrove e usino l'apiClient esportato.