import { createRouter, createWebHistory } from 'vue-router'
import AuthService from '@/api/auth';
import { usePathwayStore } from '@/stores/pathway';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: to => {
        // Redirect to dashboard if authenticated, otherwise to login
        return AuthService.isAuthenticated() ? '/dashboard' : '/login'
      }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      // Evita che utenti già autenticati possano accedere alla pagina di login
      beforeEnter: (to, from, next) => {
        if (AuthService.isAuthenticated()) {
          next('/dashboard')
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
      path: '/quiz/:id',
      name: 'quiz-details',
      component: () => import('../views/QuizDetailsView.vue'),
      meta: { requiresAuth: true },
      props: true
    },
    {
      path: '/quiz/:quizId/attempt/:attemptId',
      name: 'quiz-attempt',
      component: () => import('../views/QuizAttemptView.vue'),
      meta: { requiresAuth: true },
      props: true
    },
    {
      path: '/pathway/:id',
      name: 'pathway-details',
      component: () => import('../views/PathwayDetailsView.vue'),
      meta: { requiresAuth: true },
      props: true
    },
    // Rotta 404 per pagine non trovate
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      redirect: '/'
    }
  ],
})

// Guardia di navigazione globale per proteggere le rotte autenticate
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const isAuthenticated = AuthService.isAuthenticated()

  if (requiresAuth) {
    if (isAuthenticated) {
      // Verifica che il token sia valido prima di consentire la navigazione
      try {
        const isValid = await AuthService.checkTokenValidity()
        if (isValid) {
          next()
        } else {
          // Token non valido, reindirizza al login
          next('/login')
        }
      } catch (error) {
        console.error('Error checking token validity:', error)
        next('/login')
      }
    } else {
      // Non autenticato, reindirizza al login
      next('/login')
    }
  } else {
    // Rotta non protetta, consente la navigazione
    next()
  }
})

export default router
