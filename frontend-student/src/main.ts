import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate' // Importa il plugin
import { useAuthStore } from './stores/auth' // Importa lo store authStudent

import App from './App.vue'
import router from './router'

// Funzione asincrona per inizializzare e montare l'app
async function initializeAndMountApp() {
  const app = createApp(App)
  const pinia = createPinia() // Crea istanza Pinia
  pinia.use(piniaPluginPersistedstate) // Usa il plugin

  app.use(pinia) // Usa Pinia configurato PRIMA di accedere agli store
  app.use(router)

  // Ottieni lo store DOPO aver usato Pinia
  const authStore = useAuthStore()

  try {
    // Chiama l'azione di inizializzazione dello store
    await authStore.initializeAuth()
    console.log('[main.ts] Auth initialization attempt complete.');
  } catch (error) {
    // Anche se fallisce, l'app deve montare (gestirà redirect)
    console.error('[main.ts] Error during auth initialization:', error);
  }

  // Monta l'app solo dopo l'inizializzazione
  app.mount('#app')
}

// Chiama la funzione di inizializzazione
initializeAndMountApp();
