// frontend-teacher/src/api/groups.ts
import apiClient from './apiClient';
import type { StudentGroup, GroupMember, StudentGroupData, AddStudentToGroupData } from '@/types/groups';

// --- Group CRUD ---

/**
 * Recupera l'elenco dei gruppi per il docente autenticato.
 */
export const getGroups = (): Promise<{ data: StudentGroup[] }> => {
  return apiClient.get('/groups/');
};

/**
 * Recupera i dettagli di un gruppo specifico.
 * @param groupId L'ID del gruppo.
 */
export const getGroup = (groupId: number): Promise<{ data: StudentGroup }> => {
  return apiClient.get(`/groups/${groupId}/`);
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
  return apiClient.get(`/groups/${groupId}/students/`);
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