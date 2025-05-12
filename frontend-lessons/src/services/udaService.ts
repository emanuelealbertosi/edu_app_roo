import type { UDA, UDATemplate, UDAContent, UDATemplateContent } from '@/types/uda';
import apiClient from './apiClient';

const UDA_TEMPLATE_BASE_URL = '/uda/uda-templates';
const UDA_BASE_URL = '/uda/udas';

export const udaService = {
  // UDA Template Endpoints
  async getUdaTemplates(): Promise<UDATemplate[]> {
    const response = await apiClient.get(`${UDA_TEMPLATE_BASE_URL}/`);
    return response.data;
  },

  async getUdaTemplate(id: number): Promise<UDATemplate> {
    const response = await apiClient.get(`${UDA_TEMPLATE_BASE_URL}/${id}/`);
    return response.data;
  },

  async createUdaTemplate(templateData: Partial<UDATemplate>): Promise<UDATemplate> {
    const response = await apiClient.post(`${UDA_TEMPLATE_BASE_URL}/`, templateData);
    return response.data;
  },

  async updateUdaTemplate(id: number, templateData: Partial<UDATemplate>): Promise<UDATemplate> {
    const response = await apiClient.put(`${UDA_TEMPLATE_BASE_URL}/${id}/`, templateData);
    return response.data;
  },

  async deleteUdaTemplate(id: number): Promise<void> {
    await apiClient.delete(`${UDA_TEMPLATE_BASE_URL}/${id}/`);
  },

  async getUdaTemplateContents(templateId: number): Promise<UDATemplateContent[]> {
    const response = await apiClient.get(`${UDA_TEMPLATE_BASE_URL}/${templateId}/contents/`);
    return response.data;
  },

  async addContentToUdaTemplate(templateId: number, contentData: Partial<UDATemplateContent>): Promise<UDATemplateContent> {
    const response = await apiClient.post(`${UDA_TEMPLATE_BASE_URL}/${templateId}/contents/`, contentData);
    return response.data;
  },

  async updateUdaTemplateContent(templateId: number, contentId: number, contentData: Partial<UDATemplateContent>): Promise<UDATemplateContent> {
    const response = await apiClient.put(`${UDA_TEMPLATE_BASE_URL}/${templateId}/contents/${contentId}/`, contentData);
    return response.data;
  },

  async deleteUdaTemplateContent(templateId: number, contentId: number): Promise<void> {
    await apiClient.delete(`${UDA_TEMPLATE_BASE_URL}/${templateId}/contents/${contentId}/`);
  },

  // UDA Endpoints
  async getUdas(params?: { status?: string; courseId?: number }): Promise<UDA[]> {
    const response = await apiClient.get(`${UDA_BASE_URL}/`, { params });
    return response.data;
  },

  async getUda(id: number): Promise<UDA> {
    const response = await apiClient.get(`${UDA_BASE_URL}/${id}/`);
    return response.data;
  },

  async createUda(udaData: Partial<UDA>): Promise<UDA> {
    // Includere courseId e orderInCourse se presenti in udaData
    const response = await apiClient.post(`${UDA_BASE_URL}/`, udaData);
    return response.data;
  },

  async updateUda(id: number, udaData: Partial<UDA>): Promise<UDA> {
    // CORRETTO: Usare PATCH per aggiornamenti parziali
    const response = await apiClient.patch(`${UDA_BASE_URL}/${id}/`, udaData);
    return response.data;
  },

  async deleteUda(id: number): Promise<void> {
    await apiClient.delete(`${UDA_BASE_URL}/${id}/`);
  },

  async getUdaContents(udaId: number): Promise<UDAContent[]> {
    const response = await apiClient.get(`${UDA_BASE_URL}/${udaId}/contents/`);
    return response.data;
  },

  async addContentToUda(udaId: number, contentData: Partial<UDAContent>, file?: File): Promise<UDAContent> {
    let dataToSend: any = contentData;
    let headers = {};

    if (file) {
      const formData = new FormData();
      Object.keys(contentData).forEach(key => {
        const value = (contentData as any)[key];
        if (value !== null && value !== undefined) {
          if (typeof value === 'boolean') {
            formData.append(key, value ? 'true' : 'false');
          } else {
            formData.append(key, value as string);
          }
        }
      });
      formData.append('activity_attachment_url', file, file.name);
      dataToSend = formData;
      headers = { 'Content-Type': 'multipart/form-data' };
    }

    const response = await apiClient.post(`${UDA_BASE_URL}/${udaId}/contents/`, dataToSend, { headers });
    return response.data;
  },

  async updateUdaContent(udaId: number, contentId: number, contentData: Partial<UDAContent>, file?: File): Promise<UDAContent> {
    let dataToSend: any = contentData;
    let headers = {};

    if (file) {
      const formData = new FormData();
      // Aggiungi i campi di contentData al FormData
      // Nota: i campi booleani e null potrebbero necessitare di una gestione speciale
      // o essere omessi se il backend li gestisce correttamente con FormData.
      // Per i FileField, il backend si aspetta il file stesso.
      // Per altri campi, li inviamo come stringhe o il backend deve essere in grado di parsarli.
      Object.keys(contentData).forEach(key => {
        const value = (contentData as any)[key];
        if (value !== null && value !== undefined) {
          if (typeof value === 'boolean') {
            formData.append(key, value ? 'true' : 'false');
          } else if (value instanceof File) {
            // Questo caso non dovrebbe accadere se il file è passato separatamente
            // ma lo gestiamo per robustezza se contentData contenesse un file.
            formData.append(key, value, value.name);
          } else if (typeof value === 'object' && !(value instanceof Date)) {
             // Non inviare oggetti complessi direttamente in FormData a meno che il backend non sia configurato per gestirli (es. JSON stringato)
             // Per ora, omettiamo o stringifichiamo. Per UDAContent, i campi sono principalmente primitivi o FK.
             // Se ci sono campi JSON, andrebbero stringati: formData.append(key, JSON.stringify(value));
          }
          else {
            formData.append(key, value as string); // Assumiamo stringhe o valori convertibili
          }
        }
      });
      
      // Il nome del campo per il file deve corrispondere a quello atteso dal serializer Django per il FileField
      // Spesso è il nome del campo stesso, es. 'activity_attachment_url'
      formData.append('activity_attachment_url', file, file.name);
      
      dataToSend = formData;
      headers = { 'Content-Type': 'multipart/form-data' };
    }

    const response = await apiClient.put(`${UDA_BASE_URL}/${udaId}/contents/${contentId}/`, dataToSend, { headers });
    return response.data;
  },

  async deleteUdaContent(udaId: number, contentId: number): Promise<void> {
    await apiClient.delete(`${UDA_BASE_URL}/${udaId}/contents/${contentId}/`);
  },

  async updateUdaContentTeacherCompletion(udaId: number, contentId: number, completed: boolean): Promise<UDAContent> {
    const response = await apiClient.patch(`${UDA_BASE_URL}/${udaId}/contents/${contentId}/update-teacher-completion/`, { completed });
    return response.data;
  },

  async completeActivityInUda(udaId: number, contentId: number, completed: boolean): Promise<UDAContent> {
    // L'endpoint nel backend è /complete-activity/, ma il piano FE diceva completeActivityInUda
    // Assumiamo che l'endpoint corretto sia quello del backend
    const response = await apiClient.patch(`${UDA_BASE_URL}/${udaId}/contents/${contentId}/complete-activity/`, { completed });
    return response.data;
  },

async reorderUdaContents(udaId: number, contentIds: number[]): Promise<UDAContent[]> {
    const response = await apiClient.post(`${UDA_BASE_URL}/${udaId}/contents/reorder/`, { content_ids: contentIds });
    return response.data; // L'API restituisce i contenuti riordinati
  },
  // La funzione uploadActivityAttachment è stata integrata in updateUdaContent
};