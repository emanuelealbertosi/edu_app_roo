export interface Notification {
  id: number;
  message: string;
  link: string; // Es. '/quiz/attempt/123/result'
  notification_type: string; // Es. 'QUIZ_GRADED'
  is_read: boolean;
  created_at: string; // Formato ISO date string, es. "2025-05-09T10:00:00Z"
}

export interface NotificationsState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
}