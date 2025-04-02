import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import ProfileView from '../ProfileView.vue';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
import type { WalletInfo } from '@/api/dashboard';

// Mock del router
const routes = [
  { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
  { path: '/dashboard', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
  { path: '/profile', name: 'Profile', component: ProfileView },
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Mock dati utente
const mockUser = { 
    id: 1, 
    first_name: 'Mario', 
    last_name: 'Rossi', 
    student_code: 'MARROS01',
    full_name: 'Mario Rossi', 
    teacher: 1,             
    teacher_username: 'prof', 
    is_active: true,        
    created_at: new Date().toISOString() 
};

// Mock dati wallet
const mockWallet: WalletInfo = {
    current_points: 250,
    recent_transactions: []
};


describe('ProfileView.vue', () => {
  let authStore: ReturnType<typeof useAuthStore>;
  let dashboardStore: ReturnType<typeof useDashboardStore>;

  beforeEach(async () => {
    setActivePinia(createPinia());
    authStore = useAuthStore();
    dashboardStore = useDashboardStore();
    
    // Imposta stato iniziale store
    authStore.user = mockUser;
    authStore.isAuthenticated = true; // Assicurati che sia autenticato
    dashboardStore.wallet = mockWallet; // Inizia con wallet già caricato per alcuni test

    router.push('/profile'); 
    await router.isReady(); 
    vi.clearAllMocks(); // Pulisci i mock tra i test
  });

  it('renders user information correctly from authStore', () => {
    const wrapper = mount(ProfileView, {
      global: { plugins: [router] }
    });

    const infoItems = wrapper.findAll('.info-card .info-item');
    expect(infoItems.length).toBeGreaterThanOrEqual(2); // Almeno nome e codice

    // Verifica Nome
    const nameItem = infoItems[0];
    expect(nameItem.find('.info-label').text()).toBe('Nome:');
    // Usa il getter userFullName che viene calcolato dallo store
    expect(nameItem.find('.info-value').text()).toBe(authStore.userFullName); 

    // Verifica Codice Studente
    const codeItem = infoItems[1];
    expect(codeItem.find('.info-label').text()).toBe('Codice Studente:');
    expect(codeItem.find('.info-value').text()).toBe(mockUser.student_code);
  });

  it('renders current points correctly from dashboardStore', () => {
     const wrapper = mount(ProfileView, {
      global: { plugins: [router] }
    });

    const pointsItem = wrapper.find('.stats-card .info-item');
    expect(pointsItem.find('.info-label').text()).toBe('Punti Attuali:');
    expect(pointsItem.find('.info-value.points').text()).toContain(mockWallet.current_points.toString());
  });

  it('calls dashboardStore.loadWallet on mount if wallet is initially null', async () => {
    // Resetta lo stato del wallet per questo test
    dashboardStore.wallet = null;
    const fetchWalletSpy = vi.spyOn(dashboardStore, 'fetchWallet'); // Corretto: usa fetchWallet

    mount(ProfileView, {
      global: { plugins: [router] }
    });

    // Attende che onMounted venga eseguito
    await flushPromises();

    expect(fetchWalletSpy).toHaveBeenCalledTimes(1); // Corretto: verifica fetchWalletSpy
  });

   it('does not call dashboardStore.fetchWallet on mount if wallet already exists', async () => { // Corretto nome test
    // Lo stato iniziale ha già il wallet nel beforeEach
    const fetchWalletSpy = vi.spyOn(dashboardStore, 'fetchWallet'); // Corretto: usa fetchWallet

    mount(ProfileView, {
      global: { plugins: [router] }
    });

    await flushPromises();

    expect(fetchWalletSpy).not.toHaveBeenCalled(); // Corretto: verifica fetchWalletSpy
  });


  it('navigates back to dashboard on button click', async () => {
    const routerPushSpy = vi.spyOn(router, 'push');
     const wrapper = mount(ProfileView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    await wrapper.find('.back-button').trigger('click');
    expect(routerPushSpy).toHaveBeenCalledWith('/dashboard');
  });

  it('renders placeholder for other stats', () => {
     const wrapper = mount(ProfileView, {
      global: { plugins: [router] }
    });
     expect(wrapper.find('.stats-placeholder').exists()).toBe(true);
     expect(wrapper.find('.stats-placeholder').text()).toContain('Altre statistiche saranno disponibili prossimamente');
  });

});