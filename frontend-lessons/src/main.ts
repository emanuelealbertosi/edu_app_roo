import { createApp } from 'vue'
import { createPinia } from 'pinia' // Importa Pinia
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate' // Importa il plugin
import router from './router' // Importa il router
import './index.css' // Importa gli stili Tailwind
import './style.css' // Importa i nostri stili personalizzati
import App from './App.vue'
import { useAuthStore } from '@/stores/auth'; // Importa l'auth store
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa sharedAuthStore per l'event listener

// Crea l'istanza dell'app Vue
const app = createApp(App)

// Crea l'istanza di Pinia
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate) // Usa il plugin

// Usa Pinia e il Router nell'app
app.use(pinia) // Usa l'istanza Pinia configurata

// Dopo aver usato Pinia, possiamo istanziare gli store
const authStore = useAuthStore(); // authStore deve essere disponibile globalmente nel modulo
let activeHostWindow: MessageEventSource | null = null;
let activeHostOrigin: string | null = null;

// Controlla lo stato di autenticazione iniziale
// È importante farlo prima di montare l'app e prima della navigazione iniziale
// per assicurarsi che le guardie di navigazione abbiano lo stato corretto.
const initializeApp = async () => {
  try {
    await authStore.checkInitialAuth();
    console.log('[Main.ts] checkInitialAuth completato.');
  } catch (error) {
    console.error("[Main.ts] Errore durante il checkInitialAuth:", error);
  } finally {
    // Monta l'app e registra il router indipendentemente dall'esito di checkInitialAuth
    app.use(router);
    app.mount('#app');
    console.log('[Main.ts] App montata.');

    // Non inviare IFRAME_READY_FOR_AUTH proattivamente qui.
    // Attendi il segnale dall'host.
  }
};

initializeApp();

// Aggiungi un listener per l'evento 'storage' per sincronizzare sharedAuthStore
// Questo è utile quando localStorage viene modificato da un'altra scheda/iframe.
// L'evento 'storage' potrebbe non essere affidabile per la sincronizzazione iframe immediata.
// window.addEventListener('storage', (event) => { ... }); // Commentato per ora

// Ascolta i messaggi da window.parent (frontend-student)
window.addEventListener('message', (event) => {
  // Non possiamo conoscere l'origine dell'host in anticipo per tutti i messaggi,
  // quindi la verificheremo in modo specifico per tipo di messaggio.

  const { type, payload } = event.data;

  if (type === 'HOST_READY_FOR_IFRAME_SIGNAL') {
    // Qui l'host si identifica. Memorizziamo la sua finestra e origine.
    // Idealmente, dovremmo anche verificare event.origin contro una lista di host consentiti
    // se VITE_ALLOWED_HOST_ORIGINS fosse configurata. Per ora, ci fidiamo dell'host che invia questo.
    activeHostWindow = event.source;
    activeHostOrigin = event.origin;
    console.log(`[Main.ts] Ricevuto HOST_READY_FOR_IFRAME_SIGNAL da origine: ${event.origin}. L'iframe è pronto.`);
    // activeHostOrigin è già stato impostato a event.origin, che è una stringa.
    // activeHostWindow è event.source, che è di tipo MessageEventSource.
    // Per usare .postMessage(message, targetOrigin), dobbiamo assicurarci che sia una Window.
    if (activeHostWindow && typeof activeHostOrigin === 'string') {
      // Assumiamo che event.source sia una Window se non è null.
      // In un contesto iframe, event.source dovrebbe essere la finestra dell'host.
      const hostWindow = activeHostWindow as Window;
      const targetOriginForPostMessage: string = activeHostOrigin;
      hostWindow.postMessage({ type: 'IFRAME_READY_FOR_AUTH' }, targetOriginForPostMessage);
      console.log(`[Main.ts] Inviato IFRAME_READY_FOR_AUTH a host: ${targetOriginForPostMessage}`);
    } else {
        console.error("[Main.ts] activeHostWindow non definito o activeHostOrigin non è una stringa dopo aver ricevuto HOST_READY_FOR_IFRAME_SIGNAL. Impossibile rispondere.");
    }
    return; // Messaggio gestito
  }

  // Per altri messaggi, verifica che provengano dall'host attivo precedentemente identificato.
  if (!activeHostOrigin || event.origin !== activeHostOrigin) {
    console.warn(`[Main.ts message listener] Messaggio di tipo "${type}" ricevuto da origine non attendibile o non attiva: ${event.origin}. Host attivo atteso: ${activeHostOrigin || 'nessuno'}. Messaggio ignorato.`);
    return;
  }

  if (type === 'AUTH_STATE_UPDATED' && payload) {
    console.log(`[Main.ts message listener] Ricevuto AUTH_STATE_UPDATED da host attivo ${activeHostOrigin}:`, payload);
    try {
      const sharedAuthStore = useSharedAuthStore();
      if (payload.accessToken && payload.user && payload.user.role) {
        sharedAuthStore.setAuthData(payload.accessToken, payload.refreshToken, payload.user);
        console.log('[Main.ts message listener] sharedAuthStore aggiornato con i dati da postMessage.');

        // const authStore = useAuthStore(); // authStore è già definito a livello di modulo
        authStore.checkInitialAuth().then(() => {
           console.log('[Main.ts message listener] checkInitialAuth rieseguito dopo aggiornamento da postMessage.');
           if (router.currentRoute.value.meta.requiresGuest && sharedAuthStore.isAuthenticated) {
               const redirectPath = router.currentRoute.value.query.redirect as string || { name: 'dashboard' };
               console.log('[Main.ts message listener] Utente autenticato su pagina guest, redirect a:', redirectPath);
               router.push(redirectPath);
           }
        });
      } else {
        console.warn('[Main.ts message listener] Payload AUTH_STATE_UPDATED invalido o mancante di dati essenziali:', payload);
      }
    } catch (e) {
      console.error('[Main.ts message listener] Errore processando messaggio AUTH_STATE_UPDATED:', e);
    }
  } else if (type === 'AUTH_STATE_CLEARED') {
    console.log(`[Main.ts message listener] Ricevuto AUTH_STATE_CLEARED da host attivo ${activeHostOrigin}.`);
    const sharedAuthStore = useSharedAuthStore();
    sharedAuthStore.clearAuthData();
    // const authStore = useAuthStore(); // authStore è già definito a livello di modulo
    authStore.checkInitialAuth();
  }
});
