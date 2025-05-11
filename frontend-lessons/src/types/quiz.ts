// Interfaccia base per un Quiz
export interface Quiz {
  id: number;
  teacher: number; // FK a User (docente creatore)
  source_template_id?: number | null; // FK a QuizTemplate (opzionale)
  title: string;
  description?: string | null;
  subject?: number | null; // FK a Subject (opzionale)
  subject_name?: string; // Denormalizzato per comodità di visualizzazione
  subject_color_placeholder?: string; // Denormalizzato
  topic?: number | null; // FK a Topic (opzionale)
  topic_name?: string; // Denormalizzato
  image_url?: string | null;
  // metadata: Record<string, any>; // Es: difficoltà, completion_threshold, points_on_completion
  // Per semplicità iniziale, metadata può essere any. In futuro si potrebbe tipizzare meglio.
  metadata?: any; 
  created_at: string;
  available_from?: string | null;
  available_until?: string | null;
  updated_at?: string;
  questions_count?: number; // Numero di domande, utile per le liste
  // questions: Question[]; // Array di domande, da definire se si gestiscono qui
}

// Interfaccia per una Domanda (Question) - semplificata per ora
export interface Question {
  id: number;
  quiz: number; // FK a Quiz
  text: string;
  question_type: string; // Es: 'multiple_choice_single', 'true_false', ecc.
  order: number;
  // metadata: Record<string, any>; // Es: punti
  metadata?: any;
  // answer_options: AnswerOption[]; // Array di opzioni di risposta
}

// Interfaccia per un'Opzione di Risposta (AnswerOption) - semplificata
export interface AnswerOption {
  id: number;
  question: number; // FK a Question
  text: string;
  is_correct: boolean;
  order: number;
}

// Potrebbero servire altri tipi relativi ai tentativi (QuizAttempt), assegnazioni (QuizAssignment) ecc.
// ma per ora ci concentriamo sulla struttura base del Quiz per la selezione.