import { createApp } from 'vue'
import { createPinia } from 'pinia' // Importa Pinia
import router from './router' // Importa il router
import './index.css' // Importa gli stili Tailwind
import App from './App.vue'

// Crea l'istanza dell'app Vue
const app = createApp(App)

// Crea l'istanza di Pinia
const pinia = createPinia()

// Usa Pinia e il Router nell'app
app.use(pinia)
app.use(router)

// Monta l'applicazione
app.mount('#app')
