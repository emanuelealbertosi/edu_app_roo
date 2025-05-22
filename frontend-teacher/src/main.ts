import './assets/main.css' // Import base CSS

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate' // Importa il plugin

import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'; // Importa l'auth store del teacher

const app = createApp(App)
const pinia = createPinia() // Crea l'istanza Pinia
pinia.use(piniaPluginPersistedstate) // Usa il plugin

app.use(pinia) // Usa l'istanza Pinia configurata prima di istanziare gli store

// Funzione asincrona per inizializzare l'app
async function initializeApp() {
  const authStore = useAuthStore(); // Ottieni l'istanza dello store DOPO aver usato Pinia
  try {
    console.log('[main.ts Teacher] Attempting initial auth check...');
    await authStore.checkAuthAndFetchProfile();
    console.log('[main.ts Teacher] Initial auth check complete.');
  } catch (error) {
    console.error('[main.ts Teacher] Error during initial auth check:', error);
    // Non bloccare il montaggio dell'app, le guardie gestiranno il reindirizzamento
  }

  // Monta il router e l'app solo dopo il tentativo di check dell'auth
  app.use(router)
  app.mount('#app')
  console.log('[main.ts Teacher] App mounted.');
}

initializeApp();