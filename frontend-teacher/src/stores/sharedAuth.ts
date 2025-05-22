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
  can_create_public_groups?: boolean; // Permesso specifico per Docenti/Admin
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
    console.log('[SharedAuthStore Teacher] Setting auth data (Pinia state):', { access: access ? 'TOKEN_PRESENT' : 'null', refresh: refresh ? 'TOKEN_PRESENT' : 'null', user: userData });
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
    
    // Scrittura manuale in localStorage per coerenza con frontend-student e per debug immediato
    // pinia-plugin-persistedstate dovrebbe comunque gestirlo.
    try {
        localStorage.setItem('sharedAuth', JSON.stringify(stateToPersist));
        console.log('[SharedAuthStore Teacher WORKAROUND] Dati scritti manualmente in localStorage per "sharedAuth":', JSON.stringify(stateToPersist));
    } catch (e) {
        console.error('[SharedAuthStore Teacher WORKAROUND] Errore scrivendo in localStorage:', e);
    }

    console.log('[SharedAuthStore Teacher] Dati auth impostati. L\'invio all\'iframe avverrà al segnale di prontezza dell\'iframe.');
    pendingAuthDataToSend = { type: 'AUTH_STATE_UPDATED' as const, payload: stateToPersist };
    // Se l'iframe è già pronto (improbabile qui, ma per sicurezza), invia subito.
    // Questo è più rilevante se setAuthData fosse chiamato DOPO che l'iframe è pronto.
    if (lessonsIframeReady.value) {
        console.log('[SharedAuthStore Teacher] Iframe già pronto, invio AUTH_STATE_UPDATED.');
        sendAuthMessageToIframe(pendingAuthDataToSend);
        pendingAuthDataToSend = null;
    }
  }

  /**
   * Pulisce i dati di autenticazione dallo store e da localStorage.
   */
  function clearAuthData() {
    console.log('[SharedAuthStore Teacher] Clearing auth data (Pinia state).');
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
        console.log('[SharedAuthStore Teacher WORKAROUND] Dati rimossi/resettati manualmente in localStorage per "sharedAuth".');
    } catch (e) {
        console.error('[SharedAuthStore Teacher WORKAROUND] Errore pulendo localStorage:', e);
    }

    console.log('[SharedAuthStore Teacher] Dati auth puliti. L\'invio all\'iframe avverrà al segnale di prontezza dell\'iframe.');
    pendingAuthDataToSend = { type: 'AUTH_STATE_CLEARED' as const };
    if (lessonsIframeReady.value) {
        console.log('[SharedAuthStore Teacher] Iframe già pronto, invio AUTH_STATE_CLEARED.');
        sendAuthMessageToIframe(pendingAuthDataToSend);
        pendingAuthDataToSend = null;
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
    // Tenta di trovare l'iframe. L'ID potrebbe variare se ci sono più tipi di iframe.
    // Per ora, assumiamo un ID generico o che la vista imposti un ID standard come 'lessons-iframe'.
    // Se si usano ID diversi per iframe (es. 'teacher-lessons-iframe-subjects'), questa logica
    // o quella nella vista embedded necessita di coordinamento.
    // Per semplicità, usiamo 'lessons-iframe' come ID standard che le viste embedded dovrebbero usare.
    const lessonsIframe = document.getElementById('lessons-iframe') as HTMLIFrameElement ||
                          document.getElementById('teacher-lessons-iframe-subjects') as HTMLIFrameElement; // Aggiungi altri ID se necessario

    let lessonsOrigin = '';
    try {
        const appUrl = import.meta.env.VITE_LESSONS_APP_URL as string;
        if (appUrl && appUrl.startsWith('http')) {
            lessonsOrigin = new URL(appUrl).origin;
        } else {
            console.error('[SharedAuthStore Teacher] VITE_LESSONS_APP_URL non è un URL http valido o non è definito. Impossibile inviare postMessage in modo sicuro.');
            return;
        }
    } catch(e) {
        console.error('[SharedAuthStore Teacher] Errore nel parsare VITE_LESSONS_APP_URL:', e);
        return;
    }

    if (lessonsIframe && lessonsIframe.contentWindow) {
      lessonsIframe.contentWindow.postMessage(message, lessonsOrigin);
      console.log(`[SharedAuthStore Teacher] Messaggio ${message.type} inviato all'iframe lessons (ID: ${lessonsIframe.id}).`);
    } else {
      console.warn(`[SharedAuthStore Teacher] Iframe con ID cercati non trovato, o contentWindow non disponibile. Impossibile inviare ${message.type}. Questo non dovrebbe accadere se lessonsIframeReady è true e l'iframe è nel DOM.`);
    }
  }

  if (typeof window !== 'undefined') {
    const messageListener = (event: MessageEvent) => {
      let expectedLessonsOrigin = '';
      try {
        const appUrl = import.meta.env.VITE_LESSONS_APP_URL as string;
        if (appUrl && appUrl.startsWith('http')) {
          expectedLessonsOrigin = new URL(appUrl).origin;
        } else {
          console.error('[SharedAuthStore Teacher] VITE_LESSONS_APP_URL non è definito o non è un URL http. Impossibile verificare l\'origine dei messaggi dall\'iframe.');
          return;
        }
      } catch (e) {
        console.error('[SharedAuthStore Teacher] Errore nel parsare VITE_LESSONS_APP_URL per l\'origine:', e);
        return;
      }

      if (event.origin !== expectedLessonsOrigin) {
        return;
      }

      if (event.data && event.data.type === 'IFRAME_READY_FOR_AUTH') {
        console.log('[SharedAuthStore Teacher] Ricevuto IFRAME_READY_FOR_AUTH da lessons iframe.');
        lessonsIframeReady.value = true;
        if (pendingAuthDataToSend) {
          console.log('[SharedAuthStore Teacher] Invio dati di autenticazione accodati (pending) all\'iframe.');
          sendAuthMessageToIframe(pendingAuthDataToSend);
          pendingAuthDataToSend = null;
        } else {
          console.log('[SharedAuthStore Teacher] Iframe pronto. Invio stato di autenticazione corrente.');
          if (isAuthenticated.value && user.value && accessToken.value) {
            const plainUser = JSON.parse(JSON.stringify(user.value));
            const currentAuthPayload = {
              user: plainUser,
              accessToken: accessToken.value,
              refreshToken: refreshToken.value,
              loading: loading.value,
              error: error.value
            };
            sendAuthMessageToIframe({ type: 'AUTH_STATE_UPDATED', payload: currentAuthPayload });
          } else {
            sendAuthMessageToIframe({ type: 'AUTH_STATE_CLEARED' });
          }
        }
      }
    };
    window.addEventListener('message', messageListener);
  }

  return {
    user,
    accessToken,
    refreshToken,
    loading,
    error,
    lessonsIframeReady,
    isAuthenticated,
    userRole,
    userId,
    setAuthData,
    clearAuthData,
    setLoading,
    setError
  }
}, { persist: true })