import { createRouter, createWebHistory, type RouteLocationNormalized, type NavigationGuardNext, type RouteRecordNormalized } from 'vue-router' // Importa tipi per la guardia
import { useAuthStore } from '@/stores/auth' // Import auth store
// Views are lazy-loaded below

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      // component: LoginView // Assign component later
      component: () => import('../views/LoginView.vue') // Lazy load example
    },
    {
      path: '/', // Or '/dashboard'
      name: 'dashboard',
      // component: DashboardView, // Assign component later
      component: () => import('../views/DashboardView.vue'), // Lazy load example
      meta: { requiresAuth: true } // Mark this route as requiring authentication
    },
    {
      path: '/students',
      name: 'students',
      component: () => import('../views/StudentsView.vue'), // Lazy load
      meta: { requiresAuth: true }
    },
    {
      path: '/quizzes',
      name: 'quizzes',
      component: () => import('../views/QuizzesView.vue'), // Lazy load
      meta: { requiresAuth: true }
    },
    {
      path: '/quizzes/new', // Rotta per creare un nuovo quiz
      name: 'quiz-new',
      component: () => import('../views/QuizFormView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/quizzes/:id/edit', // Rotta per modificare un quiz esistente
      name: 'quiz-edit',
      component: () => import('../views/QuizFormView.vue'),
      props: true, // Passa i parametri della rotta (es. :id) come props al componente
      meta: { requiresAuth: true }
    },
    // Rotte annidate per le domande di un quiz
    {
      path: '/quizzes/:quizId/questions/new', // Crea nuova domanda per un quiz
      name: 'question-new',
      component: () => import('../views/QuestionFormView.vue'),
      props: true, // Passa quizId
      meta: { requiresAuth: true }
    },
    {
      path: '/quizzes/:quizId/questions/:questionId/edit', // Modifica domanda esistente
      name: 'question-edit',
      component: () => import('../views/QuestionFormView.vue'),
      props: true, // Passa quizId e questionId
      meta: { requiresAuth: true }
    },
    {
      path: '/pathways',
      name: 'pathways',
      component: () => import('../views/PathwaysView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/pathways/new',
      name: 'pathway-new',
      component: () => import('../views/PathwayFormView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/pathways/:id/edit',
      name: 'pathway-edit',
      component: () => import('../views/PathwayFormView.vue'),
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/rewards',
      name: 'rewards',
      component: () => import('../views/RewardsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/rewards/new',
      name: 'reward-new',
      component: () => import('../views/RewardFormView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/rewards/:id/edit',
      name: 'reward-edit',
      component: () => import('../views/RewardFormView.vue'),
      props: true,
      meta: { requiresAuth: true }
    },
    {
      path: '/assign',
      name: 'assign',
      component: () => import('../views/AssignmentView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/grading',
      name: 'grading',
      component: () => import('../views/GradingView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/student-progress',
      name: 'student-progress',
      component: () => import('../views/StudentProgressView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/delivery', // Rotta per la consegna ricompense
      name: 'delivery',
      component: () => import('../views/DeliveryView.vue'),
      meta: { requiresAuth: true }
    }
    // Add other teacher routes here later (e.g., student-progress-detail)
  ]
})

// Navigation Guard
router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  // Get store instance *inside* the guard, as Pinia might not be fully initialized outside
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record: RouteRecordNormalized) => record.meta.requiresAuth) // Aggiunto tipo esplicito

  // Check authentication status AFTER store is initialized
  if (requiresAuth && !authStore.isAuthenticated) {
    console.log('Navigation Guard: Route requires auth, but user is not authenticated. Redirecting to login.');
    // Redirect to login if not authenticated and trying to access protected route
    next({ name: 'login', query: { redirect: to.fullPath } }); // Optional: pass redirect query
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    console.log('Navigation Guard: User is authenticated and trying to access login. Redirecting to dashboard.');
    // Optional: Redirect to dashboard if already logged in and trying to access login page
    next({ name: 'dashboard' });
  } else {
    // Otherwise, allow navigation
    console.log('Navigation Guard: Allowing navigation to', to.name);
    next();
  }
})

export default router