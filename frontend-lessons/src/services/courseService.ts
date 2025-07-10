import type { Course, UDA, CourseGroup } from '@/types/uda'; // Assumendo che i tipi siano definiti qui
import apiClient from './apiClient'; // Assumendo un client API configurato

const BASE_URL = '/uda/courses/';
const GROUP_BASE_URL = '/uda/course-groups/';

export const courseService = {
  // Course Group Methods
  async getCourseGroups(): Promise<CourseGroup[]> {
    const response = await apiClient.get(GROUP_BASE_URL);
    return response.data;
  },

  async createCourseGroup(groupData: { name: string }): Promise<CourseGroup> {
    const response = await apiClient.post(GROUP_BASE_URL, groupData);
    return response.data;
  },

  async updateCourseGroup(id: number, groupData: { name: string }): Promise<CourseGroup> {
    const response = await apiClient.put(`${GROUP_BASE_URL}${id}/`, groupData);
    return response.data;
  },

  async deleteCourseGroup(id: number): Promise<void> {
    await apiClient.delete(`${GROUP_BASE_URL}${id}/`);
  },

  // Course Methods
  async getCourses(): Promise<Course[]> {
    const response = await apiClient.get(BASE_URL);
    return response.data;
  },

  async getCourse(id: number): Promise<Course> {
    const response = await apiClient.get(`${BASE_URL}${id}`);
    return response.data;
  },

  async createCourse(courseData: Partial<Course>): Promise<Course> {
    const response = await apiClient.post(BASE_URL, courseData);
    return response.data;
  },

  async updateCourse(id: number, courseData: Partial<Course>): Promise<Course> {
    const response = await apiClient.patch(`${BASE_URL}${id}/`, courseData);
    return response.data;
  },

  async deleteCourse(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}${id}/`);
  },

  async getUdasForCourse(courseId: number): Promise<UDA[]> {
    const response = await apiClient.get(`${BASE_URL}${courseId}/udas/`);
    return response.data;
  },

  async reorderUdasInCourse(courseId: number, udaIds: number[]): Promise<void> {
    await apiClient.post(`${BASE_URL}${courseId}/udas/reorder/`, { uda_ids: udaIds });
  },

  async copyCourse(courseId: number): Promise<Course> {
    const response = await apiClient.post(`${BASE_URL}${courseId}/copy/`);
    return response.data;
  },

  async exportUdas(courseId: number, format: 'docx' | 'pdf'): Promise<void> {
    try {
      // L'URL del backend è ora separato per docx e pdf
      let apiUrl = `${BASE_URL}${courseId}/`;
      if (format === 'docx') {
        apiUrl += 'export-udas-docx/';
      } else if (format === 'pdf') {
        apiUrl += 'export-udas-pdf/';
      } else {
        // Gestione di un formato non supportato, se necessario
        console.error(`Formato di esportazione non supportato: ${format}`);
        throw new Error(`Formato di esportazione non supportato: ${format}`);
      }

      const response = await apiClient.get(apiUrl, {
        responseType: 'blob', // Importante per ricevere il file come Blob
      });
      
      // Determina il tipo di contenuto corretto per il Blob
      let blobType = 'application/octet-stream'; // Default generico
      if (format === 'docx') {
        blobType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
      } else if (format === 'pdf') {
        blobType = 'application/pdf';
      }

      const url = window.URL.createObjectURL(new Blob([response.data], { type: blobType }));
      const link = document.createElement('a');
      link.href = url;
      
      const contentDisposition = response.headers['content-disposition'];
      let filename = `export_udas_corso_${courseId}.${format}`; // Default filename dinamico
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch && filenameMatch.length > 1) {
          filename = filenameMatch[1];
        }
      }
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(`Error downloading ${format.toUpperCase()} file:`, error);
      throw error;
    }
  }
};