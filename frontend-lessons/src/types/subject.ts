export interface Subject {
  id: number;
  name: string;
  color_placeholder?: string; // Come da design_document.md
  // teacher_id non è solitamente esposto o necessario per la selezione nel frontend
  // created_at, updated_at potrebbero essere utili per debug ma non per la UI di selezione
}