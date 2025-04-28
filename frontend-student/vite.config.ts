import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({ // Modificato per accedere a 'command'
  envDir: '../', // Cerca i file .env nella directory principale del progetto
  base: command === 'build' ? '/studenti/' : '/', // Base condizionale: '/studenti/' per build, '/' per dev
  plugins: [
    vue(),
    vueJsx(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  // Aggiunta parentesi di chiusura per la funzione defineConfig
}));
