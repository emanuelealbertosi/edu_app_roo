import { createRouter, createWebHistory, type RouteLocationNormalized, type NavigationGuardNext, type RouteRecordNormalized } from 'vue-router' // Importa tipi per la guardia
import { useAuthStore } from '@/stores/auth' // Store specifico Teacher (per logout?)
import { useSharedAuthStore, type SharedUser } from '@/stores/sharedAuth'; // Importa store condiviso E TIPO SharedUser
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
      path: '/docenti/login', // Aggiornato il path per corrispondere a Nginx
      name: 'login', // Manteniamo il nome per coerenza interna (es. nelle guardie)
      component: () => import('../views/LoginView.vue'),
      meta: { requiresGuest: true }, // Marca la login come "guest"
      // La guardia beforeEnter è ridondante se beforeEach gestisce requiresGuest, ma la lasciamo per sicurezza/chiarezza
      beforeEnter: (to, from, next) => {
        // Usa lo store condiviso anche qui
        const sharedAuth = useSharedAuthStore();
        if (sharedAuth.isAuthenticated) {
          console.log('Login Route Guard (Teacher): Shared user authenticated, redirecting to landing.');
          // Se l'utente è già loggato (da studente o teacher), mandalo a /landing
          next({ name: 'landing' });
        } else {
          next(); // Proceed to teacher login page
        }
      }
    },
    {
      // Rotta per la Landing Page post-login
      path: '/landing',
      name: 'landing',
      component: () => import('../views/LandingView.vue'),
      meta: { requiresAuth: true } // Richiede autenticazione
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
    // --- Rotta per Sfogliare Gruppi Pubblici ---
    {
      path: '/groups/browse',
      name: 'BrowseGroups',
      component: () => import('../views/BrowseGroupsView.vue'),
      meta: { requiresAuth: true }
    },
    // --- Rotte Quiz Template ---
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
      name: 'GradingDashboard', // Rinominiamo per chiarezza, se GradingView non serve più
      component: () => import('../views/GradingDashboardView.vue'), // Punta alla nuova vista
      meta: { requiresAuth: true },
    },
    {
      path: '/grading/attempt/:attemptId',
      name: 'GradingAttemptView',
      component: () => import('../views/GradingAttemptView.vue'),
      props: true, // Passa i parametri della rotta (attemptId) come props
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
  // Usa lo store condiviso per leggere lo stato di autenticazione
  const sharedAuth = useSharedAuthStore();
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest);
  const isAuthenticated = sharedAuth.isAuthenticated;
  const userRole = sharedAuth.userRole;

  console.log(`[Teacher Router Guard] Navigating to: ${to.path}, requiresAuth: ${requiresAuth}, requiresGuest: ${requiresGuest}, isAuthenticated: ${isAuthenticated}, role: ${userRole}`);

  if (requiresAuth) {
    if (isAuthenticated) {
      // Utente autenticato, verifica ruolo per rotte specifiche del teacher
      // Definisci i ruoli permessi come stringhe letterali
      const allowedRoles = ['TEACHER', 'ADMIN'];
      const isTeacherOrAdmin = userRole && allowedRoles.includes(userRole);

      if (to.name === 'landing') {
         // Chiunque sia autenticato può accedere a /landing
         console.log('[Teacher Router Guard] Accessing landing page (authenticated). Allowing.');
         next();
      } else if (isTeacherOrAdmin) {
         // Utente Teacher/Admin che accede ad altre rotte protette del teacher
         console.log('[Teacher Router Guard] Teacher/Admin accessing protected route. Allowing.');
         // Qui potresti aggiungere la verifica del token se necessaria (try/catch con fetchUserProfile)
         next();
      } else {
         // Utente autenticato ma NON Teacher/Admin (es. Studente) che tenta di accedere a rotte teacher diverse da /landing
         console.warn(`[Teacher Router Guard] Authenticated user with role '${userRole}' tried to access teacher route '${String(to.name)}'. Redirecting to landing.`);
         next({ name: 'landing' }); // Rimanda alla landing page
      }
    } else {
      // Utente non autenticato che tenta di accedere a una rotta protetta
      console.log('[Teacher Router Guard] Auth required, but user not authenticated. Redirecting to teacher login.');
      next({ name: 'login' }); // Reindirizza alla pagina di login del teacher
    }
  } else if (requiresGuest) {
      if (isAuthenticated) {
        // Utente autenticato tenta di accedere a rotta guest (login teacher)
        console.log('[Teacher Router Guard] Guest required, but user is authenticated. Redirecting to landing.');
        next({ name: 'landing' }); // Mandalo alla landing page
      } else {
        // Utente non autenticato su rotta guest, procedi
        next();
      }
  } else {
    // Rotta pubblica non marcata come guest (es. una pagina informativa se esistesse)
    next();
  }
})

export default router