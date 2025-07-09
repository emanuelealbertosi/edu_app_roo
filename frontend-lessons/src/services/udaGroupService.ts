import type { UdaGroup } from '@/types/uda';
import apiClient from './apiClient';

const BASE_URL = '/uda/uda-groups/';

export const udaGroupService = {
  async getUdaGroups(): Promise<UdaGroup[]> {
    const response = await apiClient.get(BASE_URL);
    return response.data;
  },

  async createUdaGroup(groupData: Pick<UdaGroup, 'name'>): Promise<UdaGroup> {
    const response = await apiClient.post(BASE_URL, groupData);
    return response.data;
  },

  async updateUdaGroup(id: number, groupData: Pick<UdaGroup, 'name'>): Promise<UdaGroup> {
    const response = await apiClient.put(`${BASE_URL}${id}/`, groupData);
    return response.data;
  },

  async deleteUdaGroup(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}${id}/`);
  },
};