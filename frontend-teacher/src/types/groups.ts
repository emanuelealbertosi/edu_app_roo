// frontend-teacher/src/types/groups.ts

/**
 * Rappresenta uno studente membro di un gruppo,
 * come restituito dall'API (es. /api/groups/{id}/students/).
 */
export interface GroupMember {
  id: number; // CORRETTO: Usa 'id' come restituito da StudentBasicSerializer
  student_code?: string; // Aggiunto per coerenza con StudentBasicSerializer (opzionale)
  first_name: string;
  last_name: string;
  // Potremmo aggiungere l'email o l'identificativo unico se necessario
  joined_at: string; // Data di aggiunta al gruppo (ISO string)
}

/**
 * Rappresenta un gruppo di studenti.
 */
export interface StudentGroup {
  id: number;
  name: string;
  description: string | null;
  registration_link: string | null; // Sostituito token con link
  created_at: string; // ISO date string
  is_active: boolean;
  student_count?: number; // Numero di studenti nel gruppo (opzionale, utile per le liste)
  // teacher_id non è necessario se l'API è già filtrata per il docente loggato
  // students: GroupMember[]; // Potrebbe essere caricato separatamente nella vista dettaglio
}

/**
 * Dati necessari per creare o aggiornare un gruppo.
 */
export interface StudentGroupData {
  name: string;
  description?: string | null;
  is_active?: boolean; // Generalmente gestito separatamente o al momento della creazione
}

/**
 * Dati per aggiungere uno studente a un gruppo.
 * Potrebbe essere l'ID dello studente o un identificativo unico.
 */
export interface AddStudentToGroupData {
    student_id: number; // O un altro identificatore come 'unique_identifier'
}