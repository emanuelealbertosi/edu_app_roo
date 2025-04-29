// frontend-teacher/src/stores/groups.ts
import { defineStore } from 'pinia';
// Importa tipi direttamente da types/groups
import type { StudentGroup, GroupMember, StudentGroupData, AddStudentToGroupData, GroupAccessRequestData, GroupAccessRequest, RespondGroupAccessRequestData } from '@/types/groups'; // Aggiunto GroupAccessRequest, RespondGroupAccessRequestData
// Import API functions
import * as groupApi from '@/api/groups';

interface GroupState {
  groups: StudentGroup[]; // Gruppi del docente o a cui ha accesso
  currentGroup: StudentGroup | null;
  currentGroupMembers: GroupMember[];
  accessRequests: GroupAccessRequest[]; // Richieste di accesso per il gruppo corrente
  publicGroupsSearchResult: StudentGroup[]; // Risultati ricerca gruppi pubblici
  isLoadingList: boolean;
  isLoadingDetail: boolean; // For group details and members
  isLoadingRequests: boolean; // Loading per le richieste di accesso
  isLoadingSearch: boolean; // Loading per la ricerca
  error: string | null;
  requestsError: string | null; // Errore specifico per le richieste
  searchError: string | null; // Errore specifico per la ricerca
  requestAccessError: string | null; // Errore specifico per richiesta accesso
  requestAccessSuccess: boolean; // Flag per successo richiesta accesso
}

export const useGroupStore = defineStore('groups', {
  state: (): GroupState => ({
    groups: [],
    currentGroup: null,
    currentGroupMembers: [],
    accessRequests: [], // Inizializza vuoto
    publicGroupsSearchResult: [], // Inizializza vuoto
    isLoadingList: false,
    isLoadingDetail: false,
    isLoadingRequests: false, // Inizializza loading richieste
    isLoadingSearch: false, // Inizializza loading ricerca
    error: null,
    requestsError: null, // Inizializza errore richieste
    searchError: null, // Inizializza errore ricerca
    requestAccessError: null, // Inizializza errore richiesta
    requestAccessSuccess: false, // Inizializza flag successo
  }),

  actions: {
    clearError() {
      this.error = null;
    },

    clearCurrentGroup() {
        this.currentGroup = null;
        this.currentGroupMembers = [];
        this.isLoadingDetail = false; // Reset loading state as well
        this.accessRequests = []; // Pulisci anche le richieste
        this.isLoadingRequests = false;
        this.requestsError = null;
        this.error = null; // Clear errors related to the specific group
    },

    // --- Group List ---
    async fetchGroups() {
      this.isLoadingList = true;
      this.error = null;
      try {
        console.log('[Store Groups] Calling groupApi.getGroups()...'); // LOG
        const response = await groupApi.getGroups();
        console.log('[Store Groups] API Response for getGroups:', JSON.stringify(response.data)); // LOG
        this.groups = response.data;
        console.log('[Store Groups] State `groups` updated:', JSON.stringify(this.groups)); // LOG
      } catch (err: any) {
        console.error('[Store Groups] Error fetching groups:', err); // LOG Errore
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

    // --- Group Discovery & Access Requests ---
    async searchPublicGroups(searchTerm: string) {
        this.isLoadingSearch = true;
        this.searchError = null;
        this.publicGroupsSearchResult = []; // Clear previous results
        try {
            // Assicurati che GroupAccessRequestData sia importato se necessario
            const response = await groupApi.searchPublicGroups(searchTerm);
            this.publicGroupsSearchResult = response.data;
        } catch (err: any) {
            this.searchError = err.response?.data?.detail || err.message || 'Errore nella ricerca dei gruppi pubblici.';
            this.publicGroupsSearchResult = [];
        } finally {
            this.isLoadingSearch = false;
        }
    },

    async requestAccess(groupId: number) {
        // Potremmo usare isLoadingDetail o un loading specifico per questa azione
        this.isLoadingDetail = true; // Riutilizziamo isLoadingDetail per semplicità
        this.requestAccessError = null;
        this.requestAccessSuccess = false;
        try {
            // Usa il tipo importato direttamente
            const requestData: GroupAccessRequestData = { group: groupId };
            await groupApi.requestGroupAccess(requestData);
            this.requestAccessSuccess = true; // Imposta flag successo
            // Potremmo voler mostrare un messaggio all'utente
        } catch (err: any) {
            this.requestAccessError = err.response?.data?.detail || err.response?.data?.group?.[0] || err.message || 'Errore nell\'invio della richiesta di accesso.';
             this.requestAccessSuccess = false;
             // Rethrow per gestione nel componente se necessario
             // throw err;
        } finally {
            this.isLoadingDetail = false;
        }
    },

    // --- Access Request Management (Owner) ---
    async fetchAccessRequests(groupId: number) {
        this.isLoadingRequests = true;
        this.requestsError = null;
        this.accessRequests = [];
        try {
            const response = await groupApi.getGroupAccessRequests(groupId);
            this.accessRequests = response.data;
        } catch (err: any) {
            this.requestsError = err.response?.data?.detail || err.message || 'Errore nel caricamento delle richieste di accesso.';
            this.accessRequests = [];
        } finally {
            this.isLoadingRequests = false;
        }
    },

    async respondToRequest(groupId: number, requestId: number, approve: boolean) { // Aggiunto groupId
        this.isLoadingRequests = true; // Potrebbe essere un loading diverso?
        this.requestsError = null;
        try {
            // Costruisci il payload corretto per la nuova API
            const responseData = { status: approve ? 'APPROVED' : 'REJECTED' as 'APPROVED' | 'REJECTED' };
            // Chiama la funzione API aggiornata con groupId, requestId e il nuovo payload
            await groupApi.respondToGroupAccessRequest(groupId, requestId, responseData);
            // Rimuovi la richiesta dallo stato locale dopo la risposta
            this.accessRequests = this.accessRequests.filter(req => req.id !== requestId);
            // Potrebbe essere necessario aggiornare l'elenco dei membri se la richiesta è stata approvata?
            // O l'elenco dei gruppi accessibili per il richiedente?
            // Per ora, gestiamo solo la rimozione dalla lista delle richieste pendenti.
        } catch (err: any) {
            this.requestsError = err.response?.data?.detail || err.message || 'Errore nella risposta alla richiesta di accesso.';
            // Rethrow se necessario per UI
            // throw err;
        } finally {
            this.isLoadingRequests = false;
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