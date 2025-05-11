export interface Topic {
  id: number;
  name: string;
  subject: number; // ID della materia associata, come da API
  // teacher_id non è solitamente esposto o necessario per la selezione nel frontend
  // created_at, updated_at potrebbero essere utili per debug ma non per la UI di selezione
}