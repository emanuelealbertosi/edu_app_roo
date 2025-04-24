import { defineStore } from 'pinia';
// Rimosso import axios locale
import apiClient from '@/services/api'; // Importa l'istanza Axios condivisa e configurata
// import type { Topic } from '@/types/lezioni';
// Rimosso blocco creazione apiClient locale e interceptor locale

interface Topic {
    id: number;
    name: string;
    description: string;
    subject: number; // ID della materia
    subject_name?: string; // Nome materia (opzionale, dal serializer)
    // Aggiungere altri campi se necessario
}

export const useTopicStore = defineStore('topics', {
  state: () => ({
    topics: [] as Topic[],
    isLoading: false,
    error: null as string | null,
  }),

  actions: {
    // Passiamo subjectId come argomento opzionale per filtrare
    async fetchTopics(subjectId: number | null = null) {
      this.isLoading = true;
      this.error = null;
      // Aggiunto prefisso /lezioni/
      let url = '/lezioni/topics/';
      if (subjectId !== null) {
        url += `?subject_id=${subjectId}`; // Aggiunge il parametro di query per filtrare
      }
      try {
        const response = await apiClient.get(url);
        this.topics = response.data;
      } catch (err: any) {
        console.error("Errore nel caricamento degli argomenti:", err);
        this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
        this.topics = [];
      } finally {
        this.isLoading = false;
      }
    },

    async addTopic(topicData: { name: string; subject: number; description?: string }) {
      this.isLoading = true;
      this.error = null;
      try {
        // Aggiunto prefisso /lezioni/
        const response = await apiClient.post('/lezioni/topics/', topicData);
        // Aggiunge o ricarica la lista
        // Potrebbe essere meglio ricaricare se l'ordinamento è importante
        // await this.fetchTopics(topicData.subject); // Ricarica per la materia specifica
        this.topics.push(response.data); // Aggiunge semplicemente per ora
        return true;
      } catch (err: any) {
        console.error("Errore nell'aggiunta dell'argomento:", err);
        this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
        // Gestire errori specifici dei campi se necessario
        return false;
      } finally {
        this.isLoading = false;
      }
    },

    async updateTopic(topicId: number, topicData: { name?: string; subject?: number; description?: string }) {
        this.isLoading = true;
        this.error = null;
        try {
            // Aggiunto prefisso /lezioni/
            const response = await apiClient.patch(`/lezioni/topics/${topicId}/`, topicData);
            const index = this.topics.findIndex(t => t.id === topicId);
            if (index !== -1) {
                // Aggiorna mantenendo i campi non modificati
                this.topics[index] = { ...this.topics[index], ...response.data };
            }
            return true;
        } catch (err: any) {
            console.error("Errore nell'aggiornamento dell'argomento:", err);
            this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
            return false;
        } finally {
            this.isLoading = false;
        }
    },

     async deleteTopic(topicId: number) {
        this.isLoading = true;
        this.error = null;
        try {
            // Aggiunto prefisso /lezioni/
            await apiClient.delete(`/lezioni/topics/${topicId}/`);
            this.topics = this.topics.filter(t => t.id !== topicId);
            return true;
        } catch (err: any) {
            console.error("Errore nell'eliminazione dell'argomento:", err);
            this.error = err.response?.data?.detail || err.message || 'Errore sconosciuto';
             if (err.response?.status === 403) { // Forbidden (o 400 Bad Request a seconda di come è gestito IntegrityError)
                 this.error = err.response.data.detail || "Impossibile eliminare l'argomento (potrebbe contenere lezioni).";
            }
            return false;
        } finally {
            this.isLoading = false;
        }
    },

  },
});