import { defineStore } from 'pinia';
import axios from 'axios'; // Riutilizziamo l'istanza configurata o ne creiamo una specifica
// import type { Subject } from '@/types/lezioni'; // Definiremo i tipi più avanti

// Assumiamo che l'istanza Axios sia configurata globalmente o importata da un modulo api.ts
// Per semplicità, usiamo un'istanza base qui, ma idealmente dovrebbe essere condivisa.
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/lezioni', // Specifica il path base per le lezioni
  headers: {
    'Content-Type': 'application/json',
  }
});

// Aggiungiamo l'interceptor anche qui se non è globale
// È meglio avere una singola istanza configurata globalmente (es. in un plugin o in main.ts)
import { useAuthStore } from './auth'; // Importa auth store per il token
apiClient.interceptors.request.use(config => {
  const authStore = useAuthStore();
  const token = authStore.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  // Gestione errori globale (es. refresh token) potrebbe andare qui
  return Promise.reject(error);
});


interface Subject {
    id: number;
    name: string;
    description: string;
    // Aggiungere altri campi se necessario (creator, timestamps, ecc.)
}

export const useSubjectStore = defineStore('subjects', {
  state: () => ({
    subjects: [] as Subject[],
    isLoading: false,
    error: null as string | null,
  }),

  actions: {
    async fetchSubjects() {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await apiClient.get('/subjects/'); // Endpoint per listare le materie
        this.subjects = response.data;
      } catch (err: any) {
        console.error("Errore nel caricamento delle materie:", err);
        this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
        this.subjects = []; // Resetta in caso di errore
      } finally {
        this.isLoading = false;
      }
    },

    async addSubject(subjectData: { name: string; description?: string }) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await apiClient.post('/subjects/', subjectData);
        // Aggiunge la nuova materia allo state locale (o ricarica la lista)
        this.subjects.push(response.data);
        return true; // Successo
      } catch (err: any) {
        console.error("Errore nell'aggiunta della materia:", err);
        this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
        // Potremmo voler estrarre errori specifici dei campi qui
        // if (err.response?.data) { this.error = JSON.stringify(err.response.data); }
        return false; // Fallimento
      } finally {
        this.isLoading = false;
      }
    },

    async updateSubject(subjectId: number, subjectData: { name?: string; description?: string }) {
        this.isLoading = true;
        this.error = null;
        try {
            const response = await apiClient.patch(`/subjects/${subjectId}/`, subjectData); // Usa PATCH per aggiornamenti parziali
            // Aggiorna la materia nello state locale
            const index = this.subjects.findIndex(s => s.id === subjectId);
            if (index !== -1) {
                this.subjects[index] = { ...this.subjects[index], ...response.data };
            }
            return true; // Successo
        } catch (err: any) {
            console.error("Errore nell'aggiornamento della materia:", err);
            this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
            return false; // Fallimento
        } finally {
            this.isLoading = false;
        }
    },

     async deleteSubject(subjectId: number) {
        this.isLoading = true;
        this.error = null;
        try {
            await apiClient.delete(`/subjects/${subjectId}/`);
            // Rimuovi la materia dallo state locale
            this.subjects = this.subjects.filter(s => s.id !== subjectId);
            return true; // Successo
        } catch (err: any) {
            console.error("Errore nell'eliminazione della materia:", err);
            this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
             // Gestire il caso in cui non si può eliminare (es. materie con argomenti)
            if (err.response?.status === 403) { // Forbidden (o altro codice in base all'implementazione backend)
                 this.error = err.response.data.detail || "Impossibile eliminare la materia (potrebbe contenere argomenti).";
            }
            return false; // Fallimento
        } finally {
            this.isLoading = false;
        }
    },

  },
});