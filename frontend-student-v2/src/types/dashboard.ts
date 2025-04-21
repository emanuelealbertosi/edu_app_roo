// src/types/dashboard.ts

// Tipo per un Quiz assegnato (ipotizzato)
export interface AssignedQuiz {
  id: number;
  quiz_template_id: number; // ID del template originale
  title: string;
  description?: string;
  status: 'pending' | 'not_started' | 'in_progress' | 'completed' | 'failed'; // Stato del tentativo dello studente
  assigned_date: string; // Data assegnazione (formato ISO string)
  deadline?: string | null; // Eventuale scadenza
  best_score?: number | null; // Miglior punteggio ottenuto
  attempts_made?: number; // Tentativi fatti
  max_attempts?: number | null; // Tentativi massimi
  // Potrebbero esserci altri campi come 'subject', 'difficulty', etc.
}

// Tipo per un Percorso assegnato (ipotizzato)
export interface AssignedPathway {
  id: number;
  pathway_template_id: number; // ID del template originale
  title: string;
  description?: string;
  status: 'pending' | 'not_started' | 'in_progress' | 'completed'; // Stato del percorso per lo studente
  assigned_date: string; // Data assegnazione
  deadline?: string | null; // Eventuale scadenza
  progress_percentage?: number; // Percentuale completamento
  // Potrebbero esserci altri campi
}

// Tipo per il Wallet dello studente (ipotizzato)
export interface Wallet {
  student_id: number;
  current_points: number;
  last_updated: string; // Data ultimo aggiornamento
  // Potrebbero esserci altri campi relativi a transazioni o altro
}

// Tipo combinato per i dati della dashboard (anche se fetchati separatamente)
export interface DashboardData {
  assignedQuizzes: AssignedQuiz[];
  assignedPathways: AssignedPathway[];
  wallet: Wallet | null;
}