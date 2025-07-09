import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'
// Importa le viste di login
import TeacherAdminLoginView from '../views/TeacherAdminLoginView.vue' // Rinominata
import StudentLoginView from '../views/StudentLoginView.vue' // Nuova
import DashboardView from '../views/DashboardView.vue'
// import NotFoundView from '../views/NotFoundView.vue'

// Funzione helper per determinare il breadcrumb "Home"
const getHomeBreadcrumb = () => {
  // Controlla se l'app è in un iframe e se il parametro 'embedded' è presente
  const urlParams = new URLSearchParams(window.location.search);
  const isEmbedded = urlParams.get('embedded') === 'true';

  if (isEmbedded) {
    // Se è embedded, usa un oggetto speciale che il componente Breadcrumb interpreterà
    // Se è embedded, usa un oggetto speciale che il componente Breadcrumb interpreterà
    return { text: 'Home', isHostLink: true, hostLinkType: 'home' };
  }
  // Altrimenti, linka alla dashboard interna
  return { text: 'Home', to: { name: 'dashboard' } };
};

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
      meta: {
        requiresAuth: true,
        breadcrumb: () => [
          getHomeBreadcrumb()
        ]
      }
    },
    // Aggiungere qui altre route per materie, argomenti, lezioni, ecc.
    {
      path: '/materie',
      name: 'subjects',
      component: () => import('../views/SubjectListView.vue'), // Lazy loading
      meta: {
        requiresAuth: true,
        roles: ['Admin', 'Docente', 'Teacher', 'ADMIN', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'Materie' }
        ]
      }
    },
    {
      path: '/argomenti', // URL per la lista argomenti
      name: 'topics',
      component: () => import('../views/TopicListView.vue'), // Lazy loading
      meta: {
        requiresAuth: true,
        roles: ['Admin', 'Docente', 'Teacher', 'ADMIN', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'Argomenti' }
        ]
      }
    },
     {
      path: '/docente', // Rotta per l'atterraggio del docente da /lezioni/docente
      name: 'teacher-landing', // Nome univoco
      component: () => import('../views/TeacherLessonListView.vue'), // Mostra la lista lezioni
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'Le mie Lezioni' }
        ]
      }
     },
     {
      path: '/lezioni-docente', // URL alternativo per la lista lezioni del docente (se serve)
      name: 'teacher-lessons', // Nome diverso se si mantiene questa rotta
      component: () => import('../views/TeacherLessonListView.vue'),
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'Le mie Lezioni' }
        ]
      }
    },
    {
      path: '/lezioni-assegnate', // URL per la lista lezioni dello studente
      name: 'assigned-lessons',
      component: () => import('../views/StudentLessonListView.vue'),
      meta: {
        requiresAuth: true,
        roles: ['Studente', 'STUDENT'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'Lezioni Assegnate' }
        ]
      }
    },
    {
      path: '/lezioni/:id(\\d+)', // Usa regex per assicurare che id sia numerico
      name: 'lesson-detail',
      component: () => import('../views/LessonDetailView.vue'),
      props: true, // Passa i parametri della route (id) come props al componente
      meta: {
        requiresAuth: true,
        breadcrumb: () => {
          const urlParams = new URLSearchParams(window.location.search);
          const isEmbedded = urlParams.get('embedded') === 'true';

          let lessonsBreadcrumb;
          if (isEmbedded) {
            // Se embedded (dentro student FE), il link deve tornare alla lista dell'host
            lessonsBreadcrumb = { text: 'Lezioni Assegnate', isHostLink: true, hostLinkType: 'assigned-lessons' };
          } else {
            // Altrimenti, è un docente/admin dentro l'app lessons, va alla sua lista
            lessonsBreadcrumb = { text: 'Lezioni', to: { name: 'teacher-lessons' } };
          }

          return [
            getHomeBreadcrumb(),
            lessonsBreadcrumb,
            { text: 'Dettaglio' }
          ];
        }
      }
    },
    {
      path: '/lezioni/:lessonId(\\d+)/contenuti', // Rotta per gestire i contenuti
      name: 'lesson-contents',
      component: () => import('../views/LessonContentView.vue'),
      props: true, // Passa lessonId come prop
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: (route: RouteLocationNormalized) => [
          getHomeBreadcrumb(),
          { text: 'Lezioni', to: { name: 'teacher-lessons' } },
          { text: `Lezione ${route.params.lessonId}`, to: { name: 'lesson-detail', params: { id: route.params.lessonId } } },
          { text: 'Contenuti' }
        ]
      }
    },
     {
      path: '/lezioni/:lessonId(\\d+)/assegna', // Rotta per assegnare la lezione
      name: 'lesson-assign',
      component: () => import('../views/LessonAssignView.vue'),
      props: true, // Passa lessonId come prop
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: (route: RouteLocationNormalized) => [
          getHomeBreadcrumb(),
          { text: 'Lezioni', to: { name: 'teacher-lessons' } },
          { text: `Lezione ${route.params.lessonId}`, to: { name: 'lesson-detail', params: { id: route.params.lessonId } } },
          { text: 'Assegna' }
        ]
      }
    },
    // --- Route per i Corsi (Courses) ---
    {
      path: '/courses',
      name: 'course-list',
      component: () => import('../views/courses/CourseListView.vue'),
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'Corsi' }
        ]
      }
    },
    {
      path: '/courses/new',
      name: 'course-new',
      component: () => import('../views/courses/CourseFormView.vue'),
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'Corsi', to: { name: 'course-list' } },
          { text: 'Nuovo' }
        ]
      }
    },
    {
      path: '/courses/:id(\\d+)',
      name: 'course-detail',
      component: () => import('../views/courses/CourseDetailView.vue'),
      props: true,
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'Corsi', to: { name: 'course-list' } },
          { text: 'Dettaglio' }
        ]
      }
    },
    {
      path: '/courses/:id(\\d+)/edit',
      name: 'course-edit',
      component: () => import('../views/courses/CourseFormView.vue'),
      props: true,
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: (route: RouteLocationNormalized) => [
          getHomeBreadcrumb(),
          { text: 'Corsi', to: { name: 'course-list' } },
          { text: `Modifica Corso ${route.params.id}`, to: { name: 'course-detail', params: { id: route.params.id } } },
        ]
      }
    },
    // --- Fine Route Corsi ---

    // --- Route per Unità Didattiche di Apprendimento (UDA) ---
    {
      path: '/udas',
      name: 'uda-list',
      component: () => import('../views/uda/UdaListView.vue'),
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'UDA' }
        ]
      }
    },
    {
      path: '/udas/new',
      name: 'uda-new',
      component: () => import('../views/uda/UdaFormView.vue'), // Può usare un template opzionale
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'UDA', to: { name: 'uda-list' } },
          { text: 'Nuova' }
        ]
      }
    },
    {
      path: '/udas/:id(\\d+)',
      name: 'uda-detail',
      component: () => import('../views/uda/UdaDetailView.vue'),
      props: true,
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: () => [
          getHomeBreadcrumb(),
          { text: 'UDA', to: { name: 'uda-list' } },
          { text: 'Dettaglio' }
        ]
      }
    },
    {
      path: '/udas/:id(\\d+)/edit',
      name: 'uda-edit',
      component: () => import('../views/uda/UdaFormView.vue'),
      props: true,
      meta: {
        requiresAuth: true,
        roles: ['Docente', 'Teacher', 'TEACHER'],
        breadcrumb: (route: RouteLocationNormalized) => [
          getHomeBreadcrumb(),
          { text: 'UDA', to: { name: 'uda-list' } },
          { text: `Modifica UDA ${route.params.id}`, to: { name: 'uda-detail', params: { id: route.params.id } } },
        ]
      }
    },
    // --- Fine Route UDA ---

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

  console.log(`[Router Guard] beforeEach: Navigating from ${from.fullPath} to ${to.fullPath}`);

  // Logica per far persistere il query parameter 'embedded'
  if (from.query.embedded === 'true' && to.query.embedded !== 'true') {
    // Se stiamo navigando da una pagina embedded e la destinazione non ha il parametro, aggiungilo.
    // Questo assicura che il parametro persista durante la navigazione interna all'iframe.
    // È importante clonare to.query per evitare modifiche dirette che Vue Router potrebbe non gradire.
    const newQuery = { ...to.query, embedded: 'true' };
    // Rimpiazza la navigazione con la nuova query.
    // Usiamo 'replace' per non aggiungere una nuova entry nella history del browser per questo aggiustamento.
    console.log(`Guard: Persisting 'embedded=true'. Navigating to ${String(to.name)} with query: ${JSON.stringify(newQuery)}`);
    next({ path: to.path, query: newQuery, replace: true });
    return; // Interrompi l'esecuzione della guardia qui, la navigazione è stata gestita.
  }

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