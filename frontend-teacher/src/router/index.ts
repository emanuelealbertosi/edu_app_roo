import { createRouter, createWebHistory, type RouteLocationNormalized, type NavigationGuardNext, type RouteRecordNormalized } from 'vue-router' // Importa tipi per la guardia
import { useAuthStore } from '@/stores/auth' // Import auth store
// Views are lazy-loaded below

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
    // --- Rotte per Gruppi Studenti ---
    {
      path: '/groups',
      name: 'GroupsList', // Nome per la lista dei gruppi
      component: () => import('../views/GroupsListView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/groups/new',
      name: 'GroupCreate',
      component: () => import('../views/GroupFormView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/groups/:id/edit',
      name: 'GroupEdit',
      component: () => import('../views/GroupFormView.vue'),
      props: true, // Passa :id come prop
      meta: { requiresAuth: true }
    },
    {
      path: '/groups/:id', // Rotta per i dettagli del gruppo
      name: 'GroupDetail',
      component: () => import('../views/GroupDetailView.vue'),
      props: true, // Passa :id come prop
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
// Guardia di navigazione globale aggiornata
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore(); // Ottieni lo store
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  // Non chiamare isAuthenticated() qui, usa il getter dello store
  const isAuthenticated = authStore.isAuthenticated;

  if (requiresAuth) { // Se la rotta di destinazione richiede autenticazione
    if (isAuthenticated) {
      // Verifica la validità del token (lo store dovrebbe gestire il refresh/logout se necessario)
      // Potremmo aggiungere una chiamata esplicita a checkTokenValidity o fetchUserProfile se necessario
      // Per ora, assumiamo che lo stato dello store sia affidabile o che le chiamate API falliranno
      // Se vuoi una verifica più robusta ad ogni navigazione protetta:
      try {
          // await authStore.fetchUserProfile(); // Assicurati che il profilo sia aggiornato e il token valido
          // O una chiamata più leggera se disponibile: await authStore.checkTokenValidity();
          next(); // Utente autenticato, procedi
      } catch (error) {
          console.error("Errore durante la verifica dell'utente prima della navigazione:", error);
          next({ name: 'login' }); // In caso di errore, vai al login
      }
    } else {
      // Utente non autenticato che tenta di accedere a una rotta protetta
      next({ name: 'login' }); // Reindirizza alla pagina di login
    }
  } else { // Rotta non protetta (né auth né guest specificato esplicitamente O requiresGuest)
    const requiresGuest = to.matched.some(record => record.meta.requiresGuest);
    if (requiresGuest && isAuthenticated) {
       // Utente autenticato tenta di accedere a rotta guest (login, root)
       console.log('Guard: Guest required but user is authenticated, redirecting to dashboard.');
       next({ name: 'dashboard' });
    } else {
       // Utente non autenticato su rotta guest O qualsiasi utente su rotta veramente pubblica
       next();
    }
  }
})

export default router