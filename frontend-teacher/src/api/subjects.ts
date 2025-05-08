import apiClient from './config';
import type { AxiosResponse } from 'axios';

// Interfaccia per una Materia (Subject) come restituita dall'API
// Basata su apps.education.serializers.SubjectSerializer
export interface Subject {
  id: number;
  name: string;
  teacher: number; // ID del docente creatore
  color_placeholder?: string | null; // Opzionale, per UI
  created_at?: string;
  updated_at?: string;
  // Aggiungere qui altri campi se il serializer li espone e sono utili
}

// Interfaccia per un Argomento (Topic) come restituito dall'API
// Basata su apps.education.serializers.TopicSerializer
export interface Topic {
  id: number;
  name: string;
  subject: number; // ID della materia di appartenenza
  teacher: number; // ID del docente creatore
  created_at?: string;
  updated_at?: string;
  // Aggiungere qui altri campi se il serializer li espone e sono utili
}

/**
 * Recupera l'elenco delle materie (subjects) create dal docente autenticato.
 */
export const fetchTeacherSubjects = async (): Promise<Subject[]> => {
  try {
    // Aggiornato endpoint in base a fe-lessons
    const response: AxiosResponse<Subject[]> = await apiClient.get('/lezioni/subjects/');
    return response.data;
  } catch (error) {
    console.error('Errore API durante il recupero delle materie del docente:', error);
    throw error;
  }
};

/**
 * Recupera l'elenco degli argomenti (topics) per una specifica materia del docente autenticato.
 * @param subjectId L'ID della materia per cui recuperare gli argomenti.
 */
export const fetchTeacherTopicsForSubject = async (subjectId: number): Promise<Topic[]> => {
  if (!subjectId) {
    // Non dovrebbe accadere se la UI lo gestisce, ma per sicurezza
    return Promise.resolve([]);
  }
  try {
    // Aggiornato endpoint in base a fe-lessons
    const response: AxiosResponse<Topic[]> = await apiClient.get(`/lezioni/topics/?subject_id=${subjectId}`);
    return response.data;
  } catch (error) {
    console.error(`Errore API durante il recupero degli argomenti per la materia ${subjectId}:`, error);
    throw error;
  }
};