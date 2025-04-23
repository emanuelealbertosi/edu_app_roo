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
      path: '/', // Dashboard come home page
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true } // Esempio: richiede autenticazione
    },
    // Aggiungere qui altre route per materie, argomenti, lezioni, ecc.
    {
      path: '/materie',
      name: 'subjects',
      component: () => import('../views/SubjectListView.vue'), // Lazy loading
      meta: { requiresAuth: true, roles: ['Admin', 'Docente', 'Teacher'] } // Richiede auth e ruolo Admin, Docente o Teacher
    },
    {
      path: '/argomenti', // URL per la lista argomenti
      name: 'topics',
      component: () => import('../views/TopicListView.vue'), // Lazy loading
      meta: { requiresAuth: true, roles: ['Admin', 'Docente', 'Teacher'] } // Stessi permessi delle materie (incluso Teacher)
    },
     {
      path: '/lezioni-docente', // URL per la lista lezioni del docente
      name: 'teacher-lessons',
      component: () => import('../views/TeacherLessonListView.vue'),
      meta: { requiresAuth: true, roles: ['Docente', 'Teacher'] } // Solo per Docenti o Teacher
    },
    {
      path: '/lezioni-assegnate', // URL per la lista lezioni dello studente
      name: 'assigned-lessons',
      component: () => import('../views/StudentLessonListView.vue'),
      meta: { requiresAuth: true, roles: ['Studente'] } // Solo per Studenti
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
      meta: { requiresAuth: true, roles: ['Docente', 'Teacher'] } // Solo Docenti/Teacher possono gestire contenuti
    },
     {
      path: '/lezioni/:lessonId(\\d+)/assegna', // Rotta per assegnare la lezione
      name: 'lesson-assign',
      component: () => import('../views/LessonAssignView.vue'),
      props: true, // Passa lessonId come prop
      meta: { requiresAuth: true, roles: ['Docente', 'Teacher'] } // Solo Docenti/Teacher possono assegnare
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
import { useAuthStore } from '@/stores/auth'; // Importa lo store per le guardie

router.beforeEach(async (to, _from, next) => { // Rende la guardia async per poter chiamare checkInitialAuth, rinominato 'from' non usato
  const authStore = useAuthStore();

  // Assicurati che lo stato iniziale sia caricato prima di controllare i permessi
  // Questo è importante se l'utente ricarica la pagina su una rotta protetta
  if (!authStore.user && authStore.accessToken) {
      console.log('Guard: Fetching user before proceeding...');
      await authStore.fetchUser(); // Attende il recupero dei dati utente
      // Se fetchUser fallisce (es. token scaduto), farà logout e lo stato cambierà
  }

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest);
  const requiredRoles = to.meta.roles as string[] | undefined;

  console.log(`Guard: Navigating to ${to.fullPath}, requiresAuth: ${requiresAuth}, isAuthenticated: ${authStore.isAuthenticated}`); // Debug

  if (requiresAuth && !authStore.isAuthenticated) {
    // Se richiede auth ma non è loggato, redirect alla pagina di login di default
    console.log('Guard: Auth required, redirecting to default login.'); // Debug
    next({ name: 'teacher-admin-login', query: { redirect: to.fullPath } }); // Usa il nome della rotta di default
  } else if (requiresGuest && authStore.isAuthenticated) {
    // Se richiede guest (es. pagina login) ma è loggato, redirect a dashboard
    console.log('Guard: Guest required, redirecting to dashboard.'); // Debug
    next({ name: 'dashboard' });
  } else if (requiresAuth && requiredRoles) {
     // Controllo ruolo case-insensitive
     const userRoleUpper = (authStore.user?.role ?? '').toUpperCase();
     const requiredRolesUpper = requiredRoles.map(role => role.toUpperCase());
     if (!requiredRolesUpper.includes(userRoleUpper)) {
        // Se richiede un ruolo specifico ma l'utente non ce l'ha
        console.warn(`Guard: Access denied to route ${String(to.name)}. Role required: ${requiredRoles}, User role: ${authStore.user?.role}`);
        // Reindirizza alla dashboard (o a una pagina 'Unauthorized' se esistesse)
        next({ name: 'dashboard' });
        return; // Esce dalla guardia dopo il redirect
     }
     // Se il ruolo è corretto, procedi
     next();
  } else {
    // Se nessuna delle condizioni precedenti è vera (es. rotta pubblica o utente con ruolo corretto), procedi.
    next();
  }
});

export default router