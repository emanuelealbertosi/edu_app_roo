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
        const rawData: any[] = await udaService.getUdas(filters); // Ricevi come any[]
        // Mappa i dati ricevuti all'interfaccia UDA, conservando i nuovi campi
        this.udas = rawData.map((udaData: any) => ({
          ...udaData, // Copia tutti i campi ricevuti
          course: udaData.course_id, // Salva l'ID del corso nel campo 'course'
          course_name: udaData.course_name, // Salva il nome del corso
          course_teacher_username: udaData.course_teacher_username, // Salva l'username dell'autore
          subjects: udaData.subject_ids || [], // Mappa subject_ids a subjects (per il form)
          topics: udaData.topic_ids || []      // Mappa topic_ids a topics (per il form)
        })) as UDA[]; // Asserisci il tipo finale a UDA[]
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
        const rawData: any = await udaService.getUda(udaId); // Ricevi come any

        // Mappa i contenuti esistenti, se presenti in rawData, per aggiungere uda_id
        let processedContents = rawData.contents;
        if (rawData.contents && Array.isArray(rawData.contents)) {
          processedContents = rawData.contents.map((content: any) => ({
            ...content,
            uda_id: udaId // Assicura che uda_id sia presente per ogni contenuto
          }));
        }

        // Mappa i dati ricevuti all'interfaccia UDA, conservando i nuovi campi
        this.currentUda = {
          ...rawData, // Copia tutti i campi ricevuti
          contents: processedContents, // Usa i contenuti processati (o originali se non c'erano)
          course: rawData.course_id, // Salva l'ID del corso nel campo 'course'
          course_name: rawData.course_name, // Salva il nome del corso
          course_teacher_username: rawData.course_teacher_username, // Salva l'username dell'autore
          subjects: rawData.subject_ids || [], // Mappa subject_ids a subjects (per il form)
          topics: rawData.topic_ids || []      // Mappa topic_ids a topics (per il form)
        } as UDA; // Asserisci il tipo finale a UDA
        
        // Se i contenuti non erano presenti in rawData o erano vuoti (anche dopo il tentativo di processarli),
        // fetchUdaContents li caricherà (e li processerà con uda_id grazie alla modifica precedente in fetchUdaContents)
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
        
        // Gestione di topics: se presente in udaData, lo processiamo.
        // Se udaData.topics è un array (anche vuoto), lo usiamo.
        // Se è un array di oggetti, mappiamo a ID.
        // Se è undefined, non lo includiamo nel payload per PATCH parziali.
        if (udaData.topics !== undefined) {
            if (Array.isArray(udaData.topics) && udaData.topics.length > 0 && typeof udaData.topics[0] === 'object' && udaData.topics[0] !== null && 'id' in udaData.topics[0]) {
                payload.topics = udaData.topics.map((t: any) => t.id);
            } else {
                payload.topics = udaData.topics; // Sarà un array di ID o un array vuoto
            }
        } else {
            delete payload.topics; // Assicurati che non venga inviato se non fornito
        }

        // Gestione di subject_ids: se presente in udaData, lo processiamo.
        // Se udaData.subject_ids è un array (anche vuoto), lo usiamo.
        // Se è undefined, non lo includiamo nel payload per PATCH parziali.
        if (udaData.subject_ids !== undefined) {
             if (!Array.isArray(udaData.subject_ids)) {
                console.warn('subject_ids is defined but not an array in updateUda, setting to empty array.');
                payload.subject_ids = [];
            } else {
                payload.subject_ids = udaData.subject_ids;
            }
        } else {
            delete payload.subject_ids; // Assicurati che non venga inviato se non fornito
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
            const contentsFromService = await udaService.getUdaContents(udaId);
            const contentsWithUdaId = contentsFromService.map(content => ({
                ...content,
                uda_id: udaId // Assicura che uda_id sia presente
            }));
            const sortedContents = contentsWithUdaId.sort((a, b) => a.order - b.order);
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

    // Aggiornata la firma per includere estimated_hours nel tipo contentData (tramite UDAContent)
    async addContentToUda(
      udaId: number,
      contentData: Partial<Omit<UDAContent, 'id' | 'uda_id' | 'created_at' | 'updated_at'>>,
      file?: File // Aggiunto parametro file opzionale
    ): Promise<UDAContent | undefined> {
      this.loading = true;
      this.error = null;
      try {
        // Passa il file al servizio se presente
        const newContentFromService = await udaService.addContentToUda(udaId, contentData, file);
        const newContent = {
            ...newContentFromService,
            uda_id: udaId // Assicura che uda_id sia presente
        };
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

    // Aggiornata la firma per includere estimated_hours nel tipo contentData (tramite UDAContent)
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
        const updatedContentFromService = await udaService.updateUdaContent(udaId, contentId, contentData, file);
        const updatedContent = {
            ...updatedContentFromService,
            uda_id: udaId // Assicura che uda_id sia presente
        };
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
    }, // <-- Aggiunta virgola qui
    async reorderUdaContents(udaId: number, contentIds: number[]): Promise<void> {
      // Ottimisticamente, potremmo aggiornare l'ordine locale prima della chiamata API,
      // ma per semplicità e consistenza, aggiorniamo dopo la risposta positiva.
      this.loading = true;
      this.error = null;
      try {
        const reorderedContents = await udaService.reorderUdaContents(udaId, contentIds);
        // Aggiorna i contenuti nell'UDA corrente se corrisponde
        if (this.currentUda?.id === udaId) {
          this.currentUda.contents = reorderedContents;
        }
        // Aggiorna anche i contenuti nell'array 'udas' se l'UDA è presente
        const udaInList = this.udas.find((u: UDA) => u.id === udaId);
        if (udaInList) {
          udaInList.contents = reorderedContents;
        }
      } catch (err) {
        this.error = (err as Error).message || `Failed to reorder contents for UDA ${udaId}`;
        console.error(err);
        // In caso di errore, potremmo voler ricaricare i contenuti originali
        // o notificare l'utente in modo più specifico.
        throw err; // Rilancia l'errore per gestirlo nel componente se necessario
      } finally {
        this.loading = false;
      }
    },
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