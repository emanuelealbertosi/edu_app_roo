import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite' // Aggiunto loadEnv
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => { // Aggiunto mode
  // Carica le variabili d'ambiente specifiche per la modalità corrente (development, production, ecc.)
  // dal file .env nella directory principale del progetto (../)
  const env = loadEnv(mode, process.cwd() + '/..', ['VITE_', 'DJANGO_']) // Carica variabili con prefisso VITE_ e DJANGO_

  const djangoBackend = env.DJANGO_BACKEND_URL || 'http://localhost:8000'; // Fallback se non definito

  return {
    envDir: '../',
    base: command === 'build' ? '/studenti/' : '/',
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
    server: { // NUOVA SEZIONE SERVER
      host: '0.0.0.0', // Permette l'accesso da altri dispositivi sulla rete locale
      port: parseInt(env.VITE_STUDENT_PORT || '5173'), // Usa la porta da .env o default 5173
      proxy: {
        // Proxy per le richieste API al backend Django
        '/api': {
          target: djangoBackend,
          changeOrigin: true, // Necessario per i virtual host
          // Non è necessario riscrivere il percorso se /api è già il prefisso corretto nel backend
        },
        // Proxy per le richieste ai file media al backend Django
        '/media': {
          target: djangoBackend,
          changeOrigin: true,
          // Non è necessario riscrivere il percorso se /media è già il prefisso corretto nel backend
        }
      }
    }
  }
});
