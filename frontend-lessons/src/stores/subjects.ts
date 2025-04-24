import { defineStore } from 'pinia';
// Rimosso import axios locale
import apiClient from '@/services/api'; // Importa l'istanza Axios condivisa e configurata
// import type { Subject } from '@/types/lezioni'; // Definiremo i tipi più avanti
// Rimosso blocco creazione apiClient locale e interceptor locale

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
        // Aggiunto prefisso /lezioni/
        const response = await apiClient.get('/lezioni/subjects/'); // Endpoint per listare le materie
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
        // Aggiunto prefisso /lezioni/
        const response = await apiClient.post('/lezioni/subjects/', subjectData);
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
            // Aggiunto prefisso /lezioni/
            const response = await apiClient.patch(`/lezioni/subjects/${subjectId}/`, subjectData); // Usa PATCH per aggiornamenti parziali
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
            // Aggiunto prefisso /lezioni/
            await apiClient.delete(`/lezioni/subjects/${subjectId}/`);
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