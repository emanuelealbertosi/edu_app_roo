import apiClient from './config'
import type { AxiosResponse } from 'axios'

// Interfaccia basata sul StudentGroupSerializer di Django
export interface StudentGroup {
  id: number
  name: string
  teacher: number // ID del docente
  teacher_username: string
  member_count: number // Conteggio membri (calcolato dal backend)
  created_at: string
  updated_at: string
  // Nota: la lista degli studenti membri non è inclusa qui,
  // viene gestita tramite l'endpoint degli studenti.
}

// Tipo per i dati di creazione/aggiornamento
interface GroupPayload {
  name: string
}

/**
 * Recupera l'elenco dei gruppi del docente autenticato.
 */
export const fetchGroups = async (): Promise<StudentGroup[]> => {
  try {
    const response: AxiosResponse<StudentGroup[]> = await apiClient.get('/teacher/groups/')
    return response.data
  } catch (error) {
    console.error('Errore nel recupero dei gruppi:', error)
    throw error // Rilancia l'errore per gestirlo nel componente chiamante
  }
}

/**
 * Crea un nuovo gruppo per il docente autenticato.
 * @param groupData - Oggetto contenente il nome del gruppo.
 */
export const createGroup = async (groupData: GroupPayload): Promise<StudentGroup> => {
  try {
    const response: AxiosResponse<StudentGroup> = await apiClient.post('/teacher/groups/', groupData)
    return response.data
  } catch (error) {
    console.error('Errore nella creazione del gruppo:', error)
    throw error
  }
}

/**
 * Aggiorna un gruppo esistente.
 * @param groupId - ID del gruppo da aggiornare.
 * @param groupData - Oggetto contenente il nuovo nome del gruppo.
 */
export const updateGroup = async (groupId: number, groupData: GroupPayload): Promise<StudentGroup> => {
  try {
    const response: AxiosResponse<StudentGroup> = await apiClient.put(`/teacher/groups/${groupId}/`, groupData)
    return response.data
  } catch (error) {
    console.error(`Errore nell'aggiornamento del gruppo ${groupId}:`, error)
    throw error
  }
}

/**
 * Elimina un gruppo esistente.
 * @param groupId - ID del gruppo da eliminare.
 */
export const deleteGroup = async (groupId: number): Promise<void> => {
  try {
    await apiClient.delete(`/teacher/groups/${groupId}/`)
  } catch (error) {
    console.error(`Errore nell'eliminazione del gruppo ${groupId}:`, error)
    throw error
  }
}