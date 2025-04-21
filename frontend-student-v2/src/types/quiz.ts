// src/types/quiz.ts

// Tipo per la risposta base da start-attempt (solo ID e info essenziali)
export interface StartAttemptResponse {
  id: number; // ID del QuizAttempt
  status: string;
  quiz: {
    id: number;
    title: string;
  };
  // Aggiungere altri campi se utili subito, ma NON le domande
}


// Opzione di risposta per una domanda specifica in un tentativo (come da API /current-question/)
export interface AttemptAnswerOption {
  id: number; // ID dell'AnswerOption originale
  text: string;
  order: number; // Ordine dell'opzione
  is_correct?: boolean | null; // Inclusa dall'API, ma non dovremmo usarla per lo studente
}

// Domanda specifica all'interno di un tentativo di quiz (come da API /current-question/)
export interface AttemptQuestion {
  id: number; // ID della Question originale
  quiz?: number; // ID del quiz (opzionale, presente nella risposta)
  text: string;
  // Usa i tipi stringa esatti dal backend se possibile, altrimenti string generico
  question_type: 'MC_SINGLE' | 'MC_MULTI' | 'TF' | 'FILL_BLANK' | 'OPEN_MANUAL' | string;
  question_type_display?: string | null; // Campo display opzionale
  order: number; // Ordine della domanda nel quiz
  metadata?: Record<string, any>; // Metadati generici
  answer_options: AttemptAnswerOption[]; // USA answer_options come da API
}

// Dettagli GENERALI di un tentativo di quiz recuperati dall'API (SENZA domande)
export interface QuizAttemptDetails {
  id: number; // ID del QuizAttempt
  quiz: { // Oggetto Quiz nidificato
    id: number;
    title: string;
    // Aggiungere altri campi del quiz se necessari/disponibili
  };
  status: 'in_progress' | 'completed' | 'failed' | string; // Stato attuale del tentativo (stringa per flessibilità)
  started_at: string; // Timestamp inizio (corretto nome)
  completed_at?: string | null; // Timestamp fine (corretto nome)
  score?: number | null; // Punteggio (se completato)
  // questions: AttemptQuestion[]; // RIMOSSO - L'API /details/ non le restituisce al momento
  // Campi aggiuntivi dal serializer (basati sulla risposta JSON fornita)
  total_questions?: number; // Numero totale domande (utile)
  correct_answers_count?: number;
  completion_threshold?: number | null;
  student_info?: {
    id: number;
    full_name: string;
  };
  given_answers?: any[]; // Array delle risposte date (tipo da definire meglio se serve)
  newly_earned_badges?: any[]; // Badge guadagnati (tipo da definire meglio se serve)
  // Aggiungere altri campi dalla risposta JSON se utili
  student?: number; // ID studente
  quiz_title?: string;
  status_display?: string;
}


// Tipo per la risposta inviata dallo studente
export interface SubmitAnswerPayload {
  attempt_id: number;
  question_id: number;
  selected_option_id?: number | null; // Per multiple choice
  answer_text?: string | null; // Per open ended
}