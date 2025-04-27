// frontend-teacher/src/stores/groups.ts
import { defineStore } from 'pinia';
import type { StudentGroup, GroupMember, StudentGroupData, AddStudentToGroupData } from '@/types/groups';
// Import API functions
import * as groupApi from '@/api/groups';

interface GroupState {
  groups: StudentGroup[];
  currentGroup: StudentGroup | null;
  currentGroupMembers: GroupMember[];
  isLoadingList: boolean;
  isLoadingDetail: boolean; // For group details and members
  error: string | null;
}

export const useGroupStore = defineStore('groups', {
  state: (): GroupState => ({
    groups: [],
    currentGroup: null,
    currentGroupMembers: [],
    isLoadingList: false,
    isLoadingDetail: false,
    error: null,
  }),

  actions: {
    clearError() {
      this.error = null;
    },

    clearCurrentGroup() {
        this.currentGroup = null;
        this.currentGroupMembers = [];
        this.isLoadingDetail = false; // Reset loading state as well
        this.error = null; // Clear errors related to the specific group
    },

    // --- Group List ---
    async fetchGroups() {
      this.isLoadingList = true;
      this.error = null;
      try {
        const response = await groupApi.getGroups();
        this.groups = response.data;
      } catch (err: any) {
        this.error = err.response?.data?.detail || err.message || 'Errore nel caricamento dei gruppi.';
        this.groups = []; // Clear groups on error
      } finally {
        this.isLoadingList = false;
      }
    },

    // --- Single Group CRUD ---
    async fetchGroupDetails(groupId: number) {
        this.isLoadingDetail = true;
        this.error = null;
        this.currentGroup = null; // Clear previous group details
        this.currentGroupMembers = [];
        try {
            const response = await groupApi.getGroup(groupId);
            this.currentGroup = response.data;

            // Optionally fetch members immediately after fetching details, or handle it in the component
            // await this.fetchGroupMembers(groupId); // Decide if this should be automatic
        } catch (err: any) {
            this.error = err.response?.data?.detail || err.message || 'Errore nel caricamento dei dettagli del gruppo.';
            this.currentGroup = null;
        } finally {
            // isLoadingDetail might be set to false after members are fetched if called sequentially
            // For now, set it here. Adjust if fetchGroupMembers is called separately.
            // Set loading to false only if not fetching members sequentially
            this.isLoadingDetail = false;
        }
    },

    async createGroup(groupData: StudentGroupData) {
        this.isLoadingList = true; // Indicate loading on the list view
        this.error = null;
        try {
            const response = await groupApi.createGroup(groupData);
            const newGroup = response.data;
            // Add locally or re-fetch the list for consistency
            // this.groups.push(newGroup); // Add locally (might lack some fields like student_count)
            await this.fetchGroups(); // Re-fetch is safer for consistency
        } catch (err: any) {
            const errorData = err.response?.data;
            // Imposta l'errore generico nello store solo se non è un errore di validazione specifico per campo
            // (cioè, se errorData non è un oggetto o contiene solo 'detail')
            if (typeof errorData !== 'object' || !errorData || Object.keys(errorData).length === 0 || (Object.keys(errorData).length === 1 && errorData.detail)) {
                this.error = errorData?.detail || err.message || 'Errore nella creazione del gruppo.';
            }
            // Rethrow or handle specific validation errors if needed
            throw err; // Propagate error for form handling in the component
        } finally {
            this.isLoadingList = false;
        }
    },

    async updateGroup(groupId: number, groupData: Partial<StudentGroupData>) {
        // Indicate loading either on list or detail view depending on context
        this.isLoadingDetail = true; // Assume update happens in detail view
        this.error = null;
        try {
            const response = await groupApi.updateGroup(groupId, groupData);
            const updatedGroup = response.data;

            // Update local state for immediate feedback
            const index = this.groups.findIndex(g => g.id === groupId);
            if (index !== -1) {
                // Merge updates, ensuring all fields from response are included
                this.groups[index] = { ...this.groups[index], ...updatedGroup };
            }
            if (this.currentGroup?.id === groupId) {
                this.currentGroup = { ...this.currentGroup, ...updatedGroup };
            }
            // Consider re-fetching details for full consistency if needed
            // await this.fetchGroupDetails(groupId);
        } catch (err: any) {
            this.error = err.response?.data?.detail || err.message || 'Errore nell\'aggiornamento del gruppo.';
            throw err; // Propagate error for form handling
        } finally {
            this.isLoadingDetail = false;
        }
    },

    async deleteGroup(groupId: number) {
        this.isLoadingList = true; // Indicate loading on the list view
        this.error = null;
        try {
            await groupApi.deleteGroup(groupId);

            // Update local state
            this.groups = this.groups.filter(g => g.id !== groupId);
            if (this.currentGroup?.id === groupId) {
                this.clearCurrentGroup(); // Clear detail view if the deleted group was selected
            }
        } catch (err: any) {
            this.error = err.response?.data?.detail || err.message || 'Errore nell\'eliminazione del gruppo.';
        } finally {
            this.isLoadingList = false;
        }
    },

    // --- Group Members ---
    async fetchGroupMembers(groupId: number) {
        this.isLoadingDetail = true; // Loading happens in the detail view
        this.error = null;
        // Don't clear currentGroup here, only members
        this.currentGroupMembers = [];
        try {
            const response = await groupApi.getGroupMembers(groupId);
            // console.log('[DEBUG] fetchGroupMembers - API Response Data:', JSON.stringify(response.data)); // DEBUG REMOVED
            this.currentGroupMembers = response.data;
        } catch (err: any) {
            this.error = err.response?.data?.detail || err.message || 'Errore nel caricamento dei membri del gruppo.';
            this.currentGroupMembers = [];
        } finally {
            this.isLoadingDetail = false;
        }
    },

    async addStudentToGroup(groupId: number, studentData: AddStudentToGroupData) {
        this.isLoadingDetail = true;
        this.error = null;
        try {
            await groupApi.addStudentToGroup(groupId, studentData);

            // Re-fetch members to get updated list and joined_at date
            await this.fetchGroupMembers(groupId);
            // Optionally update student_count by re-fetching group details or incrementing locally
            // For simplicity, we rely on fetchGroupMembers or a subsequent fetchGroupDetails
            // to potentially update the count if the API provides it.
            // Consider adding student_count to GroupMember API response if needed frequently.
        } catch (err: any) {
            this.error = err.response?.data?.detail || err.message || 'Errore nell\'aggiunta dello studente al gruppo.';
             throw err; // Propagate error
        } finally {
            // isLoadingDetail is handled by fetchGroupMembers
        }
    },

    async removeStudentFromGroup(groupId: number, studentId: number) {
        this.isLoadingDetail = true;
        this.error = null;
        try {
            await groupApi.removeStudentFromGroup(groupId, studentId);

            // Update local state directly for immediate feedback
            this.currentGroupMembers = this.currentGroupMembers.filter(m => m.id !== studentId); // Usa m.id
            // Optionally update student_count by re-fetching group details or decrementing locally
            // await this.fetchGroupMembers(groupId); // Alternative: re-fetch for full consistency
        } catch (err: any) {
            this.error = err.response?.data?.detail || err.message || 'Errore nella rimozione dello studente dal gruppo.';
        } finally {
            this.isLoadingDetail = false;
        }
    },

     // --- Registration Token ---
    async generateRegistrationToken(groupId: number) {
        this.isLoadingDetail = true;
        this.error = null;
        try {
            const response = await groupApi.generateRegistrationToken(groupId);
            // L'API ora restituisce registration_link
            const newLink = response.data.registration_link;

            // Update local state
            if (this.currentGroup?.id === groupId) {
                // Aggiorna il link nello stato corrente
                this.currentGroup.registration_link = newLink;
                // Potrebbe essere necessario anche aggiornare il token grezzo se serve altrove,
                // ma l'API dei dettagli ora restituisce solo il link.
                // Se il token grezzo è ancora nel modello StudentGroup, aggiorniamo anche quello?
                // Assumiamo che il modello StudentGroup ora abbia solo registration_link.
                // this.currentGroup.registration_token = extractTokenFromLink(newLink); // Funzione helper ipotetica
            }
            const index = this.groups.findIndex(g => g.id === groupId);
            if (index !== -1) {
                // Aggiorna il link nella lista generale
                this.groups[index].registration_link = newLink;
                // this.groups[index].registration_token = extractTokenFromLink(newLink); // Se necessario
            }
        } catch (err: any) {
            this.error = err.response?.data?.detail || err.message || 'Errore nella generazione del token.';
        } finally {
            this.isLoadingDetail = false;
        }
    },

    async deleteRegistrationToken(groupId: number) {
        this.isLoadingDetail = true;
        this.error = null;
        try {
            await groupApi.deleteRegistrationToken(groupId);

            // Update local state
            if (this.currentGroup?.id === groupId) {
                this.currentGroup.registration_link = null;
                // this.currentGroup.registration_token = null; // Se necessario
            }
            const index = this.groups.findIndex(g => g.id === groupId);
            if (index !== -1) {
                this.groups[index].registration_link = null;
                // this.groups[index].registration_token = null; // Se necessario
            }
        } catch (err: any) {
            this.error = err.response?.data?.detail || err.message || 'Errore nell\'eliminazione del token.';
        } finally {
            this.isLoadingDetail = false;
        }
    },

  },

  getters: {
    // Example getter: get group by ID from the list
    getGroupById: (state) => (id: number) => {
      return state.groups.find((group) => group.id === id);
    },
  },
});