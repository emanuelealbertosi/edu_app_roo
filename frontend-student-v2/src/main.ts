import { createApp } from 'vue'
import router from './router' // Importa il router
import pinia from './stores' // Importa Pinia
import './style.css'
import App from './App.vue'

const app = createApp(App)

app.use(router) // Usa il router
app.use(pinia) // Usa Pinia

app.mount('#app')
