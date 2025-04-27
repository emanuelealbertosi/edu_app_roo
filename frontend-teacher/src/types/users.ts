// frontend-teacher/src/types/users.ts

/**
 * Rappresenta i dati di uno studente come restituiti dall'API.
 * Basato su StudentSerializer nel backend.
 */
export interface Student {
  id: number;
  teacher: number; // ID del docente associato
  teacher_username: string;
  first_name: string;
  last_name: string;
  student_code: string;
  is_active: boolean;
  created_at: string; // ISO date string
  full_name: string;
}

/**
 * Rappresenta i dati di un utente (Docente/Admin).
 * Basato su UserSerializer nel backend.
 */
export interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    role: string; // Es. 'TEACHER', 'ADMIN'
    role_display: string; // Es. 'Docente', 'Amministratore'
    is_active: boolean;
    date_joined: string; // ISO date string
}