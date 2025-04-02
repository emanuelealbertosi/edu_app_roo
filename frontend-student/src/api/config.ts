import axios from 'axios';

// Crea un'istanza axios configurata per l'API
const apiClient = axios.create({
  // URL base del backend. In produzione, questo potrebbe essere un URL assoluto
  baseURL: 'http://localhost:8000/api/', // Ripristinato baseURL generico
  
  // Headers di default per tutte le richieste
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  
  // Timeout per le richieste in ms (5 secondi)
  timeout: 5000
});

// Interceptor per aggiungere automaticamente il token JWT alle richieste
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Interceptor per gestire le risposte e gli errori
apiClient.interceptors.response.use(
  response => {
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
        localStorage.removeItem('auth_token');
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
    
    return Promise.reject(error);
  }
);

export default apiClient;