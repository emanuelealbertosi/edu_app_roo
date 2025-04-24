import { fileURLToPath, URL } from 'node:url' // Importa helper per i percorsi

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  envDir: '../', // Cerca i file .env nella directory principale del progetto
  base: '/lezioni/', // Imposta il base path per l'applicazione
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)) // Definisce l'alias @ per puntare a src/
    }
  }
})
