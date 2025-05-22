import { createApp } from 'vue'
import { createPinia } from 'pinia' // Importa Pinia
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate' // Importa il plugin
import router from './router' // Importa il router
import './index.css' // Importa gli stili Tailwind
import './style.css' // Importa i nostri stili personalizzati
import App from './App.vue'
import { useAuthStore } from '@/stores/auth'; // Importa l'auth store

// Crea l'istanza dell'app Vue
const app = createApp(App)

// Crea l'istanza di Pinia
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate) // Usa il plugin

// Usa Pinia e il Router nell'app
app.use(pinia) // Usa l'istanza Pinia configurata

// Dopo aver usato Pinia, possiamo istanziare gli store
const authStore = useAuthStore();

// Controlla lo stato di autenticazione iniziale
// È importante farlo prima di montare l'app e prima della navigazione iniziale
// per assicurarsi che le guardie di navigazione abbiano lo stato corretto.
authStore.checkInitialAuth().then(() => {
  // Ora che l'autenticazione iniziale è stata verificata (o tentata),
  // possiamo usare il router e montare l'app.
  app.use(router)
  app.mount('#app')
}).catch(error => {
  console.error("Errore durante il checkInitialAuth:", error);
  // Anche in caso di errore nel check dell'auth, montiamo l'app.
  // Il router e le viste gestiranno il reindirizzamento se l'utente non è autenticato.
  app.use(router)
  app.mount('#app')
});
