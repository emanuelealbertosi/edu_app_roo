import apiClient from './apiClient';
import type { Announcement } from '@/types/announcements';

/**
 * Recupera gli avvisi per il docente autenticato.
 * @returns Una Promise che risolve in un array di avvisi.
 */
export const getAnnouncementsAPI = async (): Promise<Announcement[]> => {
  const response = await apiClient.get<Announcement[]>('announcements/');
  return response.data;
};

/**
 * Segna uno specifico avviso come letto.
 * @param announcementId - L'ID dell'avviso da segnare come letto.
 * @returns Una Promise che risolve quando l'operazione è completa.
 */
export const markAnnouncementAsReadAPI = async (announcementId: number): Promise<void> => {
  await apiClient.post(`announcements/${announcementId}/mark-as-read/`);
};

/**
 * Imposta un avviso per non essere più mostrato all'utente.
 * @param announcementId - L'ID dell'avviso da non mostrare più.
 * @returns Una Promise che risolve quando l'operazione è completa.
 */
export const markAnnouncementAsDoNotShowAgainAPI = async (announcementId: number): Promise<void> => {
  await apiClient.post(`announcements/${announcementId}/do-not-show-again/`);
};