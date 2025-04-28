import './assets/main.css' // Import base CSS

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate' // Importa il plugin

import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia() // Crea l'istanza Pinia
pinia.use(piniaPluginPersistedstate) // Usa il plugin

app.use(pinia) // Usa l'istanza Pinia configurata
app.use(router)

app.mount('#app')