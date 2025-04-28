import axios from 'axios';
import { useUiStore } from '@/stores/ui'; // Importa lo store UI

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

    let token: string | null = null;
    try {
      const persistedStateString = localStorage.getItem('sharedAuth'); // Leggi lo stato persistito
      if (persistedStateString) {
        const persistedState = JSON.parse(persistedStateString);
        token = persistedState?.accessToken || null; // Estrai l'accessToken
      }
    } catch (e) {
      console.error("Failed to parse persisted auth state from localStorage:", e);
      token = null; // Assicurati che il token sia null se il parsing fallisce
    }

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    } else {
      // Opzionale: rimuovi l'header se il token non è trovato,
      // per evitare di inviare un header "Bearer null" o simile.
      delete config.headers.Authorization;
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
  error => {
    // Gestione degli errori standard
    if (error.response) {
      // Errore server (status code non 2xx)
      console.error('API Error:', error.response.data);
      
      // Se riceviamo un 401 (Unauthorized), potremmo voler reindirizzare al login
      if (error.response.status === 401) {
        // Qui potremmo gestire il logout
        // Rimuovi lo stato persistito condiviso. Idealmente, questo dovrebbe
        // essere gestito chiamando sharedAuthStore.clearAuthData() nell'app.
        localStorage.removeItem('sharedAuth');
        // In un'app reale, potremmo usare il router per reindirizzare
        // router.push('/login');
      }
    } else if (error.request) {
      // Richiesta fatta ma nessuna risposta ricevuta
      console.error('No response received:', error.request);
    } else {
      // Errore nella configurazione della richiesta
      console.error('Request error:', error.message);
    }
    
    // Segnala fine richiesta anche in caso di errore
    const uiStore = useUiStore();
    uiStore.apiRequestEnded();
    return Promise.reject(error);
  }
);

export default apiClient;