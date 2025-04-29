// frontend-teacher/src/api/groups.ts
import apiClient from './apiClient';
import type { StudentGroup, GroupMember, StudentGroupData, AddStudentToGroupData, GroupAccessRequest, GroupAccessRequestData, RespondGroupAccessRequestData } from '@/types/groups'; // Importa i nuovi tipi

// --- Group CRUD ---

/**
 * Recupera l'elenco dei gruppi per il docente autenticato.
 */
export const getGroups = (): Promise<{ data: StudentGroup[] }> => {
  // Corretto: L'endpoint corretto per la lista dei gruppi è /groups/groups/
  // a causa della registrazione del router (`router.register(r'groups', ...)`).
  return apiClient.get('/groups/groups/');
};

/**
 * Recupera i dettagli di un gruppo specifico.
 * @param groupId L'ID del gruppo.
 */
export const getGroup = (groupId: number): Promise<{ data: StudentGroup }> => {
  return apiClient.get(`/groups/groups/${groupId}/`); // Corretto: Aggiunto /groups/ dal router
};

/**
 * Crea un nuovo gruppo.
 * @param groupData I dati per il nuovo gruppo.
 */
export const createGroup = (groupData: StudentGroupData): Promise<{ data: StudentGroup }> => {
  return apiClient.post('/groups/', groupData);
};

/**
 * Aggiorna un gruppo esistente.
 * @param groupId L'ID del gruppo da aggiornare.
 * @param groupData I dati da aggiornare (parziali o completi).
 */
export const updateGroup = (groupId: number, groupData: Partial<StudentGroupData>): Promise<{ data: StudentGroup }> => {
  // Usiamo PATCH per aggiornamenti parziali, PUT richiederebbe tutti i campi.
  return apiClient.patch(`/groups/${groupId}/`, groupData);
};

/**
 * Elimina un gruppo.
 * @param groupId L'ID del gruppo da eliminare.
 */
export const deleteGroup = (groupId: number): Promise<void> => {
  return apiClient.delete(`/groups/${groupId}/`);
};

// --- Group Members ---

/**
 * Recupera l'elenco dei membri (studenti) di un gruppo specifico.
 * @param groupId L'ID del gruppo.
 */
export const getGroupMembers = (groupId: number): Promise<{ data: GroupMember[] }> => {
  return apiClient.get(`/groups/groups/${groupId}/students/`); // Corretto: Aggiunto /groups/ dal router
};

/**
 * Aggiunge uno studente a un gruppo.
 * @param groupId L'ID del gruppo.
 * @param studentData L'ID dello studente da aggiungere (o altri dati richiesti dall'API).
 */
export const addStudentToGroup = (groupId: number, studentData: AddStudentToGroupData): Promise<void> => {
  // L'endpoint corretto definito nel backend è /add-student/
  return apiClient.post(`/groups/${groupId}/add-student/`, studentData);
};

/**
 * Rimuove uno studente da un gruppo.
 * @param groupId L'ID del gruppo.
 * @param studentId L'ID dello studente da rimuovere.
 */
export const removeStudentFromGroup = (groupId: number, studentId: number): Promise<void> => {
  // L'endpoint corretto nel backend usa POST e il path 'remove-student'
  return apiClient.post(`/groups/${groupId}/remove-student/${studentId}/`);
};


// --- Registration Token ---

/**
 * Genera (o rigenera) un token di registrazione per un gruppo.
 * @param groupId L'ID del gruppo.
 */
export const generateRegistrationToken = (groupId: number): Promise<{ data: { registration_link: string } }> => { // Aggiornato tipo di ritorno
    // Assumiamo un endpoint specifico con POST, come da piano backend
    return apiClient.post(`/groups/${groupId}/generate-token/`);
};

/**
 * Elimina il token di registrazione per un gruppo.
 * @param groupId L'ID del gruppo.
 */
export const deleteRegistrationToken = (groupId: number): Promise<void> => {
    // Assumiamo un endpoint specifico con DELETE o POST
    return apiClient.delete(`/groups/${groupId}/delete-token/`); // O POST se l'API lo richiede
};
// --- Group Discovery & Access Requests ---

/**
 * Recupera l'elenco dei gruppi pubblici disponibili per la richiesta di accesso.
 * Esclude i gruppi propri e quelli per cui esiste già una richiesta.
 * @param searchTerm (Opzionale) Termine di ricerca (attualmente non implementato nel backend per questo endpoint).
 */
export const searchPublicGroups = (searchTerm?: string): Promise<{ data: StudentGroup[] }> => {
  // Utilizza il nuovo endpoint dedicato '/public/' creato nel backend.
  // Rimuoviamo i parametri 'is_public' e 'search' perché gestiti dal backend.
  // Potremmo passare 'search' se il backend lo supportasse in futuro.
  const params: Record<string, any> = {};
  if (searchTerm) {
    // Se volessimo supportare la ricerca in futuro, aggiungeremmo il parametro qui:
    // params.search = searchTerm;
    // Per ora, lo ignoriamo dato che il backend non lo usa su questo endpoint.
  }
  // Corretto (v2): Usa l'URL relativo corretto rispetto alla base '/api/' e al prefisso '/groups/' in config/urls.py
  return apiClient.get('/groups/public/', { params });
};

/**
 * Invia una richiesta di accesso per un gruppo specifico.
 * @param requestData L'ID del gruppo a cui richiedere accesso.
 */
export const requestGroupAccess = (requestData: GroupAccessRequestData): Promise<{ data: GroupAccessRequest }> => {
  // Corretto: Usa l'URL relativo corretto basato sulla registrazione del router in urls.py
  return apiClient.post('/groups/access-requests/', requestData);
};

/**
 * Recupera l'elenco delle richieste di accesso pendenti per un gruppo specifico (solo owner).
 * @param groupId L'ID del gruppo.
 */
export const getGroupAccessRequests = (groupId: number): Promise<{ data: GroupAccessRequest[] }> => {
  // L'azione custom nel backend è definita con url_path='access-requests' sul ViewSet registrato sotto /groups/groups/
  return apiClient.get(`/groups/groups/${groupId}/access-requests/`); // Corretto URL
};

/**
 * Risponde a una richiesta di accesso specifica (solo owner).
 * @param requestId L'ID della richiesta a cui rispondere.
 * @param responseData Dati della risposta (approve: true/false).
 */
export const respondToGroupAccessRequest = (groupId: number, requestId: number, responseData: { status: 'APPROVED' | 'REJECTED' }): Promise<void> => {
  // L'azione custom nel backend è definita con url_path='respond-request' sul ViewSet del gruppo
  // L'URL corretto è /api/student-groups/groups/{groupId}/respond-request/
  // Il corpo della richiesta deve contenere request_id e status, come atteso dal RespondGroupAccessRequestSerializer
  const payload = {
    request_id: requestId,
    status: responseData.status
  };
  return apiClient.post(`/groups/groups/${groupId}/respond-request/`, payload);
};