import type { UDA, UDATemplate, UDAContent, UDATemplateContent, UdaGroup } from '@/types/uda';
import apiClient from './apiClient';

const UDA_TEMPLATE_BASE_URL = '/uda/uda-templates';
const UDA_BASE_URL = '/uda/udas';
const UDA_GROUP_BASE_URL = '/uda/uda-groups/';

export const udaService = {
  // UDA Group Methods
  async getUdaGroups(): Promise<UdaGroup[]> {
    const response = await apiClient.get(UDA_GROUP_BASE_URL);
    return response.data;
  },

  async createUdaGroup(groupData: { name: string }): Promise<UdaGroup> {
    const response = await apiClient.post(UDA_GROUP_BASE_URL, groupData);
    return response.data;
  },

  async updateUdaGroup(id: number, groupData: { name: string }): Promise<UdaGroup> {
    const response = await apiClient.put(`${UDA_GROUP_BASE_URL}${id}/`, groupData);
    return response.data;
  },

  async deleteUdaGroup(id: number): Promise<void> {
    await apiClient.delete(`${UDA_GROUP_BASE_URL}${id}/`);
  },

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

  async copyUda(udaIdToCopy: number): Promise<UDA> {
    const response = await apiClient.post(`${UDA_BASE_URL}/${udaIdToCopy}/copy/`);
    return response.data;
  },

  async getUdaContents(udaId: number): Promise<UDAContent[]> {
    const response = await apiClient.get(`${UDA_BASE_URL}/${udaId}/contents/`);
    return response.data;
  },

  async addContentToUda(udaId: number, contentData: Partial<UDAContent>): Promise<UDAContent> {
    const response = await apiClient.post(`${UDA_BASE_URL}/${udaId}/contents/`, contentData);
    return response.data;
  },

  async updateUdaContent(udaId: number, contentId: number, contentData: Partial<UDAContent>): Promise<UDAContent> {
    const response = await apiClient.patch(`${UDA_BASE_URL}/${udaId}/contents/${contentId}/`, contentData);
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