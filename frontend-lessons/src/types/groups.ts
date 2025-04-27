export interface StudentGroup {
  id: number;
  name: string;
  description?: string | null;
  teacher_id: number; // O l'ID dell'utente docente
  student_count?: number; // Potrebbe essere utile averlo
  created_at?: string;
  is_active?: boolean;
}

// Potrebbe servire anche un tipo per l'assegnazione,
// anche se l'API potrebbe richiedere solo l'ID del gruppo.
export interface GroupAssignmentPayload {
  group_ids: number[];
  // altri parametri se necessari, es. lesson_id
}