import { createRouter, createWebHistory } from 'vue-router'
import AuthService from '@/api/auth';
import { usePathwayStore } from '@/stores/pathway';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'root', // Nome per la rotta root
      component: () => import('../views/LoginView.vue'), // Mostra LoginView per default a '/'
      meta: { requiresGuest: true } // Marca anche la root come "guest"
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { requiresGuest: true }, // Marca la login come "guest"
      // La guardia beforeEnter è ridondante se beforeEach gestisce requiresGuest, ma la lasciamo per sicurezza/chiarezza
      beforeEnter: (to, from, next) => {
        if (AuthService.isAuthenticated()) {
          next({ name: 'dashboard' }) // Usa il nome della rotta per coerenza
        } else {
          next()
        }
      }
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/shop',
      name: 'shop',
      component: () => import('../views/ShopView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/purchases',
      name: 'purchases',
      component: () => import('../views/PurchasesView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/badges',
      name: 'Badges',
      component: () => import('../views/BadgesView.vue'), // Aggiunto import dinamico
      meta: { requiresAuth: true }
    },
    {
      path: '/quiz/:id',
      name: 'quiz-details',
      component: () => import('../views/QuizDetailsView.vue'),
      meta: { requiresAuth: true },
      props: true
    },
    {
      // Nuova rotta per iniziare un tentativo
      path: '/quiz/:quizId/start',
      name: 'quiz-start-attempt',
      component: () => import('../views/QuizAttemptView.vue'),
      meta: { requiresAuth: true },
      props: route => ({ quizId: Number(route.params.quizId) }) // Passa solo quizId
    },
    {
      // Rotta esistente (potrebbe servire per riprendere/visualizzare)
      path: '/quiz/:quizId/attempt/:attemptId',
      name: 'quiz-attempt',
      component: () => import('../views/QuizAttemptView.vue'), // Usa la stessa vista per ora
      meta: { requiresAuth: true },
      props: true // Passa sia quizId che attemptId
    },
    {
      path: '/pathway/:id',
      name: 'pathway-details',
      component: () => import('../views/PathwayDetailsView.vue'),
      meta: { requiresAuth: true },
      props: true
    },
    {
      // Rotta per visualizzare i risultati di un tentativo
      path: '/quiz/result/:attemptId',
      name: 'QuizResult', // Nome usato in QuizAttemptView.vue
      component: () => import('../views/QuizResultView.vue'),
      meta: { requiresAuth: true },
      props: true // Passa attemptId come prop
    },
     {
      // Rotta per visualizzare i risultati di un percorso
      path: '/pathway/result/:pathwayId',
      name: 'PathwayResult',
      component: () => import('../views/PathwayResultView.vue'),
      meta: { requiresAuth: true },
      props: true // Passa pathwayId come prop
    },
    {
      // Rotta per iniziare o continuare un percorso
      path: '/pathway/:pathwayId/attempt',
      name: 'PathwayAttempt', // Nome usato in PathwayList.vue
      component: () => import('../views/PathwayAttemptView.vue'),
      meta: { requiresAuth: true },
      props: route => ({ pathwayId: Number(route.params.pathwayId) })
    },
    {
      // Rotta per il profilo studente
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true }
    },
    // Rotta pubblica per la registrazione studente tramite token
    {
      path: '/register/student', // Il token sarà nella query string ?token=...
      name: 'StudentRegistration',
      component: () => import('../views/StudentRegistrationView.vue'),
      beforeEnter: (to, from, next) => {
        // Se l'utente è già autenticato, reindirizza alla dashboard
        if (AuthService.isAuthenticated()) {
          next('/dashboard');
        } else {
          next();
        }
      }
    },
    // Rotta 404 per pagine non trovate
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      redirect: '/'
    }
  ],
})

// Guardia di navigazione globale aggiornata
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const isAuthenticated = AuthService.isAuthenticated(); // Assicurati che AuthService sia importato e funzioni

  if (requiresAuth) { // Se la rotta di destinazione richiede autenticazione
    if (isAuthenticated) {
      // Verifica la validità del token (gestisce refresh/logout se necessario)
      try {
        const isValid = await AuthService.checkTokenValidity();
        if (isValid) {
          next(); // Utente autenticato e token valido, procedi
        } else {
          // Token non valido (scaduto e non rinnovabile o altro errore)
          next({ name: 'login' }); // Reindirizza alla pagina di login
        }
      } catch (error) {
         console.error('Errore durante la verifica del token:', error);
         next({ name: 'login' }); // In caso di errore nella verifica, vai al login
      }
    } else {
      // Utente non autenticato che tenta di accedere a una rotta protetta
      next({ name: 'login' }); // Reindirizza alla pagina di login
    }
  } else { // Se la rotta di destinazione NON richiede autenticazione (es. '/', '/login', '/register')
    // Se l'utente è autenticato e cerca di accedere a una rotta pubblica che non dovrebbe vedere (login, root, register),
    // reindirizza alla dashboard.
    if (isAuthenticated && (to.name === 'root' || to.name === 'login' || to.name === 'StudentRegistration')) {
      next({ name: 'dashboard' }); // Reindirizza alla dashboard
    } else {
      // Altrimenti (utente non autenticato su rotta pubblica, o utente autenticato su altra rotta pubblica), procedi
      next();
    }
  }
})

export default router
