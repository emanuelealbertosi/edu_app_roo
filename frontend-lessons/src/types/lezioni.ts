// Definizione basata sui modelli Django e sugli endpoint API

export interface UserSummary {
  id: number;
  username: string;
  first_name?: string;
  last_name?: string;
}

export interface Subject {
  id: number;
  name: string;
  description: string;
  creator: UserSummary | null; // O solo ID a seconda del serializer
  created_at: string;
  updated_at: string;
}

export interface Topic {
  id: number;
  name: string;
  description: string;
  subject: number; // ID della materia
  subject_details?: Subject; // Opzionale, se il serializer annida
  creator: UserSummary | null;
  created_at: string;
  updated_at: string;
}

// Definizione base dello Studente - Potrebbe essere più complessa
// Assicurati che corrisponda al modello Student effettivo nel backend
export interface Student {
  id: number;
  user_id: number; // ID del Docente associato (se applicabile nel contesto)
  first_name: string;
  last_name: string;
  unique_identifier: string; // Codice o username studente
  created_at: string;
  is_active: boolean;
  // Aggiungere altri campi se necessari dal backend (es. email, ecc.)
}

export interface LessonAssignment {
  id: number;
  lesson: number; // ID Lezione
  lesson_details?: Lesson; // Opzionale - Attenzione: riferimento circolare potenziale se non gestito con cura
  student: number; // ID Studente
  student_details?: Student; // Opzionale
  assigned_by: UserSummary; // Docente che ha assegnato
  assigned_at: string;
  viewed_at: string | null;
}


export interface Lesson {
  id: number;
  title: string;
  description: string;
  topic: number; // ID dell'argomento
  topic_details?: Topic; // Opzionale
  topic_name: string; // Aggiunto per il nome diretto
  subject_name: string; // Aggiunto per il nome diretto
  creator: UserSummary; // Assumiamo Docente
  created_at: string;
  updated_at: string;
  is_published: boolean;
  contents?: LessonContent[]; // Opzionale, caricato separatamente o annidato
  assignments?: LessonAssignment[]; // Opzionale
}

export interface LessonContent {
  id: number;
  lesson: number; // ID della lezione
  content_type: 'html' | 'pdf' | 'ppt' | 'url'; // Aggiungere altri tipi se necessario
  html_content?: string;
  file?: string; // URL del file
  url?: string;
  title?: string;
  order: number;
  created_at: string; // Aggiunta virgola mancante
}


// Tipo per il risultato dell'operazione di assegnazione multipla
export interface AssignmentResult {
    studentId: number;
    success: boolean;
    error?: string; // Messaggio di errore in caso di fallimento
}