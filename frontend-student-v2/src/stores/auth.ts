import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios' // Assicurati che axios sia installato

// Definisci un tipo per l'utente (opzionale ma buona pratica)
// Aggiorna l'interfaccia per riflettere i dati dello studente restituiti dal backend
interface Student {
  id: number;
  student_code: string;
  first_name: string;
  last_name: string;
  teacher: number; // ID del docente
  group: number | null; // ID del gruppo (può essere null)
  // Aggiungi altri campi rilevanti restituiti da StudentSerializer se necessario
}

export const useAuthStore = defineStore('auth', () => {
  // Stato
  const token = ref<string | null>(localStorage.getItem('authToken') || null) // Carica il token dal localStorage se esiste
  const user = ref<Student | null>(null) // Inizialmente nessun studente loggato
  const isAuthenticated = ref<boolean>(!!token.value) // Vero se c'è un token
  const loginError = ref<string | null>(null) // Per memorizzare errori di login

  // Azioni
  // Modifica la firma per accettare student_code e pin
  async function login(student_code: string, pin: string): Promise<boolean> {
    loginError.value = null // Resetta l'errore precedente
    try {
      // --- IMPORTANTE ---
      // Usa l'endpoint corretto e invia student_code e pin
      // Aggiorna il tipo di risposta atteso
      const response = await axios.post<{ access: string; refresh: string; student: Student }>(
        '/api/student/auth/student/login/',
        {
          student_code,
          pin
        }
      )

      const newToken = response.data.access;
      token.value = newToken;
      isAuthenticated.value = true;
      localStorage.setItem('authToken', newToken); // Salva il token di accesso

      // Salva i dati dello studente restituiti direttamente dalla risposta di login
      user.value = response.data.student;
      // Salva l'utente nel localStorage dopo un login riuscito
      localStorage.setItem('authUser', JSON.stringify(user.value));

      // Potremmo voler salvare anche il refresh token se necessario per rinnovare la sessione
      // localStorage.setItem('refreshToken', response.data.refresh);

      console.log('Login successful, token stored.')
      return true // Indica successo

    } catch (error: any) {
      console.error('Login failed:', error)
      isAuthenticated.value = false
      token.value = null
      user.value = null
      localStorage.removeItem('authToken'); // Rimuovi token non valido
      localStorage.removeItem('authUser'); // Rimuovi anche l'utente in caso di fallimento

      if (axios.isAxiosError(error) && error.response) {
        // Gestisci errori specifici dell'API (es. 401 Unauthorized)
        if (error.response.status === 401) {
          loginError.value = 'Codice studente o PIN non validi.' // Messaggio più specifico
        } else {
          loginError.value = `Errore API: ${error.response.status} - ${error.response.data?.detail || error.message}`
        }
      } else {
        loginError.value = 'Errore durante il login. Riprova più tardi.'
      }
      return false // Indica fallimento
    }
  }

  function logout() {
    token.value = null
    user.value = null
    isAuthenticated.value = false
    loginError.value = null
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser'); // Rimuovi utente al logout
    // Qui potresti voler reindirizzare alla pagina di login
    // router.push('/login'); // Assicurati che 'router' sia accessibile qui se necessario
    console.log('User logged out.')
  }

  // Logica per caricare l'utente da localStorage all'avvio dello store
  // Viene eseguita solo se esiste un token valido
  if (token.value) {
    const storedUser = localStorage.getItem('authUser');
    if (storedUser) {
      try {
        const parsedUser: Student = JSON.parse(storedUser);
        // Verifica minima che l'oggetto parsato abbia le proprietà attese
        if (parsedUser && parsedUser.id && parsedUser.student_code) {
            user.value = parsedUser;
            isAuthenticated.value = true; // Assicurati che lo stato sia coerente
            console.log('User data loaded from localStorage.');
        } else {
            throw new Error("Parsed user data is invalid");
        }
      } catch (e) {
        console.error("Failed to parse or validate stored user data:", e);
        // Se i dati non sono validi o c'è un errore, pulisci tutto per sicurezza
        localStorage.removeItem('authUser');
        localStorage.removeItem('authToken');
        token.value = null;
        user.value = null;
        isAuthenticated.value = false;
      }
    } else {
        // Se c'è un token ma non un utente salvato, consideriamo l'utente non completamente loggato
        // Potrebbe essere uno stato intermedio o un errore precedente.
        // Per semplicità, forziamo il logout per richiedere un nuovo login.
        console.warn("Auth token found but no user data in localStorage. Forcing logout.");
        logout(); // Chiama la funzione logout definita sopra
    }
  } else {
      // Se non c'è token all'avvio, assicurati che non ci sia utente salvato
      localStorage.removeItem('authUser');
      user.value = null;
      isAuthenticated.value = false;
  }


  return {
    token,
    user,
    isAuthenticated,
    loginError,
    login,
    logout,
    // fetchUser è stato rimosso correttamente
  }
})