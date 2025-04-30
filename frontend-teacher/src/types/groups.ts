// frontend-teacher/src/types/groups.ts

/**
 * Rappresenta uno studente membro di un gruppo,
 * come restituito dall'API (es. /api/groups/{id}/students/).
 */
export interface GroupMember {
  id: number; // CORRETTO: Usa 'id' come restituito da StudentBasicSerializer
  student_code?: string; // Aggiunto per coerenza con StudentBasicSerializer (opzionale)
  first_name: string;
  last_name: string;
  // Potremmo aggiungere l'email o l'identificativo unico se necessario
  joined_at: string; // Data di aggiunta al gruppo (ISO string)
}

/**
 * Rappresenta un gruppo di studenti.
 */
export interface StudentGroup {
  id: number;
  name: string;
  description: string | null;
  registration_link: string | null; // Sostituito token con link
  created_at: string; // ISO date string
  is_active: boolean;
  student_count?: number; // Numero di studenti nel gruppo (opzionale, utile per le liste)
  is_public?: boolean; // Indica se il gruppo è pubblico
  // owner_id?: number; // Rimosso: il backend restituisce 'owner' con l'ID
  owner: number; // ID del docente proprietario (restituito dal backend)
  owner_name?: string; // Nome del docente proprietario (opzionale, per UI)
  pending_requests_count?: number | null; // Numero di richieste pendenti (solo per owner)
  qr_code_base64?: string | null; // QR code del link di registrazione (se generato)
  // teacher_id non è necessario se l'API è già filtrata per il docente loggato
  // students: GroupMember[]; // Potrebbe essere caricato separatamente nella vista dettaglio
}

/**
 * Dati necessari per creare o aggiornare un gruppo.
 */
export interface StudentGroupData {
  name: string;
  description?: string | null;
  is_active?: boolean; // Generalmente gestito separatamente o al momento della creazione
  is_public?: boolean; // Campo per creare/aggiornare lo stato pubblico
}

/**
 * Dati per aggiungere uno studente a un gruppo.
 * Potrebbe essere l'ID dello studente o un identificativo unico.
 */
export interface AddStudentToGroupData {
    student_id: number; // O un altro identificatore come 'unique_identifier'
}

/**
 * Rappresenta lo stato di una richiesta di accesso.
 */
export type GroupAccessStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

/**
 * Rappresenta una richiesta di accesso a un gruppo.
 */
export interface GroupAccessRequest {
  id: number;
  group: number; // ID del gruppo richiesto
  group_name?: string; // Nome del gruppo (opzionale, per UI)
  requesting_teacher: number; // ID del docente richiedente
  requesting_teacher_name?: string; // Nome del docente richiedente (opzionale, per UI) - Assicuriamoci che sia presente
  owner_teacher?: number; // ID del docente proprietario (opzionale, per UI)
  owner_teacher_name?: string; // Nome del docente proprietario (opzionale, per UI)
  status: GroupAccessStatus;
  requested_at: string; // ISO date string (Corretto da created_at)
  responded_at: string | null; // ISO date string
}

/**
 * Dati necessari per creare una richiesta di accesso.
 */
export interface GroupAccessRequestData {
    group: number; // ID del gruppo a cui si richiede accesso
}

/**
 * Dati necessari per rispondere a una richiesta di accesso.
 */
export interface RespondGroupAccessRequestData {
    approve: boolean; // true per approvare, false per rifiutare
}

/**
 * Rappresenta la risposta dell'API per la generazione del token.
 */
export interface GenerateTokenResponse {
  registration_link: string;
  qr_code_base64: string; // Immagine QR code codificata in Base64
}