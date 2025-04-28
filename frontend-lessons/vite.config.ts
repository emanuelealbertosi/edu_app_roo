import { fileURLToPath, URL } from 'node:url' // Importa helper per i percorsi

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({ // Modificato per accedere a 'command'
  envDir: '../', // Cerca i file .env nella directory principale del progetto
  base: command === 'build' ? '/lezioni/' : '/', // Base condizionale: '/lezioni/' per build, '/' per dev
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)) // Definisce l'alias @ per puntare a src/
    }
  },
  server: { // Aggiunta configurazione server per proxy di sviluppo
    proxy: {
      // Proxy richieste che iniziano con /api al backend Django su localhost:8000
      '/api': {
        target: 'http://localhost:8000', // Indirizzo base del backend Django
        changeOrigin: true // Necessario per evitare problemi CORS e per virtual host
        // Rimosso rewrite: Vite inoltrerà /api/... a http://localhost:8000/api/...
        // Django dovrebbe trovare la corrispondenza in config/urls.py
      }
    }
  },
  // Aggiunta parentesi di chiusura per la funzione defineConfig
}));
