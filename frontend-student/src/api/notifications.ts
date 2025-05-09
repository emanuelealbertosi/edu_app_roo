import apiClient from './config';
import type { Notification } from '@/types/notifications'; // Percorso relativo allo root di src/

/**
 * Recupera le notifiche per lo studente autenticato.
 * @param onlyUnread - Se true, richiede solo le notifiche non lette.
 * @returns Una Promise che risolve in un array di notifiche.
 */
export const getNotificationsAPI = async (onlyUnread: boolean = false): Promise<Notification[]> => {
  const params: { is_read?: string } = {};
  if (onlyUnread) {
    params.is_read = 'false';
  }
  // L'URL completo sarà gestito da baseURL di apiClient, es. http://localhost:8000/api/student/notifications/
  const response = await apiClient.get<Notification[]>('student/student/notifications/', { params });
  return response.data;
};

/**
 * Segna una specifica notifica come letta.
 * @param notificationId - L'ID della notifica da segnare come letta.
 * @returns Una Promise che risolve quando l'operazione è completa.
 */
export const markNotificationAsReadAPI = async (notificationId: number): Promise<void> => {
  await apiClient.post(`student/student/notifications/${notificationId}/mark-as-read/`);
};

/**
 * Segna tutte le notifiche non lette dello studente come lette.
 * @returns Una Promise che risolve quando l'operazione è completa.
 */
export const markAllNotificationsAsReadAPI = async (): Promise<void> => {
  await apiClient.post('student/student/notifications/mark-all-as-read/');
};