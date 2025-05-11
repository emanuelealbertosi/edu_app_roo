export interface QuizTemplate {
  id: number;
  admin_id?: number; // Se creato da admin
  teacher_id?: number; // Se i docenti possono creare template locali (da verificare se supportato)
  title: string;
  description?: string | null;
  subject_id?: number | null;
  topic_id?: number | null;
  subject_name?: string | null; // Denormalizzato per la visualizzazione
  topic_name?: string | null;   // Denormalizzato per la visualizzazione
  metadata?: any; // Es: { difficulty: 'medium' }
  created_at: string;
  updated_at?: string; // Spesso presente
  image_url?: string | null; // Coerenza con Quiz, se i template possono avere immagini
  subject_color_placeholder?: string | null; // Coerenza con Quiz
  questions_count?: number; // Utile per dare un'idea del template
}