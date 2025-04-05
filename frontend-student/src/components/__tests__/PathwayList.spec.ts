import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createRouter, createWebHistory } from 'vue-router';
import PathwayList from '../PathwayList.vue'; // Adatta il percorso
import type { Pathway } from '@/api/dashboard';

// Mock del router
const routes = [
  { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
  { path: '/pathway/result/:pathwayId', name: 'PathwayResult', component: { template: '<div>Result</div>' }, props: true },
  // Aggiungere rotta per pathway-details se si testa quel click
  // { path: '/pathway/:id', name: 'pathway-details', component: { template: '<div>Details</div>' }, props: true },
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Mock dati percorsi
const mockPathways: Pathway[] = [
  { 
    id: 1, 
    title: 'Percorso Base', 
    description: 'Introduzione', 
    metadata: { points_on_completion: 50 },
    latest_progress: null, // Non iniziato
    quiz_details: [] // Aggiunto per soddisfare il tipo
  },
  { 
    id: 2, 
    title: 'Percorso Intermedio', 
    description: 'Approfondimento', 
    metadata: {},
    // Aggiunti campi mancanti da latest_progress in dashboard.ts
    latest_progress: { id: 1, status: 'in_progress', last_completed_quiz_order: 1, completed_orders: [0, 1], started_at: new Date().toISOString(), completed_at: null, points_earned: null },
    quiz_details: [{id: 1, quiz_id: 10, quiz_title: 'Quiz 1', order: 0}, {id: 2, quiz_id: 11, quiz_title: 'Quiz 2', order: 1}] // Aggiunto per soddisfare il tipo (esempio)
  },
   { 
    id: 3, 
    title: 'Percorso Avanzato', 
    description: 'Maestria', 
    metadata: { points_on_completion: 100 },
    // Aggiunti campi mancanti da latest_progress in dashboard.ts
    latest_progress: { id: 2, status: 'completed', last_completed_quiz_order: 4, completed_orders: [0, 1, 2, 3, 4], started_at: new Date().toISOString(), completed_at: new Date().toISOString(), points_earned: 100 },
    quiz_details: [{id: 3, quiz_id: 20, quiz_title: 'Quiz A', order: 0}] // Aggiunto per soddisfare il tipo (esempio)
  },
];


describe('PathwayList.vue', () => {
  beforeEach(async () => {
    router.push('/'); 
    await router.isReady();
    vi.clearAllMocks(); 
  });

  it('renders title and empty message when no pathways are provided', () => {
    const title = 'Test Title Percorsi';
    const emptyMessage = 'Nessun percorso qui.';
    const wrapper = mount(PathwayList, {
      props: { pathways: [], title, emptyMessage, loading: false },
      global: { plugins: [router] }
    });

    expect(wrapper.find('h2').text()).toBe(title);
    expect(wrapper.find('.empty-message').exists()).toBe(true);
    expect(wrapper.find('.empty-message').text()).toBe(emptyMessage);
    expect(wrapper.find('.pathway-list').exists()).toBe(false);
  });

  it('renders loading indicator when loading is true', () => {
     const wrapper = mount(PathwayList, {
      props: { pathways: [], title: 'Loading Test', emptyMessage: '', loading: true },
      global: { plugins: [router] }
    });
     expect(wrapper.find('.loading-indicator').exists()).toBe(true);
     expect(wrapper.find('.loading-indicator').text()).toContain('Caricamento');
     expect(wrapper.find('.empty-message').exists()).toBe(false);
     expect(wrapper.find('.pathway-list').exists()).toBe(false);
  });

  it('renders list of pathways with correct details and progress', () => {
     const wrapper = mount(PathwayList, {
      props: { pathways: mockPathways, title: 'Lista Percorsi', emptyMessage: '', loading: false },
      global: { plugins: [router] }
    });

    const items = wrapper.findAll('.pathway-item');
    expect(items.length).toBe(mockPathways.length);

    // Controlla primo percorso (Non iniziato)
    const item1 = items[0];
    expect(item1.find('h3').text()).toBe(mockPathways[0].title);
    expect(item1.find('.pathway-description').text()).toBe(mockPathways[0].description);
    expect(item1.find('.pathway-status').text()).toBe('Non iniziato');
    expect(item1.find('.pathway-status').classes()).toContain('status-not-started');
    expect(item1.find('.pathway-progress-label').text()).toContain('0%');
    expect(item1.find('.pathway-progress-fill').attributes('style')).toContain('width: 0%');
    expect(item1.find('.pathway-points').text()).toContain('50');

    // Controlla secondo percorso (In corso)
    const item2 = items[1];
    expect(item2.find('h3').text()).toBe(mockPathways[1].title);
    expect(item2.find('.pathway-status').text()).toBe('In corso');
    expect(item2.find('.pathway-status').classes()).toContain('status-in-progress');
    expect(item2.find('.pathway-progress-label').text()).toContain('40%'); // (1+1)*20
    expect(item2.find('.pathway-progress-fill').attributes('style')).toContain('width: 40%');

     // Controlla terzo percorso (Completato)
    const item3 = items[2];
    expect(item3.find('h3').text()).toBe(mockPathways[2].title);
    expect(item3.find('.pathway-status').text()).toBe('Completato');
    expect(item3.find('.pathway-status').classes()).toContain('status-completed');
    expect(item3.find('.pathway-progress-label').text()).toContain('100%');
    expect(item3.find('.pathway-progress-fill').attributes('style')).toContain('width: 100%');
    expect(item3.find('.pathway-completed-at').exists()).toBe(true);
    expect(item3.find('.pathway-points-earned').text()).toContain('100');
  });

  it('shows "View Results" link only when showResultLink is true and pathway is completed', () => {
     // Test con link visibile
     const wrapperWithLink = mount(PathwayList, {
      props: { pathways: [mockPathways[2]], title: 'Test', emptyMessage: '', loading: false, showResultLink: true }, // Percorso completato
      global: { plugins: [router] }
    });
     expect(wrapperWithLink.find('.pathway-item .view-results-link').exists()).toBe(true);

     // Test con link non visibile (percorso non completo)
     const wrapperInProgress = mount(PathwayList, {
      props: { pathways: [mockPathways[1]], title: 'Test', emptyMessage: '', loading: false, showResultLink: true }, // Percorso in corso
      global: { plugins: [router] }
    });
     expect(wrapperInProgress.find('.pathway-item .view-results-link').exists()).toBe(false);

     // Test con link non visibile (prop showResultLink è false)
     const wrapperWithoutProp = mount(PathwayList, {
      props: { pathways: [mockPathways[2]], title: 'Test', emptyMessage: '', loading: false, showResultLink: false }, // Percorso completato ma prop false
      global: { plugins: [router] }
    });
     expect(wrapperWithoutProp.find('.pathway-item .view-results-link').exists()).toBe(false);
  });

  it('navigates to result route on "View Results" link click', async () => {
    const routerPushSpy = vi.spyOn(router, 'push');
    const wrapper = mount(PathwayList, {
      props: { pathways: [mockPathways[2]], title: 'Test', emptyMessage: '', loading: false, showResultLink: true }, // Percorso completato
      global: { plugins: [router] }
    });

    const resultLink = wrapper.find('.view-results-link');
    await resultLink.trigger('click');

    expect(routerPushSpy).toHaveBeenCalledTimes(1);
    expect(routerPushSpy).toHaveBeenCalledWith({ name: 'PathwayResult', params: { pathwayId: mockPathways[2].id } });
  });

  it('navigates somewhere else (TBD) when pathway item is clicked (if not completed or no result link)', async () => {
    const routerPushSpy = vi.spyOn(router, 'push');
    const wrapper = mount(PathwayList, {
      props: { pathways: [mockPathways[1]], title: 'Test', emptyMessage: '', loading: false, showResultLink: true }, // Percorso in corso
      global: { plugins: [router] }
    });

    const pathwayItem = wrapper.find('.pathway-item');
    await pathwayItem.trigger('click');

    // Verifica che la navigazione sia avvenuta (anche se la destinazione è un console.warn per ora)
    expect(routerPushSpy).not.toHaveBeenCalled(); // Non dovrebbe navigare perché la rotta dettagli non è gestita
    // Potremmo testare il console.warn se necessario, ma è più complesso
  });

});