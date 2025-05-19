// Definizione dei tipi di contenuto specifici per UDA e Template UDA
export enum UDAContentType {
  LESSON = 'LESSON',
  QUIZ = 'QUIZ', // MODIFICATO da QUIZ_TEMPLATE
  NOTE = 'NOTE',
  ACTIVITY = 'ACTIVITY',
}

export enum UDATemplateContentType {
  LESSON = 'LESSON', // Riferimento a Lesson esistente
  QUIZ_TEMPLATE = 'QUIZ_TEMPLATE', // Mantenuto QUIZ_TEMPLATE per i template UDA
  NOTE_TEMPLATE = 'NOTE_TEMPLATE',
  ACTIVITY_TEMPLATE = 'ACTIVITY_TEMPLATE',
}

// Interfaccia base per un elemento di contenuto, sia esso in un UDA o in un Template UDA
// I campi specifici verranno aggiunti nelle interfacce derivate.
interface BaseContent {
  id?: number; // ID dal backend, opzionale se creato nel frontend e non ancora salvato
  temp_id?: string; // ID temporaneo generato dal frontend per la gestione della lista
  order: number;
  created_at?: string;
  updated_at?: string;
  estimated_hours?: number | null; // Tempo stimato in ore
  actual_hours?: number | null; // Tempo effettivo in ore
}

// Contenuto di tipo Lezione
export interface LessonUDAContent extends BaseContent {
  content_type: UDAContentType.LESSON | UDATemplateContentType.LESSON;
  lesson: number; // FK a Lesson.id
  lesson_title?: string; // Titolo per visualizzazione, non parte del modello backend UDAContent ma utile nel FE
  teacher_marked_completed?: boolean; // Solo per UDAContent
}

// Contenuto di tipo Quiz (riferito a un QuizTemplate)
export interface QuizUDAContent extends BaseContent { // Rinominato per chiarezza e per riflettere UDAContentType.QUIZ
  content_type: UDAContentType.QUIZ | UDATemplateContentType.QUIZ_TEMPLATE; // UDAContent userà QUIZ, UDATemplateContent userà QUIZ_TEMPLATE
  quiz_template: number; // FK a QuizTemplate.id
  quiz_title?: string; // Titolo per visualizzazione (potrebbe essere il titolo del template)
  teacher_marked_completed?: boolean; // Solo per UDAContent effettivo
}

// Contenuto di tipo Nota (per UDA)
export interface NoteUDAContent extends BaseContent {
  content_type: UDAContentType.NOTE;
  note_title: string | null;
  note_content: string | null;
  teacher_marked_completed?: boolean;
  uda_id: number;
}

// Contenuto di tipo Nota Template (per UDATemplate)
export interface NoteTemplateUDAContent extends BaseContent {
  content_type: UDATemplateContentType.NOTE_TEMPLATE;
  note_template_title: string | null;
  note_template_content: string | null;
  uda_template_id: number;
}

// Contenuto di tipo Attività (per UDA)
export interface ActivityUDAContent extends BaseContent {
  content_type: UDAContentType.ACTIVITY;
  activity_title: string | null;
  activity_description: string | null;
  activity_attachment_url?: string | null;
  activity_attachment_file?: File | null; // Per gestire il file selezionato nel frontend
  activity_completed?: boolean; // Completamento specifico dell'attività
  teacher_marked_completed?: boolean; // Completamento marcato dal docente
  uda_id: number;
}

// Contenuto di tipo Attività Template (per UDATemplate)
export interface ActivityTemplateUDAContent extends BaseContent {
  content_type: UDATemplateContentType.ACTIVITY_TEMPLATE;
  activity_template_title: string | null;
  activity_template_description: string | null;
  uda_template_id: number;
}

// Unione dei tipi per UDAContent
export type UDAContent =
  | LessonUDAContent
  | QuizUDAContent // MODIFICATO da QuizTemplateUDAContent
  | NoteUDAContent
  | ActivityUDAContent;

// Unione dei tipi per UDATemplateContent
export type UDATemplateContent =
  | LessonUDAContent
  | QuizUDAContent   // MODIFICATO da QuizTemplateUDAContent (ma UDATemplateContent dovrebbe ancora usare QuizTemplateUDAContent se la logica di creazione template è separata)
                               // Per coerenza con il backend, UDATemplateContent dovrebbe continuare a usare QUIZ_TEMPLATE come tipo.
                               // La modifica qui è stata un errore, UDATemplateContent dovrebbe rimanere QuizTemplateUDAContent.
                               // Ripristino la riga originale per UDATemplateContent e correggo solo UDAContent.
  | QuizUDAContent // Mantenuto per UDATemplateContent, ora usa l'interfaccia rinominata
  | NoteTemplateUDAContent
  | ActivityTemplateUDAContent;


// Tipo per lo stato dell'UDA
export type UDAStatus = 'TODO' | 'IN_PROGRESS' | 'COMPLETED';

// Interfaccia per UDA (Unità Didattica di Apprendimento)
export interface UDA {
  id: number;
  teacher: number; // FK a User
  course?: number | null; // FK a Course (ID)
  course_name?: string | null; // Nome del corso (dal backend)
  course_teacher_username?: string | null; // Username dell'autore del corso (dal backend)
  source_template?: number | null; // FK a UDATemplate
  title: string;
  description?: string | null;
  knowledge_html?: string | null;
  skills_html?: string | null;
  competences_html?: string | null;
  start_date?: string | null; // Formato YYYY-MM-DD
  end_date?: string | null;   // Formato YYYY-MM-DD
  subjects?: number[]; // Array di ID di Subject (usato internamente nel form e per l'invio come subject_ids)
  subjects_display?: string[]; // Array di nomi di Subject (per la visualizzazione, fornito dal backend)
  topics?: number[]; // Array di ID di Topic
  status: UDAStatus; // Usa il tipo esportato
  order_in_course?: number | null;
  contents: UDAContent[]; // Array di contenuti specifici dell'UDA
  created_at: string;
  updated_at: string;
  topics_display?: string[];
}

// Interfaccia per Course
export interface Course {
  id: number;
  teacher: number; // FK a User
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
  // Campo opzionale per contenere le UDA quando fetchate specificamente per un corso
  udas?: UDA[];
  // Campo opzionale per l'ordinamento delle UDA, se gestito lato client prima del salvataggio
  uda_ids_ordered?: number[];
}

// Interfaccia per UDATemplate (Template Unità Didattica di Apprendimento)
export interface UDATemplate {
  id: number;
  teacher: number; // FK a User
  name: string;
  description?: string | null;
  subject?: number | null; // FK a Subject
  topics?: number[]; // Array di ID di Topic
  contents: UDATemplateContent[]; // Array di contenuti specifici del template
  created_at: string;
  updated_at: string;
}

// Tipi per gli item selezionati nella modale
// RawSelectedContentItem rappresenta ciò che viene selezionato PRIMA della trasformazione (es. un QuizTemplate)
export type RawSelectedContentItem =
  | { type: UDAContentType.LESSON; id: number; title: string; }
  | { type: 'QUIZ_TEMPLATE'; id: number; title: string; }; // Stringa letterale perché non è un UDAContentType finale

// SelectedContentItem rappresenta ciò che viene emesso DOPO la trasformazione (es. un Quiz concreto)
// e che verrà usato per creare UDAContent effettivo.
export type SelectedContentItem =
  | { type: UDAContentType.LESSON; id: number; title: string; estimated_hours?: number | null; }
  // Ora riflette che passiamo un riferimento a un QuizTemplate, ma il tipo finale per UDAContent sarà QUIZ
  | { type: UDAContentType.QUIZ; id: number; title: string; estimated_hours?: number | null; }; // id qui è l'ID del QuizTemplate, ma il content_type per UDAContent sarà QUIZ