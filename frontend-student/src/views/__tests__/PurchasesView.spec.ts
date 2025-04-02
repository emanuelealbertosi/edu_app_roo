import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import PurchasesView from '../PurchasesView.vue';
import RewardsService from '@/api/rewards'; // Servizio reale per mock
import type { RewardPurchase, Reward } from '@/api/rewards';

// Mock del router
const routes = [
  { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
  { path: '/shop', name: 'shop', component: { template: '<div>Shop</div>' } }, // Serve per il link
  { path: '/purchases', name: 'purchases', component: PurchasesView },
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Mock del servizio RewardsService
vi.mock('@/api/rewards', () => ({
  default: {
    getPurchaseHistory: vi.fn(),
    // Mock altre funzioni se non servono qui
  }
}));

// Mock dati
const mockReward1: Reward = { id: 1, name: 'Adesivo', description: 'Desc1', type: 'digital', cost_points: 50, metadata: {}, is_active: true };
const mockReward2: Reward = { id: 2, name: 'Matita', description: 'Desc2', type: 'real_world_tracked', cost_points: 100, metadata: {}, is_active: true };

const mockPurchases: RewardPurchase[] = [
  { id: 10, reward: mockReward1, points_spent: 50, purchased_at: new Date(Date.now() - 86400000).toISOString(), status: 'delivered', delivered_at: new Date().toISOString(), delivery_notes: null }, // Ieri
  { id: 11, reward: mockReward2, points_spent: 100, purchased_at: new Date().toISOString(), status: 'purchased', delivered_at: null, delivery_notes: null }, // Oggi
];


describe('PurchasesView.vue', () => {
  beforeEach(async () => {
    setActivePinia(createPinia());
    router.push('/purchases'); 
    await router.isReady(); 
    vi.clearAllMocks();
    // Mock di base per getPurchaseHistory
    vi.mocked(RewardsService.getPurchaseHistory).mockResolvedValue([...mockPurchases]);
  });

  it('renders loading state initially and fetches purchase history', async () => {
    const wrapper = mount(PurchasesView, {
      global: { plugins: [router] }
    });

    expect(wrapper.find('.loading').exists()).toBe(true);
    expect(RewardsService.getPurchaseHistory).toHaveBeenCalledTimes(1);

    await flushPromises(); // Attende caricamento

    expect(wrapper.find('.loading').exists()).toBe(false);
    expect(wrapper.find('.purchases-table').exists()).toBe(true);
  });

  it('displays purchase history in the table correctly', async () => {
     const wrapper = mount(PurchasesView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    const tableRows = wrapper.findAll('.purchases-table tbody tr');
    expect(tableRows.length).toBe(mockPurchases.length);

    // Controlla la prima riga (acquisto più vecchio)
    const firstRowCells = tableRows[0].findAll('td');
    expect(firstRowCells[0].text()).toBe(mockPurchases[0].reward.name);
    expect(firstRowCells[1].text()).toBe(mockPurchases[0].points_spent.toString());
    // expect(firstRowCells[2].text()).toBe(/* Formatted date */); // Il formato data è complesso da testare esattamente
    expect(firstRowCells[3].find('.status-badge').text()).toBe('Consegnato');
    expect(firstRowCells[3].find('.status-badge').classes()).toContain('status-delivered');
    // expect(firstRowCells[4].text()).toBe(/* Formatted date */);

     // Controlla la seconda riga (acquisto più recente)
    const secondRowCells = tableRows[1].findAll('td');
    expect(secondRowCells[0].text()).toBe(mockPurchases[1].reward.name);
    expect(secondRowCells[1].text()).toBe(mockPurchases[1].points_spent.toString());
    expect(secondRowCells[3].find('.status-badge').text()).toBe('Acquistato (In attesa)');
    expect(secondRowCells[3].find('.status-badge').classes()).toContain('status-purchased');
    expect(secondRowCells[4].text()).toBe('N/D'); // Data consegna non presente
  });

  it('displays empty message when there is no purchase history', async () => {
    vi.mocked(RewardsService.getPurchaseHistory).mockResolvedValue([]); // Sovrascrive il mock per restituire array vuoto
     const wrapper = mount(PurchasesView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.find('.purchases-table').exists()).toBe(false);
    expect(wrapper.find('.empty-message').exists()).toBe(true);
    expect(wrapper.find('.empty-message').text()).toContain('Non hai ancora effettuato nessun acquisto.');
    // Verifica la presenza del link allo shop
    expect(wrapper.find('.go-to-shop-link').exists()).toBe(true);
    expect(wrapper.find('.go-to-shop-link').attributes('to')).toBe('/shop');
  });

  it('displays error message if fetching history fails', async () => {
    const errorMessage = 'Errore API Storico';
    vi.mocked(RewardsService.getPurchaseHistory).mockRejectedValue(new Error(errorMessage));

    const wrapper = mount(PurchasesView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.find('.error-message').exists()).toBe(true);
    expect(wrapper.find('.error-message').text()).toContain('Impossibile caricare lo storico degli acquisti.');
  });

});