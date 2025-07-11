// frontend-student/src/types/education.ts

/**
 * Rappresenta un singolo spazio vuoto (blank) in una domanda fill_blank,
 * come ricevuto dallo studente durante lo svolgimento del quiz.
 * Non include le risposte corrette.
 */
export interface BlankDisplayConfig {
  id: string; // Es. "blank_0"
  order: number; // Indice posizionale
}

/**
 * Metadati specifici per una domanda di tipo 'fill_blank',
 * come ricevuti dallo studente durante lo svolgimento.
 */
export interface QuestionMetadataFillBlankDisplay {
  text_with_placeholders: string; // Es. "Il cielo è {blank_0} e l'erba è {blank_1}."
  blanks: BlankDisplayConfig[]; // Array di configurazioni per gli spazi vuoti
  // case_sensitive e points non sono inviati allo studente durante lo svolgimento
}

/**
 * Struttura di base per una domanda.
 */
export interface BaseQuestion {
  id: number;
  quiz_id: number;
  text: string; // Testo principale della domanda (potrebbe non essere usato direttamente per fill_blank se text_with_placeholders è preferito)
  question_type: string; // Es. "fill_blank", "multiple_choice_single", ecc.
  order: number;
  // metadata sarà più specifico nel tipo esteso
}

/**
 * Rappresenta una domanda di tipo 'fill_blank' completa,
 * come utilizzata dal componente frontend dello studente per il rendering.
 */
export interface QuestionFillBlankDisplay extends BaseQuestion {
  question_type: 'fill_blank';
  metadata: QuestionMetadataFillBlankDisplay;
}

/**
 * Rappresenta la risposta fornita da uno studente per un singolo spazio vuoto.
 */
export interface StudentResponseForBlank {
  blank_id: string; // ID dello spazio vuoto a cui si riferisce la risposta
  student_response: string; // Testo inserito dallo studente
}

/**
 * Rappresenta l'oggetto completo delle risposte fornite dallo studente
 * per una domanda 'fill_blank', pronto per essere inviato al backend.
 */
export interface StudentAnswerPayloadFillBlank {
  answers: StudentResponseForBlank[];
}

// Tipi per la visualizzazione dei risultati (potrebbero includere più dettagli)

/**
 * Rappresenta un singolo spazio vuoto con la risposta corretta,
 * per la visualizzazione dei risultati.
 */
export interface BlankWithCorrectAnswer extends BlankDisplayConfig {
  correct_answers: string[]; // Lista delle risposte corrette
}

/**
 * Metadati di una domanda 'fill_blank' con le risposte corrette,
 * per la visualizzazione dei risultati.
 */
export interface QuestionMetadataFillBlankWithCorrect extends QuestionMetadataFillBlankDisplay {
  blanks: BlankWithCorrectAnswer[];
  case_sensitive: boolean;
  points: number;
}

/**
 * Rappresenta una domanda 'fill_blank' con tutti i dettagli,
 * inclusi le risposte corrette, per la visualizzazione dei risultati.
 */
export interface QuestionFillBlankResult extends BaseQuestion {
  question_type: 'fill_blank';
  metadata: QuestionMetadataFillBlankWithCorrect;
}

/**
 * Risposta dello studente per una domanda fill_blank, come ricevuta dal backend
 * nel riepilogo del quiz.
 */
export interface StudentAnswerResultFillBlank {
  question_id: number;
  selected_answers: StudentAnswerPayloadFillBlank; // Le risposte date dallo studente
  is_correct: boolean;
  score: number | null;
  // Potrebbe includere QuestionFillBlankResult o solo i metadata.blanks con correct_answers
  // come specificato in FILL_BLANK_PLAN.md:105
  // Per ora, assumiamo che il componente di risultato recuperi i dettagli della domanda separatamente
  // o che il backend li fornisca in modo più completo.
  // Aggiungiamo qui la parte di metadata per completezza come da piano.
  question_metadata_for_result_display?: QuestionMetadataFillBlankWithCorrect;
}

/**
 * Tipo generico per una domanda, da utilizzare nei componenti che gestiscono diversi tipi di domande.
 * Si potrebbe usare un discriminated union basato su question_type.
 */
export type AnyQuestionDisplay = QuestionFillBlankDisplay /* | QuestionMultipleChoiceDisplay | ... */;

/**
 * Tipo generico per la risposta di uno studente, da utilizzare nei componenti che gestiscono diversi tipi di risposte.
 */
export type AnyStudentAnswerResult = StudentAnswerResultFillBlank /* | StudentAnswerResultMultipleChoice | ... */;
// --- Tipi per la Revisione dei Tentativi (Senza Correzione) ---

/**
 * Rappresenta un'opzione di risposta come visualizzata durante la revisione.
 * Non include 'is_correct'.
 */
export interface AnswerOptionReview {
  id: number;
  text: string;
  order: number;
  is_correct?: boolean; // Aggiunto per indicare se l'opzione è corretta
}

/**
 * Rappresenta la risposta data dallo studente per una domanda,
 * come visualizzata durante la revisione.
 * Il formato di 'selected_answers' dipende dal question_type.
 */
export interface StudentAnswerReview {
  question_id: number;
  selected_answers: any; // Può essere string, number[], object a seconda del tipo di domanda
  answered_at: string | null;
  is_correct?: boolean; // Aggiunto per indicare se la risposta data è corretta
  teacher_comment?: string | null; // Aggiunto per il feedback del docente
}

/**
 * Rappresenta una domanda come visualizzata durante la revisione.
 * Include le opzioni (senza indicazione di correttezza) e la risposta data dallo studente.
 */
export interface QuestionReview {
  id: number;
  text: string;
  question_type: string; // Es. "multiple_choice_single", "fill_blank", "true_false"
  question_type_display: string;
  order: number;
  metadata?: any; // Metadati specifici della domanda (es. per fill_blank)
  answer_options?: AnswerOptionReview[]; // Opzionale, non per tutti i tipi di domanda
  student_answer: StudentAnswerReview | null; // La risposta data dallo studente a QUESTA domanda in QUESTO tentativo
}

/**
 * Rappresenta i dati completi di un tentativo di quiz per la revisione.
 */
export interface QuizAttemptReviewData {
  id: number; // Attempt ID
  quiz_id: number; // Corrisponde a QuizAttempt.quiz.id
  quiz_title: string;
  status: string; // Es. "COMPLETED", "FAILED"
  score: number | null;
  // points_earned: number | null; // Rimosso per coerenza con il backend
  started_at: string | null;
  completed_at: string | null;
  student: { // Informazioni base sullo studente
    id: number;
    user_id?: number; // ID dell'utente Django associato al docente dello studente
    first_name: string;
    last_name: string;
    unique_identifier?: string;
  };
  questions: QuestionReview[]; // Elenco delle domande con le risposte date
}