import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

// Interfaccia unificata per i dati utente essenziali
// Indipendentemente da Studente o Docente/Admin
export interface SharedUser { // Aggiunto export
  id: number; // ID utente (dal modello User o Student)
  username?: string; // Presente per Teacher/Admin
  student_code?: string; // Presente per Student
  first_name: string;
  last_name: string;
  email?: string; // Presente per Teacher/Admin
  role: 'STUDENT' | 'TEACHER' | 'ADMIN' | null; // Ruolo unificato
}

// Nome univoco per lo store condiviso
export const useSharedAuthStore = defineStore('sharedAuth', () => {
  // --- State ---
  const user = ref<SharedUser | null>(null);
  const accessToken = ref<string | null>(null);
  const refreshToken = ref<string | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // State per la comunicazione con l'iframe
  const lessonsIframeReady = ref(false);
  let pendingAuthDataToSend: { type: 'AUTH_STATE_UPDATED', payload: any } | { type: 'AUTH_STATE_CLEARED' } | null = null;


  // --- Getters (Computed) ---
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value);
  const userRole = computed(() => user.value?.role || null)
  const userId = computed(() => user.value?.id || null)

  // --- Actions ---

  /**
   * Imposta i dati di autenticazione nello store e in localStorage.
   * @param access - Access Token JWT
   * @param refresh - Refresh Token JWT
   * @param userData - Dati utente conformi a SharedUser
   */
  function setAuthData(access: string, refresh: string | null, userData: SharedUser) {
    console.log('[SharedAuthStore] Setting auth data (Pinia state):', { access: access ? 'TOKEN_PRESENT' : 'null', refresh: refresh ? 'TOKEN_PRESENT' : 'null', user: userData });
    accessToken.value = access;
    refreshToken.value = refresh;
    user.value = userData;
    error.value = null; // Resetta errori precedenti

    // Assicurati che userData sia un oggetto semplice se proviene da un proxy reattivo
    const plainUserData = userData ? JSON.parse(JSON.stringify(userData)) : null;
    const stateToPersist = {
      user: plainUserData,
      accessToken: access,
      refreshToken: refresh,
      loading: loading.value, // Booleano, OK
      error: error.value     // Stringa o null, OK
    };

    try {
      localStorage.setItem('sharedAuth', JSON.stringify(stateToPersist));
      console.log('[SharedAuthStore WORKAROUND] Dati scritti manualmente in localStorage per "sharedAuth":', JSON.stringify(stateToPersist));

      // Non inviare più postMessage direttamente da setAuthData.
      // L'invio avverrà quando l'iframe segnala di essere pronto.
      // Memorizziamo solo che i dati sono cambiati, se necessario, o ci affidiamo
      // al fatto che l'iframe chiederà o che lo stato verrà inviato al momento giusto.
      // Per ora, la logica di invio quando l'iframe è pronto gestirà questo.
      console.log('[SharedAuthStore] Dati auth impostati. L\'invio all\'iframe avverrà al segnale di prontezza dell\'iframe.');
      // Se l'iframe è già pronto, potremmo voler inviare subito.
      // Ma questo potrebbe accadere prima che l'iframe sia visibile se il login avviene altrove.
      // La logica attuale di invio su IFRAME_READY_FOR_AUTH dovrebbe coprire il caso.
      // Se `lessonsIframeReady.value` è true qui, significa che l'handshake è già avvenuto.
      // Potrebbe essere sicuro inviare, ma attendere il caricamento della vista iframe è più robusto.
      // Per ora, manteniamo l'invio solo in risposta a IFRAME_READY_FOR_AUTH
      // e quando pendingAuthDataToSend viene processato.
      // Modifichiamo pendingAuthDataToSend per riflettere lo stato più recente.
      pendingAuthDataToSend = { type: 'AUTH_STATE_UPDATED' as const, payload: stateToPersist };

    } catch (e) {
      console.error('[SharedAuthStore WORKAROUND] Errore scrivendo in localStorage:', e);
    }
  }

  /**
   * Pulisce i dati di autenticazione dallo store e da localStorage.
   */
  function clearAuthData() {
    console.log('[SharedAuthStore] Clearing auth data (Pinia state).');
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;

    const clearedState = {
      user: null,
      accessToken: null,
      refreshToken: null,
      loading: false,
      error: null
    };
    try {
      localStorage.setItem('sharedAuth', JSON.stringify(clearedState));
      console.log('[SharedAuthStore WORKAROUND] Dati rimossi/resettati manualmente in localStorage per "sharedAuth".');

      // Non inviare più postMessage direttamente da clearAuthData.
      console.log('[SharedAuthStore] Dati auth puliti. L\'invio all\'iframe avverrà al segnale di prontezza dell\'iframe.');
      pendingAuthDataToSend = { type: 'AUTH_STATE_CLEARED' as const };
    } catch (e) {
      console.error('[SharedAuthStore WORKAROUND] Errore pulendo localStorage:', e);
    }
  }

  /**
   * Imposta lo stato di caricamento.
   * @param value - true se in caricamento, false altrimenti
   */
  function setLoading(value: boolean) {
    loading.value = value;
  }

   /**
   * Imposta un messaggio di errore.
   * @param message - Messaggio di errore
   */
  function setError(message: string | null) {
    error.value = message;
  }

  /**
   * Logica di inizializzazione (opzionale):
   * Potrebbe tentare di recuperare il ruolo o verificare il token all'avvio.
   * Per ora, lasciamo che gli store specifici gestiscano l'inizializzazione.
   */
  // function initialize() {
  //   if (accessToken.value) {
  //     // Potrebbe provare a decodificare il token per ottenere il ruolo
  //     // o chiamare un endpoint /me generico se esistesse.
  //   }
  // }
  // initialize();

  function sendAuthMessageToIframe(message: { type: 'AUTH_STATE_UPDATED', payload: any } | { type: 'AUTH_STATE_CLEARED' }) {
    const lessonsIframe = document.getElementById('lessons-iframe') as HTMLIFrameElement;
    const lessonsOrigin = import.meta.env.VITE_LESSONS_APP_URL_ORIGIN || new URL(import.meta.env.VITE_LESSONS_APP_URL).origin;

    if (lessonsIframe && lessonsIframe.contentWindow) {
      lessonsIframe.contentWindow.postMessage(message, lessonsOrigin);
      console.log(`[SharedAuthStore] Messaggio ${message.type} inviato all'iframe lessons.`);
    } else {
      console.warn(`[SharedAuthStore] Iframe "lessons-iframe" non trovato, impossibile inviare ${message.type}. Questo non dovrebbe accadere se lessonsIframeReady è true.`);
    }
  }

  // Listener per messaggi dall'iframe
  // NOTA: Idealmente, questo listener dovrebbe essere gestito a livello di componente App.vue
  // per un corretto cleanup (removeEventListener). Metterlo qui è una semplificazione.
  if (typeof window !== 'undefined') {
    const messageListener = (event: MessageEvent) => {
      // Determina l'origine attesa dell'iframe (frontend-lessons)
      let expectedLessonsOrigin = '';
      try {
        // VITE_LESSONS_APP_URL dovrebbe essere l'URL completo di frontend-lessons, es. http://localhost:5173
        const lessonsAppUrl = import.meta.env.VITE_LESSONS_APP_URL as string;
        if (lessonsAppUrl) {
          expectedLessonsOrigin = new URL(lessonsAppUrl).origin;
        } else {
          console.error('[SharedAuthStore] VITE_LESSONS_APP_URL non è definito. Impossibile verificare l\'origine dei messaggi dall\'iframe.');
          return; // Non possiamo procedere in modo sicuro senza l'URL dell'iframe
        }
      } catch (e) {
        console.error('[SharedAuthStore] Errore nel parsare VITE_LESSONS_APP_URL per l\'origine:', e);
        return; // Non possiamo procedere in modo sicuro
      }

      if (event.origin !== expectedLessonsOrigin) {
        // console.warn(`[SharedAuthStore] Messaggio da origine non fidata ignorato: ${event.origin}. Attesa: ${expectedLessonsOrigin}`);
        return;
      }

      if (event.data && event.data.type === 'IFRAME_READY_FOR_AUTH') {
        console.log('[SharedAuthStore] Ricevuto IFRAME_READY_FOR_AUTH da lessons iframe.');
        lessonsIframeReady.value = true;
        if (pendingAuthDataToSend) { // Se c'era un messaggio in attesa (es. da un login precedente)
          console.log('[SharedAuthStore] Invio dati di autenticazione accodati (pending) all\'iframe.');
          sendAuthMessageToIframe(pendingAuthDataToSend);
          pendingAuthDataToSend = null;
        } else {
          // L'iframe è pronto, invia lo stato di autenticazione corrente.
          // Questo copre il caso in cui l'utente naviga alla pagina dell'iframe
          // dopo essersi già autenticato.
          console.log('[SharedAuthStore] Iframe pronto. Invio stato di autenticazione corrente.');
          // Assicurati di inviare dati clonabili
          if (isAuthenticated.value && user.value && accessToken.value) {
            const plainUser = JSON.parse(JSON.stringify(user.value)); // "Spacchetta" il proxy
            const currentAuthPayload = {
              user: plainUser,
              accessToken: accessToken.value, // Stringa o null, OK
              refreshToken: refreshToken.value, // Stringa o null, OK
              loading: loading.value, // Booleano, OK
              error: error.value // Stringa o null, OK
            };
            sendAuthMessageToIframe({ type: 'AUTH_STATE_UPDATED', payload: currentAuthPayload });
          } else {
            sendAuthMessageToIframe({ type: 'AUTH_STATE_CLEARED' });
          }
        }
      }
    };
    window.addEventListener('message', messageListener);
    // Considera di aggiungere una funzione per rimuovere il listener se lo store viene distrutto,
    // anche se per gli store Pinia globali di solito non è un problema.
  }


  return {
    // State
    user,
    accessToken,
    refreshToken,
    loading,
    error,
    lessonsIframeReady, // Esporre per debug o usi futuri se necessario

    // Getters
    isAuthenticated,
    userRole,
    userId,

    // Actions
    setAuthData,
    clearAuthData,
    setLoading,
    setError
  }
}, {
  persist: true
})