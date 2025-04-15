import apiClient from './config'; // Importa l'istanza axios configurata
import type { AxiosResponse } from 'axios';

// Interfaccia per rappresentare i dati di uno studente (basata su StudentSerializer)
// Assicurati che corrisponda ai campi restituiti dal backend
export interface Student {
  id: number;
  // user_id: number; // Rimosso, non presente nel serializer aggiornato
  username: string;
  first_name: string;
  last_name: string;
  student_code: string;
  teacher?: number; // ID del docente associato (potrebbe essere utile)
  teacher_username?: string; // Aggiunto
  full_name?: string; // Aggiunto
  is_active?: boolean; // Aggiunto
  created_at?: string; // Aggiunto
  group_name?: string | null; // Aggiunto per mostrare il nome del gruppo
  group_id?: number | null; // Aggiunto per riferimento (potrebbe essere utile)
}

/**
 * Recupera l'elenco degli studenti associati al docente autenticato.
 * Richiede autenticazione (il token JWT viene aggiunto automaticamente da apiClient).
 */
export const fetchStudents = async (): Promise<Student[]> => {
  try {
    // Corretto: il percorso è relativo a baseURL ('/api')
    const response: AxiosResponse<Student[]> = await apiClient.get('/students/');
    return response.data;
  } catch (error) {
    console.error('Errore durante il recupero degli studenti:', error);
    // Potresti voler rilanciare l'errore o gestirlo in modo più specifico
    throw error;
  }
};

/**
 * Recupera i dettagli di un singolo studente tramite il suo ID.
 * Richiede autenticazione.
 * @param studentId L'ID dello studente da recuperare.
 */
export const fetchStudentById = async (studentId: number): Promise<Student> => {
  try {
    const response: AxiosResponse<Student> = await apiClient.get(`/students/${studentId}/`);
    return response.data;
  } catch (error) {
    console.error(`Errore durante il recupero dello studente ${studentId}:`, error);
    throw error;
  }
};

// Altre funzioni API relative agli studenti
// es. createStudent, updateStudent, deleteStudent

// Interfaccia per un'assegnazione di quiz (basata su StudentQuizAssignmentSerializer)
export interface StudentQuizAssignment {
  id: number; // ID dell'assegnazione
  quiz: number; // ID del quiz
  quiz_title: string;
  quiz_description: string | null;
  assigned_at: string;
  due_date: string | null;
}

// Interfaccia per un'assegnazione di percorso (basata su StudentPathwayAssignmentSerializer)
export interface StudentPathwayAssignment {
  id: number; // ID dell'assegnazione
  pathway: number; // ID del percorso
  pathway_title: string;
  pathway_description: string | null;
  assigned_at: string;
}

// Interfaccia per la risposta completa dell'endpoint assignments
export interface StudentAssignmentsResponse {
  quiz_assignments: StudentQuizAssignment[];
  pathway_assignments: StudentPathwayAssignment[];
}


/**
 * Recupera l'elenco delle assegnazioni (quiz e percorsi) per un dato studente.
 * Richiede autenticazione.
 * @param studentId L'ID dello studente.
 */
export const fetchStudentAssignments = async (studentId: number): Promise<StudentAssignmentsResponse> => {
  try {
    // L'URL per l'azione custom è /students/{student_pk}/assignments/
    const response: AxiosResponse<StudentAssignmentsResponse> = await apiClient.get(`/students/${studentId}/assignments/`);
    return response.data;
  } catch (error) {
    console.error(`Errore durante il recupero delle assegnazioni per lo studente ${studentId}:`, error);
    throw error;
  }
};

// Interfaccia per il payload della creazione studente da parte del docente
export interface TeacherCreateStudentPayload {
  first_name: string;
  last_name: string;
  group_id?: number | null; // Aggiunto campo opzionale per assegnare gruppo alla creazione
}

// Interfaccia per la risposta della creazione studente da parte del docente
// Include il PIN generato (solo in questa risposta)
export interface TeacherCreateStudentResponse extends Student {
  pin: string; // PIN generato in chiaro
}

/**
 * Crea un nuovo studente associato al docente autenticato.
 * Genera automaticamente codice studente e PIN.
 * @param payload Dati dello studente (nome, cognome).
 * @returns I dati dello studente creato, incluso il PIN generato.
 */
export const createStudentByTeacher = async (payload: TeacherCreateStudentPayload): Promise<TeacherCreateStudentResponse> => {
  try {
    // L'endpoint è POST /students/
    // Il backend userà TeacherStudentCreateSerializer grazie alla logica in get_serializer_class
    const response: AxiosResponse<TeacherCreateStudentResponse> = await apiClient.post('/students/', payload);
    return response.data;
  } catch (error) {
    console.error('Errore durante la creazione dello studente:', error);
    throw error;
  }
};

// Interfaccia per il payload dell'aggiornamento studente
export interface StudentUpdatePayload {
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  group_id?: number | null; // Permette di cambiare o rimuovere il gruppo
}

/**
 * Aggiorna i dati di uno studente esistente.
 * Richiede autenticazione (Docente o Admin proprietario).
 * @param studentId L'ID dello studente da aggiornare.
 * @param payload Oggetto con i campi da aggiornare.
 */
export const updateStudent = async (studentId: number, payload: StudentUpdatePayload): Promise<Student> => {
  try {
    // Usiamo PATCH per aggiornamenti parziali
    const response: AxiosResponse<Student> = await apiClient.patch(`/students/${studentId}/`, payload);
    return response.data;
  } catch (error) {
    console.error(`Errore durante l'aggiornamento dello studente ${studentId}:`, error);
    throw error;
  }
};


// Interfaccia per il sommario dei progressi (basata su StudentProgressSummarySerializer)
export interface StudentProgressSummary {
  student_id: number;
  full_name: string;
  student_code: string; // Corretto da username a student_code
  group_name: string | null; // Aggiunto nome gruppo
  completed_quizzes_count: number;
  completed_pathways_count: number;
  total_points_earned: number;
  average_quiz_score: number;
}

/**
 * Recupera il sommario dei progressi per uno o più studenti.
 * Se studentId è fornito, filtra per quello studente.
 * Richiede autenticazione (Docente).
 * @param studentId (Opzionale) L'ID dello studente per cui recuperare le statistiche.
 */
export const fetchStudentProgressSummary = async (studentId?: number): Promise<StudentProgressSummary[]> => {
  try {
    const params = studentId ? { student_id: studentId } : {};
    // Endpoint corretto basato su apps/users/urls.py
    const response: AxiosResponse<StudentProgressSummary[]> = await apiClient.get('/teacher/student-progress-summary/', { params });
    return response.data;
  } catch (error) {
    console.error(`Errore durante il recupero del sommario progressi (studente ${studentId}):`, error);
    throw error;
  }
};