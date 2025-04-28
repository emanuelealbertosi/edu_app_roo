import { createRouter, createWebHistory } from 'vue-router'
// Importa le viste di login
import TeacherAdminLoginView from '../views/TeacherAdminLoginView.vue' // Rinominata
import StudentLoginView from '../views/StudentLoginView.vue' // Nuova
import DashboardView from '../views/DashboardView.vue'
// import NotFoundView from '../views/NotFoundView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), // Usa la history API HTML5
  routes: [
    // Rinomina la rotta di login originale e punta al nuovo componente
    {
      path: '/login/docente-admin', // Nuovo path
      name: 'teacher-admin-login', // Nuovo nome
      component: TeacherAdminLoginView,
       meta: { requiresGuest: true }
     },
     // Aggiunge la nuova rotta per il login studente
     {
       path: '/login/studente', // Nuovo path
       name: 'student-login', // Nuovo nome
       component: StudentLoginView,
       meta: { requiresGuest: true }
     },
     // Aggiungiamo un redirect da /login alla pagina di default (es. docente/admin)
     {
       path: '/login',
       redirect: { name: 'teacher-admin-login' }
     },
    {
      path: '/', // Root path
      name: 'root', // Nome per la rotta root
      component: TeacherAdminLoginView, // Punta direttamente alla login di default
      meta: { requiresGuest: true } // Marca anche la root come "guest"
    },
    {
      // Definisci esplicitamente la dashboard
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true } // Richiede autenticazione
    },
    // Aggiungere qui altre route per materie, argomenti, lezioni, ecc.
    {
      path: '/materie',
      name: 'subjects',
      component: () => import('../views/SubjectListView.vue'), // Lazy loading
      meta: { requiresAuth: true, roles: ['Admin', 'Docente', 'Teacher', 'ADMIN', 'TEACHER'] } // Includi case corretto
    },
    {
      path: '/argomenti', // URL per la lista argomenti
      name: 'topics',
      component: () => import('../views/TopicListView.vue'), // Lazy loading
      meta: { requiresAuth: true, roles: ['Admin', 'Docente', 'Teacher', 'ADMIN', 'TEACHER'] } // Includi case corretto
    },
     {
      path: '/docente', // Rotta per l'atterraggio del docente da /lezioni/docente
      name: 'teacher-landing', // Nome univoco
      component: () => import('../views/TeacherLessonListView.vue'), // Mostra la lista lezioni
      meta: { requiresAuth: true, roles: ['Docente', 'Teacher', 'TEACHER'] } // Includi case corretto
     },
     {
      path: '/lezioni-docente', // URL alternativo per la lista lezioni del docente (se serve)
      name: 'teacher-lessons', // Nome diverso se si mantiene questa rotta
      component: () => import('../views/TeacherLessonListView.vue'),
      meta: { requiresAuth: true, roles: ['Docente', 'Teacher', 'TEACHER'] } // Includi case corretto
    },
    {
      path: '/lezioni-assegnate', // URL per la lista lezioni dello studente
      name: 'assigned-lessons',
      component: () => import('../views/StudentLessonListView.vue'),
      meta: { requiresAuth: true, roles: ['Studente', 'STUDENT'] } // Includi case corretto
    },
    {
      path: '/lezioni/:id(\\d+)', // Usa regex per assicurare che id sia numerico
      name: 'lesson-detail',
      component: () => import('../views/LessonDetailView.vue'),
      props: true, // Passa i parametri della route (id) come props al componente
      meta: { requiresAuth: true } // Accessibile da Studenti e Docenti (permesso gestito nella vista/store)
    },
    {
      path: '/lezioni/:lessonId(\\d+)/contenuti', // Rotta per gestire i contenuti
      name: 'lesson-contents',
      component: () => import('../views/LessonContentView.vue'),
      props: true, // Passa lessonId come prop
      meta: { requiresAuth: true, roles: ['Docente', 'Teacher', 'TEACHER'] } // Includi case corretto
    },
     {
      path: '/lezioni/:lessonId(\\d+)/assegna', // Rotta per assegnare la lezione
      name: 'lesson-assign',
      component: () => import('../views/LessonAssignView.vue'),
      props: true, // Passa lessonId come prop
      meta: { requiresAuth: true, roles: ['Docente', 'Teacher', 'TEACHER'] } // Includi case corretto
    },

    // Catch-all route per pagine non trovate (deve essere l'ultima)
    // {
    //   path: '/:pathMatch(.*)*',
    //   name: 'NotFound',
    //   component: NotFoundView
    // }
  ]
})

// --- Navigation Guards ---
import { useSharedAuthStore } from '@/stores/sharedAuth'; // Importa lo store condiviso

router.beforeEach(async (to, from, next) => {
  const sharedAuth = useSharedAuthStore(); // Usa lo store condiviso

  // La logica di inizializzazione/fetch utente è meglio gestirla
  // a livello di App.vue o main.ts per garantire che lo stato sia pronto.
  // Rimuoviamo il tentativo di fetch da qui.

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest);
  const requiredRoles = to.meta.roles as string[] | undefined;
  const isAuthenticated = sharedAuth.isAuthenticated; // Usa stato condiviso

  console.log(`Guard: To: ${String(to.name)}, From: ${String(from.name)}, Auth: ${isAuthenticated}, Role: ${sharedAuth.userRole}`);

  if (requiresAuth && !isAuthenticated) {
    // Utente non autenticato tenta di accedere a rotta protetta
    console.log('Guard: Auth required, redirecting to default login.');
    // Reindirizza alla pagina di login appropriata (es. quella del docente come default)
    // Potremmo voler salvare `to.fullPath` per reindirizzare dopo il login.
    next({ name: 'teacher-admin-login', query: { redirect: to.fullPath } });
  } else if (requiresGuest && isAuthenticated) {
    // Utente autenticato tenta di accedere a rotta guest (login, root)
    console.log('Guard: Guest required but user is authenticated, redirecting to dashboard.');
    // Reindirizza alla dashboard interna di questa app (lessons)
    next({ name: 'dashboard' });
  } else if (requiresAuth && isAuthenticated && requiredRoles) {
    // Utente autenticato, rotta protetta con controllo ruoli
    const userRoleUpper = (sharedAuth.userRole ?? '').toUpperCase(); // Usa ruolo condiviso
    const requiredRolesUpper = requiredRoles.map(role => role.toUpperCase()); // Assicura che anche i ruoli richiesti siano maiuscoli
    if (!requiredRolesUpper.includes(userRoleUpper)) {
      // Ruolo non corrispondente
      console.warn(`Guard: Role mismatch. Required: ${requiredRoles}, User has: ${sharedAuth.userRole}. Redirecting to dashboard.`);
      // Reindirizza alla dashboard o a una pagina 'Unauthorized'
      next({ name: 'dashboard' });
    } else {
      // Ruolo corretto, procedi
      next();
    }
  } else {
    // Tutti gli altri casi (utente non auth su rotta guest, utente auth su rotta protetta senza ruoli specifici, rotte pubbliche)
    next();
  }
});

export default router