import { defineStore } from 'pinia';
import { udaService } from '@/services/udaService';
import type { UDA, UDAContent } from '@/types/uda';

export const useUdaStore = defineStore('uda', {
  state: () => ({
    udas: [] as UDA[],
    currentUda: null as UDA | null,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchUdas(filters?: { status?: 'TODO' | 'IN_PROGRESS' | 'COMPLETED', courseId?: number }) {
      this.loading = true;
      this.error = null;
      try {
        const data = await udaService.getUdas(filters);
        this.udas = data;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to fetch UDAs';
        this.udas = [];
        console.error(err);
      } finally {
        this.loading = false;
      }
    },

    async fetchUda(udaId: number) {
      this.loading = true;
      this.error = null;
      try {
        const data = await udaService.getUda(udaId);
        this.currentUda = data;
        // Carica i contenuti se non sono già presenti o sono vuoti
        if (this.currentUda && (!this.currentUda.contents || this.currentUda.contents.length === 0)) {
           await this.fetchUdaContents(udaId);
        }
      } catch (err) {
        this.error = (err as Error).message || `Failed to fetch UDA ${udaId}`;
        this.currentUda = null;
        console.error(err);
      } finally {
        this.loading = false;
      }
    },

    async createUda(udaData: Partial<Omit<UDA, 'id' | 'teacher' | 'created_at' | 'updated_at' | 'contents' | 'topics' | 'subject' | 'subjects' | 'course' >> & { topics?: number[], subject_ids?: number[], course_id?: number | null, order_in_course?: number | null }) : Promise<UDA | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const payload = { ...udaData } as any; // Usiamo 'any' temporaneamente per flessibilità con subject_id vs subject_ids
        if (payload.topics && Array.isArray(payload.topics) && payload.topics.length > 0 && typeof payload.topics[0] === 'object' && payload.topics[0] !== null && 'id' in payload.topics[0]) {
            payload.topics = payload.topics.map((t: any) => t.id);
        }

        // Assicuriamoci che subject_ids sia un array, anche se vuoto, se non fornito
        if (payload.subject_ids === undefined) {
            payload.subject_ids = [];
        }
        
        // Rimuoviamo il vecchio subject_id se presente per errore
        delete payload.subject_id;

        // Se stiamo creando da un template, il backend gestirà la copia dei contenuti.
        // Rimuoviamo 'contents' dal payload per evitare conflitti o sovrascritture.
        if (payload.source_template_id) {
          delete payload.contents;
        }

        const newUda = await udaService.createUda(payload as Partial<UDA>);
        this.udas.push(newUda);
        // this.currentUda = newUda; // Opzionale: impostare come corrente
        return newUda;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to create UDA';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async updateUda(udaId: number, udaData: Partial<Omit<UDA, 'id' | 'teacher' | 'created_at' | 'updated_at' | 'contents' | 'topics' | 'subject' | 'subjects' | 'course'>> & { topics?: number[], subject_ids?: number[], course_id?: number | null }): Promise<UDA | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const payload = { ...udaData } as any; // Usiamo 'any' temporaneamente
         if (payload.topics && Array.isArray(payload.topics) && payload.topics.length > 0 && typeof payload.topics[0] === 'object' && payload.topics[0] !== null && 'id' in payload.topics[0]) {
            payload.topics = payload.topics.map((t: any) => t.id);
        }

        // Assicuriamoci che subject_ids sia un array se fornito, altrimenti non lo includiamo per PATCH parziali
        if (payload.subject_ids !== undefined && !Array.isArray(payload.subject_ids)) {
            // Potrebbe essere un errore, gestirlo o loggarlo
            console.warn('subject_ids is defined but not an array in updateUda, setting to empty array.');
            payload.subject_ids = [];
        }
        
        // Rimuoviamo il vecchio subject_id se presente per errore
        delete payload.subject_id;

        const updatedUda = await udaService.updateUda(udaId, payload as Partial<UDA>);
        const index = this.udas.findIndex((u: UDA) => u.id === udaId);
        if (index !== -1) {
          this.udas[index] = updatedUda;
        }
        if (this.currentUda?.id === udaId) {
          this.currentUda = updatedUda;
        }
        return updatedUda;
      } catch (err) {
        this.error = (err as Error).message || `Failed to update UDA ${udaId}`;
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async deleteUda(udaId: number) {
      this.loading = true;
      this.error = null;
      try {
        await udaService.deleteUda(udaId);
        this.udas = this.udas.filter((u: UDA) => u.id !== udaId);
        if (this.currentUda?.id === udaId) {
          this.currentUda = null;
        }
      } catch (err) {
        this.error = (err as Error).message || `Failed to delete UDA ${udaId}`;
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async fetchUdaContents(udaId: number): Promise<UDAContent[]> {
        this.loading = true;
        this.error = null;
        try {
            const contents = await udaService.getUdaContents(udaId);
            const sortedContents = contents.sort((a, b) => a.order - b.order);
            if (this.currentUda?.id === udaId) {
                this.currentUda.contents = sortedContents;
            }
            const udaInList = this.udas.find((u: UDA) => u.id === udaId);
            if (udaInList) {
                udaInList.contents = sortedContents;
            }
            return sortedContents;
        } catch (err) {
            this.error = (err as Error).message || `Failed to fetch contents for UDA ${udaId}`;
            console.error(err);
            if (this.currentUda?.id === udaId) this.currentUda.contents = [];
            const udaInList = this.udas.find((u: UDA) => u.id === udaId);
            if (udaInList) udaInList.contents = [];
            return [];
        } finally {
            this.loading = false;
        }
    },

    async addContentToUda(
      udaId: number,
      contentData: Partial<Omit<UDAContent, 'id' | 'uda_id' | 'created_at' | 'updated_at'>>,
      file?: File // Aggiunto parametro file opzionale
    ): Promise<UDAContent | undefined> {
      this.loading = true;
      this.error = null;
      try {
        // Passa il file al servizio se presente
        const newContent = await udaService.addContentToUda(udaId, contentData, file);
        const updateAndSortContents = (contentsArray?: UDAContent[]) => {
            if (!contentsArray) contentsArray = [];
            contentsArray.push(newContent);
            contentsArray.sort((a, b) => a.order - b.order);
            return contentsArray;
        };

        if (this.currentUda?.id === udaId) {
          this.currentUda.contents = updateAndSortContents(this.currentUda.contents);
        }
        const udaInList = this.udas.find((u: UDA) => u.id === udaId);
        if (udaInList) {
            udaInList.contents = updateAndSortContents(udaInList.contents);
        }
        return newContent;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to add content to UDA';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async updateContentInUda(
      udaId: number,
      contentId: number,
      contentData: Partial<Omit<UDAContent, 'id' | 'uda_id' | 'created_at' | 'updated_at'>>,
      file?: File // Aggiunto parametro file opzionale
    ): Promise<UDAContent | undefined> {
      this.loading = true;
      this.error = null;
      try {
        // Passa il file al servizio se presente
        const updatedContent = await udaService.updateUdaContent(udaId, contentId, contentData, file);
        const updateLocalContents = (contentsArray?: UDAContent[]) => {
            if (!contentsArray) return;
            const contentIndex = contentsArray.findIndex(c => c.id === contentId);
            if (contentIndex !== -1) {
                contentsArray[contentIndex] = updatedContent;
                contentsArray.sort((a, b) => a.order - b.order);
            }
        };
        if (this.currentUda?.id === udaId) {
            updateLocalContents(this.currentUda.contents);
        }
        const udaInList = this.udas.find((u: UDA) => u.id === udaId);
        if (udaInList) {
            updateLocalContents(udaInList.contents);
        }
        return updatedContent;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to update content in UDA';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async removeContentFromUda(udaId: number, contentId: number) {
      this.loading = true;
      this.error = null;
      try {
        await udaService.deleteUdaContent(udaId, contentId);
        const filterLocalContents = (contentsArray?: UDAContent[]): UDAContent[] => {
            return contentsArray?.filter(c => c.id !== contentId) || [];
        };
        if (this.currentUda?.id === udaId) {
          this.currentUda.contents = filterLocalContents(this.currentUda.contents);
        }
        const udaInList = this.udas.find((u: UDA) => u.id === udaId);
        if (udaInList) {
            udaInList.contents = filterLocalContents(udaInList.contents);
        }
      } catch (err) {
        this.error = (err as Error).message || 'Failed to remove content from UDA';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async completeActivityInUda(udaId: number, contentId: number, completed: boolean): Promise<UDAContent | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const updatedContent = await udaService.completeActivityInUda(udaId, contentId, completed);
         const updateLocalActivityCompletion = (contentsArray?: UDAContent[]) => {
            if (!contentsArray) return;
            const contentIndex = contentsArray.findIndex(c => c.id === contentId && c.content_type === 'ACTIVITY');
            if (contentIndex !== -1) {
                contentsArray[contentIndex] = updatedContent;
            }
        };
        if (this.currentUda?.id === udaId) {
            updateLocalActivityCompletion(this.currentUda.contents);
        }
        const udaInList = this.udas.find((u: UDA) => u.id === udaId);
        if (udaInList) {
            updateLocalActivityCompletion(udaInList.contents);
        }
        return updatedContent;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to complete activity in UDA';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },
    async updateUdaContentTeacherCompletion(udaId: number, contentId: number, completed: boolean): Promise<UDAContent | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const updatedContent = await udaService.updateUdaContentTeacherCompletion(udaId, contentId, completed);
        const updateLocalTeacherCompletion = (contentsArray?: UDAContent[]) => {
            if (!contentsArray) return;
            const contentIndex = contentsArray.findIndex(c => c.id === contentId);
            if (contentIndex !== -1) {
                contentsArray[contentIndex] = updatedContent; // L'API restituisce l'oggetto aggiornato
            }
        };
        if (this.currentUda?.id === udaId) {
            updateLocalTeacherCompletion(this.currentUda.contents);
        }
        const udaInList = this.udas.find((u: UDA) => u.id === udaId);
        if (udaInList) {
            updateLocalTeacherCompletion(udaInList.contents);
        }
        return updatedContent;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to update teacher completion status';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    }
  },
  getters: {
    getUdaById: (state) => (id: number): UDA | undefined => {
      return state.udas.find((uda: UDA) => uda.id === id);
    },
    getContentsForCurrentUda: (state): UDAContent[] => {
      return state.currentUda?.contents || [];
    },
    // Altri getters utili
  }
});