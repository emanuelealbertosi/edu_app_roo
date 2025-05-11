import { defineStore } from 'pinia';
import { udaService } from '@/services/udaService'; // Assumiamo che udaService gestisca anche i template
import type { UDATemplate, UDATemplateContent } from '@/types/uda';

export const useUdaTemplateStore = defineStore('udaTemplate', {
  state: () => ({
    udaTemplates: [] as UDATemplate[],
    currentUdaTemplate: null as UDATemplate | null,
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchUdaTemplates() {
      this.loading = true;
      this.error = null;
      try {
        const data = await udaService.getUdaTemplates();
        this.udaTemplates = data;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to fetch UDA templates';
        this.udaTemplates = [];
        console.error(err);
      } finally {
        this.loading = false;
      }
    },

    async fetchUdaTemplate(templateId: number) {
      this.loading = true;
      this.error = null;
      try {
        const data = await udaService.getUdaTemplate(templateId);
        this.currentUdaTemplate = data;
        // Carica i contenuti se non sono già presenti o sono vuoti
         if (this.currentUdaTemplate && (!this.currentUdaTemplate.contents || this.currentUdaTemplate.contents.length === 0)) {
           await this.fetchUdaTemplateContents(templateId);
        }
      } catch (err) {
        this.error = (err as Error).message || `Failed to fetch UDA template ${templateId}`;
        this.currentUdaTemplate = null;
        console.error(err);
      } finally {
        this.loading = false;
      }
    },

    async createUdaTemplate(templateData: Partial<Omit<UDATemplate, 'id' | 'teacher' | 'created_at' | 'updated_at' | 'contents'>> & { name: string, description?: string | null, subject_id?: number | null, topic_ids?: number[], contents: Omit<UDATemplateContent, 'temp_id'>[] }): Promise<UDATemplate | undefined> {
      this.loading = true;
      this.error = null;
      try {
        // Il payload viene passato direttamente al servizio, che dovrebbe aspettarsi subject_id e topic_ids
        const newTemplate = await udaService.createUdaTemplate(templateData); // templateData è già del tipo corretto per il servizio
        this.udaTemplates.push(newTemplate);
        // this.currentUdaTemplate = newTemplate; // Opzionale
        return newTemplate;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to create UDA template';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async updateUdaTemplate(templateId: number, templateData: Partial<Omit<UDATemplate, 'id' | 'teacher' | 'created_at' | 'updated_at' | 'contents'>> & { name?: string, description?: string | null, subject_id?: number | null, topic_ids?: number[], contents?: Omit<UDATemplateContent, 'temp_id'>[] }): Promise<UDATemplate | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const updatedTemplate = await udaService.updateUdaTemplate(templateId, templateData);
        const index = this.udaTemplates.findIndex((t: UDATemplate) => t.id === templateId);
        if (index !== -1) {
          this.udaTemplates[index] = updatedTemplate;
        }
        if (this.currentUdaTemplate?.id === templateId) {
          this.currentUdaTemplate = updatedTemplate;
        }
        return updatedTemplate;
      } catch (err) {
        this.error = (err as Error).message || `Failed to update UDA template ${templateId}`;
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async deleteUdaTemplate(templateId: number) {
      this.loading = true;
      this.error = null;
      try {
        await udaService.deleteUdaTemplate(templateId);
        this.udaTemplates = this.udaTemplates.filter((t: UDATemplate) => t.id !== templateId);
        if (this.currentUdaTemplate?.id === templateId) {
          this.currentUdaTemplate = null;
        }
      } catch (err) {
        this.error = (err as Error).message || `Failed to delete UDA template ${templateId}`;
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async fetchUdaTemplateContents(templateId: number): Promise<UDATemplateContent[]> {
        this.loading = true;
        this.error = null;
        try {
            const contents = await udaService.getUdaTemplateContents(templateId);
            const sortedContents = contents.sort((a,b) => a.order - b.order);
            if (this.currentUdaTemplate?.id === templateId) {
                this.currentUdaTemplate.contents = sortedContents;
            }
            const templateInList = this.udaTemplates.find((t: UDATemplate) => t.id === templateId);
            if (templateInList) {
                templateInList.contents = sortedContents;
            }
            return sortedContents;
        } catch (err) {
            this.error = (err as Error).message || `Failed to fetch contents for UDA Template ${templateId}`;
            console.error(err);
            if (this.currentUdaTemplate?.id === templateId) this.currentUdaTemplate.contents = [];
            const templateInList = this.udaTemplates.find((t: UDATemplate) => t.id === templateId);
            if (templateInList) templateInList.contents = [];
            return [];
        } finally {
            this.loading = false;
        }
    },

    async addContentToTemplate(templateId: number, contentData: Partial<Omit<UDATemplateContent, 'id' | 'uda_template_id' | 'created_at' | 'updated_at'>>): Promise<UDATemplateContent | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const newContent = await udaService.addContentToUdaTemplate(templateId, contentData);
        const updateAndSortContents = (contentsArray?: UDATemplateContent[]) => {
            if(!contentsArray) contentsArray = [];
            contentsArray.push(newContent);
            contentsArray.sort((a,b) => a.order - b.order);
            return contentsArray;
        };
        if (this.currentUdaTemplate?.id === templateId) {
            this.currentUdaTemplate.contents = updateAndSortContents(this.currentUdaTemplate.contents);
        }
        const templateInList = this.udaTemplates.find((t: UDATemplate) => t.id === templateId);
        if (templateInList) {
            templateInList.contents = updateAndSortContents(templateInList.contents);
        }
        return newContent;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to add content to UDA template';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async updateContentInTemplate(templateId: number, contentId: number, contentData: Partial<Omit<UDATemplateContent, 'id' | 'uda_template_id' | 'created_at' | 'updated_at'>>): Promise<UDATemplateContent | undefined> {
      this.loading = true;
      this.error = null;
      try {
        const updatedContent = await udaService.updateUdaTemplateContent(templateId, contentId, contentData);
        const updateLocalContents = (contentsArray?: UDATemplateContent[]) => {
            if (!contentsArray) return;
            const contentIndex = contentsArray.findIndex(c => c.id === contentId);
            if (contentIndex !== -1) {
                contentsArray[contentIndex] = updatedContent;
                contentsArray.sort((a,b) => a.order - b.order);
            }
        };
        if (this.currentUdaTemplate?.id === templateId) {
            updateLocalContents(this.currentUdaTemplate.contents);
        }
        const templateInList = this.udaTemplates.find((t: UDATemplate) => t.id === templateId);
        if (templateInList) {
            updateLocalContents(templateInList.contents);
        }
        return updatedContent;
      } catch (err) {
        this.error = (err as Error).message || 'Failed to update content in UDA template';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    async removeContentFromTemplate(templateId: number, contentId: number) {
      this.loading = true;
      this.error = null;
      try {
        await udaService.deleteUdaTemplateContent(templateId, contentId);
        const filterLocalContents = (contentsArray?: UDATemplateContent[]): UDATemplateContent[] => {
            return contentsArray?.filter(c => c.id !== contentId) || [];
        };
        if (this.currentUdaTemplate?.id === templateId) {
          this.currentUdaTemplate.contents = filterLocalContents(this.currentUdaTemplate.contents);
        }
        const templateInList = this.udaTemplates.find((t: UDATemplate) => t.id === templateId);
        if (templateInList) {
            templateInList.contents = filterLocalContents(templateInList.contents);
        }
      } catch (err) {
        this.error = (err as Error).message || 'Failed to remove content from UDA template';
        console.error(err);
        throw err;
      } finally {
        this.loading = false;
      }
    },
  },
  getters: {
    getUdaTemplateById: (state) => (id: number): UDATemplate | undefined => {
      return state.udaTemplates.find((template: UDATemplate) => template.id === id);
    },
    getContentsForCurrentUdaTemplate: (state): UDATemplateContent[] => {
      return state.currentUdaTemplate?.contents || [];
    },
    // Altri getters utili
  }
});