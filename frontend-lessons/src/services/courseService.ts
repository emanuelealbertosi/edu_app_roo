import type { Course, UDA } from '@/types/uda'; // Assumendo che i tipi siano definiti qui
import apiClient from './apiClient'; // Assumendo un client API configurato

const BASE_URL = '/uda/courses/';

export const courseService = {
  async getCourses(): Promise<Course[]> {
    const response = await apiClient.get(BASE_URL);
    return response.data;
  },

  async getCourse(id: number): Promise<Course> {
    const response = await apiClient.get(`${BASE_URL}/${id}`);
    return response.data;
  },

  async createCourse(courseData: Partial<Course>): Promise<Course> {
    const response = await apiClient.post(BASE_URL, courseData);
    return response.data;
  },

  async updateCourse(id: number, courseData: Partial<Course>): Promise<Course> {
    const response = await apiClient.put(`${BASE_URL}/${id}`, courseData);
    return response.data;
  },

  async deleteCourse(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}${id}/`);
  },

  async getUdasForCourse(courseId: number): Promise<UDA[]> {
    const response = await apiClient.get(`${BASE_URL}/${courseId}/udas/`);
    return response.data;
  },

  async reorderUdasInCourse(courseId: number, udaIds: number[]): Promise<void> {
    await apiClient.post(`${BASE_URL}/${courseId}/udas/reorder/`, { uda_ids: udaIds });
  }
};