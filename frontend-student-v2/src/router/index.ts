import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth' // Importa lo store per usarlo nella guardia
import MainLayout from '../layouts/MainLayout.vue' // Importa il layout principale
import LoginView from '../views/LoginView.vue' // Importa la vista di Login
import DashboardView from '../views/DashboardView.vue' // Importa la vista Dashboard
// Importa altre viste qui quando necessario

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout, // Usa il layout principale per le rotte figlie
      children: [
        {
          path: '', // Rotta base (es. /)
          name: 'home', // Questa è la nostra dashboard ora
          component: DashboardView,
          meta: { requiresAuth: true } // Questa rotta richiede autenticazione
        },
        {
          path: '/login',
          name: 'login',
          component: LoginView,
          meta: { requiresGuest: true } // Questa rotta è solo per utenti non loggati
        }
        // Aggiungi qui altre rotte che usano MainLayout
      ]
    }
    // Aggiungere qui rotte che NON usano MainLayout, se necessario
  ]
})

// Guardia di Navigazione Globale
router.beforeEach((to, from, next) => {
  // Importa lo store qui DENTRO la guardia per evitare problemi di inizializzazione
  // altrimenti potresti avere problemi con Pinia non ancora pronto all'avvio dell'app.
  // Vedi: https://pinia.vuejs.org/core-concepts/outside-component-usage.html#single-page-applications
  const authStore = useAuthStore() // Assicurati che useAuthStore sia importato all'inizio del file

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest)

  if (requiresAuth && !authStore.isAuthenticated) {
    // Se la rotta richiede auth ma l'utente non è loggato, reindirizza a login
    console.log('Navigation Guard: Not authenticated, redirecting to login.')
    next({ name: 'login' })
  } else if (requiresGuest && authStore.isAuthenticated) {
    // Se la rotta richiede guest (es. login) ma l'utente è loggato, reindirizza a home
    console.log('Navigation Guard: Authenticated, redirecting to home from guest route.')
    next({ name: 'home' })
  } else {
    // Altrimenti, procedi normalmente
    next()
  }
})

export default router