import { createRouter, createWebHistory } from 'vue-router'
import AuthService from '@/api/auth'; // Mantenuto per eventuali chiamate API specifiche se necessarie altrove
import { usePathwayStore } from '@/stores/pathway';
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa lo store condiviso

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
        // Ottieni lo store all'interno della guardia
        const sharedAuth = useSharedAuthStore();
        if (sharedAuth.isAuthenticated) {
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
      meta: { requiresGuest: true }, // Aggiunto meta tag
      beforeEnter: (to, from, next) => {
        // Ottieni lo store all'interno della guardia
        const sharedAuth = useSharedAuthStore();
        if (sharedAuth.isAuthenticated) {
          next('/dashboard');
        } else {
          next();
        }
      }
    },
    // Nuova rotta pubblica per la registrazione tramite token di gruppo
    {
      path: '/register/group/:token', // Il token è un parametro della rotta
      name: 'GroupTokenRegistration',
      component: () => import('../views/GroupTokenRegistrationView.vue'),
      props: true, // Passa i parametri della rotta come props al componente
      meta: { requiresGuest: true }, // Solo per utenti non autenticati
      beforeEnter: (to, from, next) => {
        // Ottieni lo store all'interno della guardia
        const sharedAuth = useSharedAuthStore();
        if (sharedAuth.isAuthenticated) {
          next({ name: 'dashboard' });
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
  // Ottieni lo store condiviso DENTRO la guardia
  const sharedAuth = useSharedAuthStore();
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest); // Controlla anche le rotte "guest"
  const isAuthenticated = sharedAuth.isAuthenticated; // Usa lo stato dello store

  console.log(`[Router Guard] Navigating to: ${to.path}, requiresAuth: ${requiresAuth}, requiresGuest: ${requiresGuest}, isAuthenticated: ${isAuthenticated}`);

  if (requiresAuth && !isAuthenticated) {
    // Utente non autenticato che tenta di accedere a una rotta protetta
    console.log('[Router Guard] Auth required, but user not authenticated. Redirecting to login.');
    next({ name: 'login' });
  } else if (requiresGuest && isAuthenticated) {
    // Utente autenticato che tenta di accedere a una rotta "guest" (es. login, register)
    console.log('[Router Guard] Guest required, but user is authenticated. Redirecting to dashboard.');
    next({ name: 'dashboard' });
  } else {
    // Utente autenticato su rotta protetta,
    // Utente non autenticato su rotta pubblica/guest,
    // Utente autenticato su rotta pubblica non-guest
    console.log('[Router Guard] Access granted.');
    next(); // Procedi con la navigazione
  }
})

export default router
