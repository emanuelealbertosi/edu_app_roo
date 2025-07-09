import type { CourseGroup } from '@/types/uda';
import apiClient from './apiClient';

const BASE_URL = '/uda/course-groups/';

export const courseGroupService = {
  async getCourseGroups(): Promise<CourseGroup[]> {
    const response = await apiClient.get(BASE_URL);
    return response.data;
  },

  async createCourseGroup(groupData: Pick<CourseGroup, 'name'>): Promise<CourseGroup> {
    const response = await apiClient.post(BASE_URL, groupData);
    return response.data;
  },

  async updateCourseGroup(id: number, groupData: Pick<CourseGroup, 'name'>): Promise<CourseGroup> {
    const response = await apiClient.put(`${BASE_URL}${id}/`, groupData);
    return response.data;
  },

  async deleteCourseGroup(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}${id}/`);
  },
};