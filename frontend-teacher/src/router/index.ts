import { createRouter, createWebHistory, type RouteLocationNormalized, type NavigationGuardNext, type RouteRecordNormalized } from 'vue-router' // Importa tipi per la guardia
import { useAuthStore } from '@/stores/auth' // Import auth store
// Views are lazy-loaded below

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'root',
      redirect: () => {
        // Get store instance *inside* the redirect function
        const authStore = useAuthStore();
        if (authStore.isAuthenticated) {
          // If authenticated, redirect to the main dashboard
          return { name: 'dashboard' };
        } else {
          // If not authenticated, redirect to the login page
          return { name: 'login' };
        }
      }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      // Add beforeEnter guard to redirect if already logged in
      beforeEnter: (to, from, next) => {
        const authStore = useAuthStore();
        if (authStore.isAuthenticated) {
          console.log('Login Route Guard: User authenticated, redirecting to dashboard.');
          next({ name: 'dashboard' });
        } else {
          next(); // Proceed to login page
        }
      }
    },
    {
      // Define the dashboard route separately now
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true } // Mark this route as requiring authentication
    },
    {
      path: '/students',
      name: 'students',
      component: () => import('../views/StudentsView.vue'), // Lazy load
      meta: { requiresAuth: true }
    },
    {
      path: '/quiz-templates', // Aggiornato path
      name: 'quiz-templates', // Aggiornato nome rotta
      component: () => import('../views/QuizTemplatesView.vue'), // Usa nuova vista elenco template
      meta: { requiresAuth: true }
    },
    {
      path: '/quizzes/upload', // Rotta per caricare un quiz da file
      name: 'quiz-upload',
      component: () => import('../views/QuizUploadView.vue'), // Usa la nuova vista
      meta: { requiresAuth: true }
    },
    {
      path: '/quiz-templates/new', // Aggiornato path
      name: 'quiz-template-new', // Aggiornato nome rotta
      component: () => import('../views/QuizTemplateFormView.vue'), // Usa nuova vista form template
      meta: { requiresAuth: true }
    },
    {
      path: '/quiz-templates/:id/edit', // Aggiornato path
      name: 'quiz-template-edit', // Aggiornato nome rotta
      component: () => import('../views/QuizTemplateFormView.vue'), // Usa nuova vista form template
      props: true,
      meta: { requiresAuth: true },
    }, // Aggiungo la virgola necessaria qui
    // --- Rotte per Domande Template (Nidificate sotto Quiz Templates) ---
    {
      // Rotta per creare una nuova domanda per un template specifico
      path: '/quiz-templates/:templateId/questions/new',
      name: 'quiz-template-question-new',
      component: () => import('../views/QuestionTemplateFormView.vue'), // Usa la nuova vista form
      props: route => ({ templateId: Number(route.params.templateId) }), // Passa templateId come prop
      meta: { requiresAuth: true }
    },
    {
      // Rotta per modificare una domanda template esistente
      path: '/quiz-templates/:templateId/questions/:questionId/edit',
      name: 'quiz-template-question-edit',
      component: () => import('../views/QuestionTemplateFormView.vue'), // Usa la nuova vista form
      props: route => ({
        templateId: Number(route.params.templateId),
        questionId: Number(route.params.questionId) // Passa entrambi gli ID
      }),
      meta: { requiresAuth: true }
    },
    {
      path: '/pathways',
      name: 'pathways',
      component: () => import('../views/PathwaysView.vue'),
      meta: { requiresAuth: true }
    },
    { // Aggiungo { mancante
      path: '/pathways/new',
      name: 'pathway-new',
      component: () => import('../views/PathwayFormView.vue'),
      meta: { requiresAuth: true }
    }, // Chiudo correttamente l'oggetto /pathways/new
    { // Apro l'oggetto per /pathways/:id/edit
      path: '/pathways/:id/edit',
      name: 'pathway-edit',
      component: () => import('../views/PathwayFormView.vue'),
      props: true,
      meta: { requiresAuth: true }
    }, // Aggiungo la virgola mancante
    { // Oggetto per /pathway-templates
      path: '/pathway-templates',
      name: 'pathway-templates',
      component: () => import('../views/PathwayTemplatesView.vue'), // Nuova vista elenco
      meta: { requiresAuth: true },
    },
    {
      path: '/pathway-templates/new',
      name: 'pathway-template-new',
      component: () => import('../views/PathwayTemplateFormView.vue'), // Nuova vista form
      meta: { requiresAuth: true },
    },
    {
      path: '/pathway-templates/:id/edit',
      name: 'pathway-template-edit',
      component: () => import('../views/PathwayTemplateFormView.vue'), // Nuova vista form
      props: true, // Passa :id come prop
      meta: { requiresAuth: true },
    },
    {
      path: '/rewards',
      name: 'rewards',
      component: () => import('../views/RewardsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/rewards/new',
      name: 'reward-new',
      component: () => import('../views/RewardFormView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/rewards/:id/edit',
      name: 'reward-edit',
      component: () => import('../views/RewardFormView.vue'),
      props: true,
      meta: { requiresAuth: true },
    },
    {
      path: '/assign',
      name: 'assign',
      component: () => import('../views/AssignmentView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/grading',
      name: 'grading',
      component: () => import('../views/GradingView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/student-progress',
      name: 'student-progress',
      component: () => import('../views/StudentProgressView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/delivery', // Rotta per la consegna ricompense
      name: 'delivery',
      component: () => import('../views/DeliveryView.vue'),
      meta: { requiresAuth: true },
    },
    // --- Rotte per Istanze Assegnate ---
    {
      path: '/assigned-quizzes',
      name: 'assigned-quizzes',
      component: () => import('../views/AssignedQuizzesView.vue'), // Nuova vista
      meta: { requiresAuth: true }
    },
    {
      path: '/assigned-pathways',
      name: 'assigned-pathways',
      component: () => import('../views/AssignedPathwaysView.vue'), // Nuova vista
      meta: { requiresAuth: true }
    }, // Aggiungo virgola
    { // Nuova rotta per il profilo docente
      path: '/profile',
      name: 'profile',
      component: () => import('../views/ProfileView.vue'),
      meta: { requiresAuth: true }
    }
    // Add other teacher routes here later (e.g., student-progress-detail)
  ]
})

// Navigation Guard
// Simplified Global Navigation Guard
router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  const authStore = useAuthStore();
  const requiresAuth = to.matched.some((record: RouteRecordNormalized) => record.meta.requiresAuth);

  // Only handle redirection for protected routes when the user is not authenticated
  if (requiresAuth && !authStore.isAuthenticated) {
    console.log('Global Guard: Route requires auth, user not authenticated. Redirecting to login.');
    next({ name: 'login', query: { redirect: to.fullPath } });
  } else {
    // Allow all other navigation (including root and login handled by their own guards/redirects)
    console.log('Global Guard: Allowing navigation to', to.name || to.path);
    next();
  }
})

export default router