import apiClient from './config'
import type { AxiosResponse } from 'axios'

// Interfaccia basata su StudentRegistrationTokenSerializer
export interface RegistrationToken {
  token: string // UUID come stringa
  teacher: number
  teacher_username: string
  group: number | null
  group_name: string | null
  created_at: string
  expires_at: string
  is_active: boolean
  is_valid: boolean // Calcolato dal backend
}

// Interfaccia per il payload della creazione
interface CreateTokenPayload {
  group_id?: number | null // ID del gruppo opzionale
  // Potremmo aggiungere 'validity_duration' se volessimo sovrascrivere il default
}

/**
 * Recupera l'elenco dei token di registrazione per il docente autenticato.
 */
export const fetchRegistrationTokens = async (): Promise<RegistrationToken[]> => {
  try {
    const response: AxiosResponse<RegistrationToken[]> = await apiClient.get('/teacher/registration-tokens/')
    return response.data
  } catch (error) {
    console.error('Errore nel recupero dei token di registrazione:', error)
    throw error
  }
}

/**
 * Crea un nuovo token di registrazione per il docente autenticato.
 * @param payload - Oggetto opzionale contenente group_id.
 */
export const createRegistrationToken = async (payload: CreateTokenPayload = {}): Promise<RegistrationToken> => {
  try {
    const response: AxiosResponse<RegistrationToken> = await apiClient.post('/teacher/registration-tokens/', payload)
    return response.data
  } catch (error) {
    console.error('Errore nella creazione del token di registrazione:', error)
    throw error
  }
}

/**
 * Disattiva un token di registrazione esistente.
 * @param token - L'UUID del token da disattivare.
 */
export const deactivateRegistrationToken = async (token: string): Promise<void> => {
  try {
    // L'URL per l'azione custom è /teacher/registration-tokens/{token}/deactivate/
    await apiClient.post(`/teacher/registration-tokens/${token}/deactivate/`)
  } catch (error) {
    console.error(`Errore nella disattivazione del token ${token}:`, error)
    throw error
  }
}

/**
 * Elimina un token di registrazione esistente.
 * @param token - L'UUID del token da eliminare.
 */
export const deleteRegistrationToken = async (token: string): Promise<void> => {
  try {
    await apiClient.delete(`/teacher/registration-tokens/${token}/`)
  } catch (error) {
    console.error(`Errore nell'eliminazione del token ${token}:`, error)
    throw error
  }
}