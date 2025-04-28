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
  // Leggiamo lo stato persistito di sharedAuth da localStorage
  const persistedStateString = localStorage.getItem('sharedAuth');
  let token: string | null = null;

  if (persistedStateString) {
    try {
      const persistedState = JSON.parse(persistedStateString);
      token = persistedState.accessToken || null; // Estrai il token dallo stato persistito
    } catch (e) {
      console.error('[api.ts Interceptor] Failed to parse persisted sharedAuth state:', e);
    }
  }

  if (token) {
    // Non loggare il token stesso per sicurezza
    console.log(`[api.ts Interceptor] Adding token from persisted state to request for ${config.url}`);
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

// --- Funzioni Specifiche per Lezioni ---

/**
 * Assegna una lezione a studenti e/o gruppi specifici.
 * @param lessonId L'ID della lezione da assegnare.
 * @param studentIds Array degli ID degli studenti a cui assegnare la lezione.
 * @param groupIds Array degli ID dei gruppi a cui assegnare la lezione.
 * @returns La risposta dell'API (solitamente conferma o dettagli dell'assegnazione).
 */
export const assignLesson = async (lessonId: number, studentIds: number[], groupIds: number[]) => {
  console.log(`[api.ts] Assigning lesson ${lessonId} to students: [${studentIds.join(', ')}] and groups: [${groupIds.join(', ')}]`);
  try {
    // Corretto URL: aggiunto /lessons/ prima dell'ID
    const response = await apiClient.post(`/lezioni/lessons/${lessonId}/assign/`, {
      student_ids: studentIds,
      group_ids: groupIds,
    });
    console.log(`[api.ts] Lesson ${lessonId} assignment successful:`, response.data);
    return response.data;
  } catch (error) {
    console.error(`[api.ts] Error assigning lesson ${lessonId}:`, error);
    // Potrebbe essere utile rilanciare l'errore o gestirlo in modo più specifico
    // a seconda di come viene usato nello store/componente.
    throw error;
  }
};

// Aggiungere qui altre funzioni API specifiche per lezioni se necessario
// es. revokeLesson, getLessonDetails, ecc.

// --- Funzioni Specifiche per Gruppi ---

/**
 * Recupera l'elenco dei gruppi del docente autenticato.
 * @returns Un array di oggetti StudentGroup.
 */
export const fetchGroups = async () => {
  console.log(`[api.ts] Fetching groups...`);
  try {
    const response = await apiClient.get('/groups/'); // Assumendo endpoint standard
    console.log(`[api.ts] Groups fetched successfully:`, response.data);
    return response.data; // Assumendo che l'API restituisca direttamente l'array
  } catch (error) {
    console.error(`[api.ts] Error fetching groups:`, error);
    throw error;
  }
};


// Sarebbe opportuno spostare anche le chiamate API esistenti (implicite negli store)
// qui per centralizzare la logica API.