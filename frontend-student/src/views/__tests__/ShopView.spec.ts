import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import ShopView from '../ShopView.vue';
import { useAuthStore } from '@/stores/auth';
import { useDashboardStore } from '@/stores/dashboard';
import RewardsService from '@/api/rewards'; // Importa il servizio reale per fare il mock
import type { Reward, RewardPurchase } from '@/api/rewards';
import type { WalletInfo } from '@/api/dashboard';

// Mock del router
const routes = [
  { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
  { path: '/dashboard', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
  { path: '/shop', name: 'shop', component: ShopView },
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Mock del servizio RewardsService
vi.mock('@/api/rewards', () => ({
  default: {
    getAvailableRewards: vi.fn(),
    purchaseReward: vi.fn(),
    // Mock altre funzioni se necessario
  }
}));

// Mock dati
const mockRewards: Reward[] = [
  { id: 1, name: 'Adesivo Digitale', description: 'Un bell\'adesivo', type: 'digital', cost_points: 50, metadata: {}, is_active: true },
  { id: 2, name: 'Matita Speciale', description: 'Una matita unica', type: 'real_world_tracked', cost_points: 200, metadata: { image_url: 'test.jpg' }, is_active: true },
  { id: 3, name: 'Bonus Tempo', description: '30 min extra', type: 'digital', cost_points: 100, metadata: {}, is_active: true },
];

const mockPurchase: RewardPurchase = {
    id: 1,
    reward: mockRewards[0],
    points_spent: 50,
    purchased_at: new Date().toISOString(),
    status: 'purchased',
    delivered_at: null,
    delivery_notes: null,
};

describe('ShopView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    router.push('/shop');
    // Resetta i mock prima di ogni test
    vi.clearAllMocks(); 
    // Mock implementazione base per getAvailableRewards
    vi.mocked(RewardsService.getAvailableRewards).mockResolvedValue([...mockRewards]); 
  });

  it('renders loading state initially and fetches rewards', async () => {
    const wrapper = mount(ShopView, {
      global: { plugins: [router] }
    });

    expect(wrapper.find('.loading').exists()).toBe(true);
    expect(RewardsService.getAvailableRewards).toHaveBeenCalledTimes(1);

    // Attende il caricamento
    await flushPromises();

    expect(wrapper.find('.loading').exists()).toBe(false);
    expect(wrapper.findAll('.reward-card').length).toBe(mockRewards.length);
  });

  it('displays available rewards correctly', async () => {
     const wrapper = mount(ShopView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    const rewardCards = wrapper.findAll('.reward-card');
    expect(rewardCards.length).toBe(mockRewards.length);

    // Controlla i dettagli della prima card
    const firstCard = rewardCards[0];
    expect(firstCard.find('h3').text()).toBe(mockRewards[0].name);
    expect(firstCard.find('.reward-description').text()).toBe(mockRewards[0].description);
    expect(firstCard.find('.reward-cost strong').text()).toBe(mockRewards[0].cost_points.toString());
    expect(firstCard.find('.reward-image-placeholder').exists()).toBe(true); // Prima ricompensa senza immagine

     // Controlla i dettagli della seconda card (con immagine)
    const secondCard = rewardCards[1];
    expect(secondCard.find('h3').text()).toBe(mockRewards[1].name);
    expect(secondCard.find('.reward-image').exists()).toBe(true);
    expect(secondCard.find('.reward-image').attributes('src')).toBe(mockRewards[1].metadata.image_url);
  });

  it('displays current points from dashboard store', async () => {
    const dashboardStore = useDashboardStore();
    dashboardStore.wallet = { current_points: 150, recent_transactions: [] };

    const wrapper = mount(ShopView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.find('.current-points strong').text()).toBe('150');
  });

  it('disables purchase button if points are insufficient', async () => {
    const dashboardStore = useDashboardStore();
    // Punti insufficienti per la seconda ricompensa (costo 200)
    dashboardStore.wallet = { current_points: 150, recent_transactions: [] }; 

    const wrapper = mount(ShopView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    const rewardCards = wrapper.findAll('.reward-card');
    const firstPurchaseButton = rewardCards[0].find('.purchase-button');
    const secondPurchaseButton = rewardCards[1].find('.purchase-button');

    expect(firstPurchaseButton.attributes('disabled')).toBeUndefined(); // Abbastanza punti per la prima
    expect(secondPurchaseButton.attributes('disabled')).toBeDefined(); // Non abbastanza per la seconda
  });

  it('calls purchaseReward on button click after confirmation', async () => {
    const dashboardStore = useDashboardStore();
    dashboardStore.wallet = { current_points: 250, recent_transactions: [] }; // Punti sufficienti
    // Mock della funzione confirm per restituire sempre true
    window.confirm = vi.fn(() => true); 
    // Mock della funzione purchaseReward per restituire un acquisto
    vi.mocked(RewardsService.purchaseReward).mockResolvedValue(mockPurchase);
    // Spy sulla action loadDashboard per verificare che venga chiamata
    const loadDashboardSpy = vi.spyOn(dashboardStore, 'loadDashboard');


    const wrapper = mount(ShopView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    const firstPurchaseButton = wrapper.findAll('.reward-card')[0].find('.purchase-button');
    await firstPurchaseButton.trigger('click');

    // Verifica che confirm sia stato chiamato
    expect(window.confirm).toHaveBeenCalledTimes(1);
    // Verifica che purchaseReward sia stato chiamato con l'ID corretto
    expect(RewardsService.purchaseReward).toHaveBeenCalledWith(mockRewards[0].id);

    // Attende la risoluzione della promise di acquisto
    await flushPromises();

    // Verifica che il messaggio di successo sia mostrato (o che l'alert sia stato chiamato se non modificato)
    // Qui assumiamo che l'alert sia stato rimosso come nei passi precedenti
    expect(wrapper.find('.success-message').exists()).toBe(true);
    expect(wrapper.find('.success-message').text()).toContain(`Ricompensa "${mockRewards[0].name}" acquistata con successo!`);

    // Verifica che loadDashboard sia stato chiamato per aggiornare i punti
    expect(loadDashboardSpy).toHaveBeenCalledTimes(1);
  });

  it('does not call purchaseReward if confirmation is cancelled', async () => {
    const dashboardStore = useDashboardStore();
    dashboardStore.wallet = { current_points: 250, recent_transactions: [] };
    // Mock confirm per restituire false
    window.confirm = vi.fn(() => false); 

    const wrapper = mount(ShopView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    const firstPurchaseButton = wrapper.findAll('.reward-card')[0].find('.purchase-button');
    await firstPurchaseButton.trigger('click');

    expect(window.confirm).toHaveBeenCalledTimes(1);
    // Verifica che purchaseReward NON sia stato chiamato
    expect(RewardsService.purchaseReward).not.toHaveBeenCalled();
  });

   it('displays an error message if purchase fails', async () => {
    const dashboardStore = useDashboardStore();
    dashboardStore.wallet = { current_points: 250, recent_transactions: [] };
    window.confirm = vi.fn(() => true);
    // Mock purchaseReward per fallire con un messaggio specifico
    const errorMessage = 'Punti insufficienti.';
    vi.mocked(RewardsService.purchaseReward).mockRejectedValue({ response: { data: { detail: errorMessage } } });

    const wrapper = mount(ShopView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    const firstPurchaseButton = wrapper.findAll('.reward-card')[0].find('.purchase-button');
    await firstPurchaseButton.trigger('click');

    expect(RewardsService.purchaseReward).toHaveBeenCalledWith(mockRewards[0].id);
    await flushPromises(); // Attende il fallimento

    // Verifica che il messaggio di errore sia mostrato
    expect(wrapper.find('.error-message.purchase-feedback').exists()).toBe(true);
    expect(wrapper.find('.error-message.purchase-feedback').text()).toContain(errorMessage);
  });

});