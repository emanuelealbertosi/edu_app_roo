import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import DashboardView from '../DashboardView.vue';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';

// Mock dei componenti figlio per isolare il test della DashboardView
const MockWalletCard = { template: '<div class="mock-wallet-card">Wallet</div>' };
const MockQuizList = { template: '<div class="mock-quiz-list">Quiz List</div>', props: ['quizzes', 'title', 'emptyMessage', 'loading', 'showStartButton'] };
const MockPathwayList = { template: '<div class="mock-pathway-list">Pathway List</div>', props: ['pathways', 'title', 'emptyMessage', 'loading', 'showResultLink'] };

// Mock del router
const routes = [
  { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
  { path: '/login', name: 'login', component: { template: '<div>Login</div>' } },
  { path: '/dashboard', name: 'dashboard', component: DashboardView },
  { path: '/shop', name: 'shop', component: { template: '<div>Shop</div>' } },
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

describe('DashboardView.vue', () => {
  beforeEach(() => {
    // Crea una nuova istanza Pinia per ogni test per isolarli
    setActivePinia(createPinia());
    // Resetta il router prima di ogni test
    router.push('/dashboard'); 
  });

  it('renders loading state initially', () => {
    // Mock store con stato di loading iniziale
    const dashboardStore = useDashboardStore();
    dashboardStore.loading.quizzes = true; // Simula uno stato di caricamento

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router], // Fornisce il router mockato
        stubs: { // Sostituisce i componenti figlio con i mock
            WalletCard: MockWalletCard,
            QuizList: MockQuizList,
            PathwayList: MockPathwayList,
            RouterLink: true // Stub semplice per RouterLink se necessario
        }
      }
    });

    expect(wrapper.find('.loading-container').exists()).toBe(true);
    expect(wrapper.find('.dashboard-content').exists()).toBe(false);
  });

  it('calls dashboardStore.loadDashboard on mount', async () => {
    const dashboardStore = useDashboardStore();
    // Crea uno spy sulla action loadDashboard
    const loadDashboardSpy = vi.spyOn(dashboardStore, 'loadDashboard');

    mount(DashboardView, {
      global: {
        plugins: [router],
         stubs: {
            WalletCard: MockWalletCard,
            QuizList: MockQuizList,
            PathwayList: MockPathwayList,
            RouterLink: true
        }
      }
    });

    // Attende che le promesse (come onMounted) vengano risolte
    await flushPromises(); 

    expect(loadDashboardSpy).toHaveBeenCalledTimes(1);
  });

  it('renders dashboard content after loading', async () => {
     const authStore = useAuthStore();
     const dashboardStore = useDashboardStore();

     // Simula dati caricati (fornendo tutte le proprietà di StudentData)
     authStore.user = {
         id: 1,
         first_name: 'Test',
         last_name: 'User',
         student_code: 'test01',
         full_name: 'Test User', // Aggiunto
         teacher: 1,             // Aggiunto
         teacher_username: 'docente', // Aggiunto
         is_active: true,        // Aggiunto
         created_at: new Date().toISOString() // Aggiunto
     };
     dashboardStore.wallet = { current_points: 100, recent_transactions: [] };
     dashboardStore.quizzes = [{ id: 1, title: 'Quiz 1', description: 'Desc', metadata: {}, latest_attempt: null, available_from: null, available_until: null }];
     // Corretto: usa latest_progress e aggiunge quiz_details
     dashboardStore.pathways = [{ id: 1, title: 'Pathway 1', description: 'Desc', metadata: {}, latest_progress: null, quiz_details: [] }];
     dashboardStore.loading = { quizzes: false, pathways: false, wallet: false }; // Simula fine caricamento

     const wrapper = mount(DashboardView, {
       global: {
         plugins: [router],
          stubs: {
            WalletCard: MockWalletCard,
            QuizList: MockQuizList,
            PathwayList: MockPathwayList,
            RouterLink: true
        }
       }
     });

     // Attende che Vue aggiorni il DOM dopo il cambio di stato
     await flushPromises(); 

     expect(wrapper.find('.loading-container').exists()).toBe(false);
     expect(wrapper.find('.dashboard-content').exists()).toBe(true);
     expect(wrapper.find('.user-info p').text()).toContain('Benvenuto, Test User!');
     expect(wrapper.findAll('.mock-wallet-card').length).toBe(1);
     // Verifica che vengano renderizzate le liste (5 in totale come nel template originale)
     expect(wrapper.findAll('.mock-quiz-list').length).toBe(3); 
     expect(wrapper.findAll('.mock-pathway-list').length).toBe(2); 
  });

  it('calls authStore.logout and navigates to login on logout button click', async () => {
    const authStore = useAuthStore();
    const logoutSpy = vi.spyOn(authStore, 'logout');
    const routerPushSpy = vi.spyOn(router, 'push');

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router],
         stubs: {
            WalletCard: MockWalletCard,
            QuizList: MockQuizList,
            PathwayList: MockPathwayList,
            RouterLink: true
        }
      }
    });
    
    await flushPromises(); // Assicura che il componente sia montato

    const logoutButton = wrapper.find('.logout-button');
    await logoutButton.trigger('click');

    expect(logoutSpy).toHaveBeenCalledTimes(1);
    // Attende che la promessa di logout (se asincrona) e la navigazione vengano completate
    await flushPromises(); 
    expect(routerPushSpy).toHaveBeenCalledWith('/login');
  });

   it('navigates to shop on shop button click', async () => {
    const routerPushSpy = vi.spyOn(router, 'push');

    const wrapper = mount(DashboardView, {
      global: {
        plugins: [router],
         stubs: {
            WalletCard: MockWalletCard,
            QuizList: MockQuizList,
            PathwayList: MockPathwayList,
            RouterLink: true
        }
      }
    });
    
    await flushPromises(); 

    const shopButton = wrapper.find('.shop-button');
    await shopButton.trigger('click');

    expect(routerPushSpy).toHaveBeenCalledWith('/shop');
  });

});