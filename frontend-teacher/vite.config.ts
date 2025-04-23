import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  envDir: '../', // Cerca i file .env nella directory principale del progetto
  base: '/docenti/', // Aggiungi il percorso base per la produzione
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: { // Optional: Configure a different port if needed
    port: 5174 // Example: Run teacher frontend on port 5174
  }
})