export interface StudentGroup {
  id: number;
  owner: number; // ID del docente proprietario (SOSTITUISCE teacher_id)
  owner_name?: string; // Nome del proprietario (dal serializer)
  name: string;
  description?: string | null;
  is_public?: boolean; // Aggiunto
  registration_link?: string | null; // Aggiunto
  created_at?: string;
  is_active?: boolean;
  // members?: any[]; // Potremmo definire un tipo Member se necessario
  student_count?: number; // Numero di membri
  pending_requests_count?: number | null; // Numero richieste pendenti (solo per owner)
}

// Potrebbe servire anche un tipo per l'assegnazione,
// anche se l'API potrebbe richiedere solo l'ID del gruppo.
export interface GroupAssignmentPayload {
  group_ids: number[];
  // altri parametri se necessari, es. lesson_id
}