import { defineStore } from 'pinia';
import { udaService } from '@/services/udaService';
import type { UDA, UDAContent, UdaGroup } from '@/types/uda';

export const useUdaStore = defineStore('uda', {
  state: () => ({
    udas: [] as UDA[],
    udaGroups: [] as UdaGroup[],
    currentUda: null as UDA | null,
    loading: false,
    isLoadingUdaGroups: false,
    error: null as string | null,
  }),
  actions: {
    // GROUP ACTIONS
    async fetchUdaGroups() {
      this.isLoadingUdaGroups = true;
      this.error = null;
      try {
        this.udaGroups = await udaService.getUdaGroups();
      } catch (err) {
        this.error = (err as Error).message || 'Failed to fetch UDA groups';
        this.udaGroups = [];
      } finally {
        this.isLoadingUdaGroups = false;
      }
    },

    async createUdaGroup(name: string): Promise<UdaGroup | undefined> {
      this.isLoadingUdaGroups = true;
      try {
        const newGroup = await udaService.createUdaGroup({ name });
        this.udaGroups.push(newGroup);
        return newGroup;
      } catch (error) {
        this.error = (error as Error).message || 'Failed to create UDA group';
        throw error;
      } finally {
        this.isLoadingUdaGroups = false;
      }
    },

    async updateUdaGroup(id: number, name: string): Promise<UdaGroup | undefined> {
        this.isLoadingUdaGroups = true;
        try {
            const updatedGroup = await udaService.updateUdaGroup(id, { name });
            const index = this.udaGroups.findIndex(g => g.id === id);
            if (index !== -1) {
                this.udaGroups[index] = updatedGroup;
            }
            this.udas.forEach(uda => {
                if (uda.group?.id === id) {
                    uda.group = updatedGroup;
                }
            });
            return updatedGroup;
        } catch (error) {
            this.error = (error as Error).message || 'Failed to update UDA group';
            throw error;
        } finally {
            this.isLoadingUdaGroups = false;
        }
    },

    async deleteUdaGroup(id: number) {
      this.isLoadingUdaGroups = true;
      try {
        await udaService.deleteUdaGroup(id);
        this.udaGroups = this.udaGroups.filter(g => g.id !== id);
        this.udas.forEach(uda => {
          if (uda.group?.id === id) {
            uda.group = null;
            uda.group_id = null;
          }
        });
      } catch (error) {
        this.error = (error as Error).message || 'Failed to delete UDA group';
        throw error;
      } finally {
        this.isLoadingUdaGroups = false;
      }
    },

    async assignUdasToGroup(udaIds: number[], groupId: number | null) {
        this.loading = true;
        try {
            const group = this.udaGroups.find(g => g.id === groupId) || null;
            this.udas.forEach(uda => {
                if (udaIds.includes(uda.id)) {
                    uda.group = group;
                    uda.group_id = groupId;
                }
            });
            const updatePromises = udaIds.map(udaId =>
                udaService.updateUda(udaId, { group_id: groupId })
            );
            await Promise.all(updatePromises);
        } catch (error) {
            this.error = (error as Error).message || 'Failed to assign UDAs to group';
            await this.fetchUdas(); // Rollback
            throw error;
        } finally {
            this.loading = false;
        }
    },

    async removeUdaFromGroup(udaId: number) {
        this.loading = true;
        try {
            const uda = this.udas.find(u => u.id === udaId);
            if (uda) {
                uda.group = null;
                uda.group_id = null;
            }
            await udaService.updateUda(udaId, { group_id: null });
        } catch (error) {
            this.error = (error as Error).message || 'Failed to remove UDA from group';
            await this.fetchUdas(); // Rollback
            throw error;
        } finally {
            this.loading = false;
        }
    },

    async removeUdasFromGroup(udaIds: number[]) {
        this.loading = true;
        try {
            // Ottimisticamente
            this.udas.forEach(uda => {
                if (udaIds.includes(uda.id)) {
                    uda.group = null;
                    uda.group_id = null;
                }
            });
            const updatePromises = udaIds.map(udaId =>
                udaService.updateUda(udaId, { group_id: null })
            );
            await Promise.all(updatePromises);
        } catch (error) {
            this.error = (error as Error).message || 'Failed to remove UDAs from group';
            await this.fetchUdas(); // Rollback
            throw error;
        } finally {
            this.loading = false;
        }
    },

    // UDA ACTIONS
    async fetchUdas(filters?: { status?: 'TODO' | 'IN_PROGRESS' | 'COMPLETED', courseId?: number }) {
      this.loading = true;
      this.error = null;
      try {
        const rawData: any[] = await udaService.getUdas(filters); // Ricevi come any[]
        // Mappa i dati ricevuti all'interfaccia UDA, conservando i nuovi campi
        // inclusi knowledge_html, skills_html, competences_html se presenti dal backend.
        this.udas = rawData.map((udaData: any) => ({
          ...udaData, // Copia tutti i campi ricevuti
          course: udaData.course?.id ?? udaData.course_id,
          course_name: udaData.course?.name ?? udaData.course_name,
          course_teacher_username: udaData.course?.teacher_username ?? udaData.course_teacher_username,
          subjects: (udaData.subjects?.map((s: any) => s.id) ?? udaData.subject_ids) || [],
          topics: (udaData.topics?.map((t: any) => t.id) ?? udaData.topic_ids) || [],
          // Campi per Export DOCX
          is_civic_education: udaData.is_civic_education,
          didactic_strategies_html: udaData.didactic_strategies_html,
          materials_tools_html: udaData.materials_tools_html,
          assessment_type_html: udaData.assessment_type_html,
          evaluation_html: udaData.evaluation_html,
          other_involved_subjects_text: udaData.other_involved_subjects_text,
          export_specific_annotations_html: udaData.export_specific_annotations_html,
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
        // inclusi knowledge_html, skills_html, competences_html se presenti dal backend.
        this.currentUda = {
          ...rawData, // Copia tutti i campi ricevuti
          contents: processedContents, // Usa i contenuti processati (o originali se non c'erano)
          course: rawData.course?.id ?? rawData.course_id,
          course_name: rawData.course?.name ?? rawData.course_name,
          course_teacher_username: rawData.course?.teacher_username ?? rawData.course_teacher_username,
          subjects: (rawData.subjects?.map((s: any) => s.id) ?? rawData.subject_ids) || [],
          topics: (rawData.topics?.map((t: any) => t.id) ?? rawData.topic_ids) || [],
          // Campi per Export DOCX
          is_civic_education: rawData.is_civic_education,
          didactic_strategies_html: rawData.didactic_strategies_html,
          materials_tools_html: rawData.materials_tools_html,
          assessment_type_html: rawData.assessment_type_html,
          evaluation_html: rawData.evaluation_html,
          other_involved_subjects_text: rawData.other_involved_subjects_text,
          export_specific_annotations_html: rawData.export_specific_annotations_html,
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

    async createUda(udaData: Partial<Omit<UDA, 'id' | 'teacher' | 'created_at' | 'updated_at' | 'contents' | 'topics' | 'subject' | 'subjects' | 'course' >> & { topics?: number[], subject_ids?: number[], course_id?: number | null, order_in_course?: number | null, knowledge_html?: string | null, skills_html?: string | null, competences_html?: string | null, is_civic_education?: boolean, didactic_strategies_html?: string | null, materials_tools_html?: string | null, assessment_type_html?: string | null, evaluation_html?: string | null, other_involved_subjects_text?: string | null, export_specific_annotations_html?: string | null }) : Promise<UDA | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const payload = { ...udaData } as any; // Usiamo 'any' temporaneamente per flessibilità
        // La logica di conversione del payload è stata rimossa.
        // Il componente del form (UdaFormView) ora invia direttamente i campi corretti per l'API
        // (es. 'subject_ids', 'course_id').

        // Se stiamo creando da un template, il backend gestirà la copia dei contenuti.
        // Rimuoviamo 'contents' dal payload per evitare conflitti o sovrascritture.
        if (payload.source_template_id) {
          delete payload.contents;
        }

        const newUda = await udaService.createUda(payload);
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

    async updateUda(
      udaId: number,
      udaData: Partial<Omit<UDA, 'id' | 'teacher' | 'created_at' | 'updated_at' | 'contents' | 'topics' | 'subject' | 'subjects' | 'course'>> & { group_id?: number | null, topics?: number[], subject_ids?: number[], course_id?: number | null, knowledge_html?: string | null, skills_html?: string | null, competences_html?: string | null, is_civic_education?: boolean, didactic_strategies_html?: string | null, materials_tools_html?: string | null, assessment_type_html?: string | null, evaluation_html?: string | null, other_involved_subjects_text?: string | null, export_specific_annotations_html?: string | null },
      options: { silent?: boolean } = {}
    ): Promise<UDA | undefined> {
      if (!options.silent) {
        this.loading = true;
      }
      this.error = null;
      try {
        const payload = { ...udaData } as any; // Usiamo 'any' temporaneamente
        
        // La logica di conversione del payload è stata rimossa.
        // Il componente del form (UdaFormView) ora invia direttamente i campi corretti per l'API.
        const updatedUda = await udaService.updateUda(udaId, payload);
        
        if (!options.silent) {
          const index = this.udas.findIndex((u: UDA) => u.id === udaId);
          if (index !== -1) {
            this.udas[index] = updatedUda;
          }
          if (this.currentUda?.id === udaId) {
            this.currentUda = updatedUda;
          }
        }
        
        return updatedUda;
      } catch (err) {
        this.error = (err as Error).message || `Failed to update UDA ${udaId}`;
        console.error(err);
        throw err;
      } finally {
        if (!options.silent) {
          this.loading = false;
        }
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
      contentData: Partial<Omit<UDAContent, 'id' | 'uda_id' | 'created_at' | 'updated_at'>>
    ): Promise<UDAContent | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const newContentFromService = await udaService.addContentToUda(udaId, contentData);
        console.log('[udaStore.addContentToUda] newContentFromService:', JSON.parse(JSON.stringify(newContentFromService))); // LOG 1
        const newContent = {
            ...newContentFromService,
            uda_id: udaId // Assicura che uda_id sia presente
        };
        console.log('[udaStore.addContentToUda] newContent after adding uda_id:', JSON.parse(JSON.stringify(newContent))); // LOG 2
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
      contentData: Partial<Omit<UDAContent, 'id' | 'uda_id' | 'created_at' | 'updated_at'>>
    ): Promise<UDAContent | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const updatedContentFromService = await udaService.updateUdaContent(udaId, contentId, contentData);
        console.log('[udaStore.updateContentInUda] updatedContentFromService:', JSON.parse(JSON.stringify(updatedContentFromService))); // LOG 3
        const updatedContent = {
            ...updatedContentFromService,
            uda_id: udaId // Assicura che uda_id sia presente
        };
        console.log('[udaStore.updateContentInUda] updatedContent after adding uda_id:', JSON.parse(JSON.stringify(updatedContent))); // LOG 4
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
        await udaService.reorderUdaContents(udaId, contentIds);
        // Dopo aver riordinato, ricarica i dati dell'UDA per assicurarti che lo stato sia consistente
        // e che tutti i dati arricchiti (es. titoli delle lezioni) siano presenti.
        // Questo risolve il problema di visualizzazione in UdaDetailView.
        await this.fetchUda(udaId);
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

    async copyUda(udaIdToCopy: number): Promise<UDA | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const newUda = await udaService.copyUda(udaIdToCopy);
        // Aggiungi la nuova UDA alla lista (potrebbe essere necessario un fetchUdas per aggiornare completamente se l'ordinamento è importante qui)
        // O, se la risposta include l'UDA completa, possiamo aggiungerla direttamente.
        // Per ora, assumiamo che il servizio restituisca l'UDA copiata.
        this.udas.push(newUda);
        // Potremmo voler impostare la nuova UDA come currentUda se l'utente viene reindirizzato alla sua modifica
        // this.currentUda = newUda;
        return newUda;
      } catch (err) {
        this.error = (err as Error).message || `Failed to copy UDA ${udaIdToCopy}`;
        console.error(err);
        throw err;
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