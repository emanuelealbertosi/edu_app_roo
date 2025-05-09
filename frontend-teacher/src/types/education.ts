// Definizioni preliminari per i tipi relativi a education in frontend-teacher

export interface QuizAttempt {
  id: number;
  student_name?: string; // Opzionale, potrebbe venire da un join
  quiz_title?: string;   // Opzionale, potrebbe venire da un join
  status: string; // Es. 'PENDING_GRADING', 'COMPLETED', 'IN_PROGRESS', 'FAILED'
  started_at: string | null;
  completed_at: string | null; // Data sottomissione per correzione o completamento finale
  score?: number | null;
  // Aggiungere altri campi rilevanti per QuizAttempt se necessario
  // Esempio:
  // student_id: number;
  // quiz_id: number;
}

export interface AnswerOption { // Aggiunta per GradingQuestionData
  id: number;
  text: string;
  is_correct: boolean;
  order?: number; // Opzionale, ma utile
}

export interface Question {
  id: number;
  text: string;
  question_type: string; // Es. 'OPEN_MANUAL', 'MC_SINGLE', ecc.
  question_type_display?: string; // Per visualizzazione
  order: number;
  metadata?: Record<string, any>; // Oggetto generico per metadati
  answer_options?: AnswerOption[]; // Per MC, TF
  // student_answer?: GradingStudentAnswerData; // Questo sarebbe specifico del contesto di un tentativo
}


// Potremmo aggiungere altri tipi qui in futuro
// specifici per il frontend del docente.