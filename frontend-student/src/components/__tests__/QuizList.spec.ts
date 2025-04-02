import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createRouter, createWebHistory } from 'vue-router';
import QuizList from '../QuizList.vue'; // Adatta il percorso
import type { Quiz } from '@/api/dashboard';

// Mock del router
const routes = [
  { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
  { path: '/quiz/:quizId/start', name: 'quiz-start-attempt', component: { template: '<div>Start</div>' }, props: true },
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Mock dati quiz
const mockQuizzes: Quiz[] = [
  { 
    id: 1, 
    title: 'Quiz Facile', 
    description: 'Descrizione facile', 
    metadata: { difficulty: 'Facile', points_on_completion: 10 }, 
    latest_attempt: null, // Non iniziato
    available_from: null, 
    available_until: null 
  },
  { 
    id: 2, 
    title: 'Quiz Medio', 
    description: 'Descrizione media', 
    metadata: { subject: 'Storia', points_on_completion: 20 },
    latest_attempt: {
        id: 10,
        status: 'in_progress',
        score: null,
        started_at: new Date(Date.now() - 3600000).toISOString(), // Aggiunto (1 ora fa)
        completed_at: null // Aggiunto
    }, // In corso
    available_from: new Date(Date.now() - 86400000).toISOString(), // Disponibile da ieri
    available_until: null 
  },
   { 
    id: 3, 
    title: 'Quiz Difficile', 
    description: 'Descrizione difficile', 
    metadata: {},
    latest_attempt: {
        id: 11,
        status: 'completed',
        score: 0.9,
        started_at: new Date(Date.now() - 7200000).toISOString(), // Aggiunto (2 ore fa)
        completed_at: new Date(Date.now() - 3600000).toISOString() // Aggiunto (1 ora fa)
    }, // Completato
    available_from: null, 
    available_until: new Date(Date.now() + 86400000).toISOString() // Disponibile fino a domani
  },
];


describe('QuizList.vue', () => {
  beforeEach(async () => {
    // Resetta il router prima di ogni test
    router.push('/'); // Vai a una rotta neutra
    await router.isReady();
    vi.clearAllMocks(); // Pulisci i mock se ce ne fossero
  });

  it('renders title and empty message when no quizzes are provided', () => {
    const title = 'Test Title';
    const emptyMessage = 'Nessun quiz qui.';
    const wrapper = mount(QuizList, {
      props: { quizzes: [], title, emptyMessage, loading: false },
      global: { plugins: [router] }
    });

    expect(wrapper.find('h2').text()).toBe(title);
    expect(wrapper.find('.empty-message').exists()).toBe(true);
    expect(wrapper.find('.empty-message').text()).toBe(emptyMessage);
    expect(wrapper.find('.quiz-list').exists()).toBe(false);
  });

  it('renders loading indicator when loading is true', () => {
     const wrapper = mount(QuizList, {
      props: { quizzes: [], title: 'Loading Test', emptyMessage: '', loading: true },
      global: { plugins: [router] }
    });
     expect(wrapper.find('.loading-indicator').exists()).toBe(true);
     expect(wrapper.find('.loading-indicator').text()).toContain('Caricamento');
     expect(wrapper.find('.empty-message').exists()).toBe(false);
     expect(wrapper.find('.quiz-list').exists()).toBe(false);
  });

  it('renders list of quizzes with correct details', () => {
     const wrapper = mount(QuizList, {
      props: { quizzes: mockQuizzes, title: 'Lista Quiz', emptyMessage: '', loading: false },
      global: { plugins: [router] }
    });

    const items = wrapper.findAll('.quiz-item');
    expect(items.length).toBe(mockQuizzes.length);

    // Controlla primo quiz (Non iniziato)
    const item1 = items[0];
    expect(item1.find('h3').text()).toBe(mockQuizzes[0].title);
    expect(item1.find('.quiz-description').text()).toBe(mockQuizzes[0].description);
    expect(item1.find('.quiz-status').text()).toBe('Non iniziato');
    expect(item1.find('.quiz-status').classes()).toContain('status-not-started');
    expect(item1.find('.quiz-difficulty').text()).toContain('Facile');
    expect(item1.find('.quiz-points').text()).toContain('10');

    // Controlla secondo quiz (In corso)
    const item2 = items[1];
    expect(item2.find('h3').text()).toBe(mockQuizzes[1].title);
    expect(item2.find('.quiz-status').text()).toBe('In corso');
    expect(item2.find('.quiz-status').classes()).toContain('status-in-progress');
    expect(item2.find('.quiz-subject').text()).toContain('Storia');
    expect(item2.find('.quiz-available-from').exists()).toBe(true);

     // Controlla terzo quiz (Completato)
    const item3 = items[2];
    expect(item3.find('h3').text()).toBe(mockQuizzes[2].title);
    expect(item3.find('.quiz-status').text()).toContain('Completato (90%)'); // Verifica formattazione punteggio
    expect(item3.find('.quiz-status').classes()).toContain('status-completed');
    expect(item3.find('.quiz-available-until').exists()).toBe(true);
  });

  it('shows "Start Quiz" button only when showStartButton is true', () => {
     const wrapperWithButton = mount(QuizList, {
      props: { quizzes: [mockQuizzes[0]], title: 'Test', emptyMessage: '', loading: false, showStartButton: true },
      global: { plugins: [router] }
    });
     expect(wrapperWithButton.find('.quiz-item .start-quiz-button').exists()).toBe(true);

     const wrapperWithoutButton = mount(QuizList, {
      props: { quizzes: [mockQuizzes[0]], title: 'Test', emptyMessage: '', loading: false, showStartButton: false }, // o omesso
      global: { plugins: [router] }
    });
     expect(wrapperWithoutButton.find('.quiz-item .start-quiz-button').exists()).toBe(false);
  });

  it('navigates to start attempt route on "Start Quiz" button click', async () => {
    const routerPushSpy = vi.spyOn(router, 'push');
    const wrapper = mount(QuizList, {
      props: { quizzes: [mockQuizzes[0]], title: 'Test', emptyMessage: '', loading: false, showStartButton: true },
      global: { plugins: [router] }
    });

    const startButton = wrapper.find('.start-quiz-button');
    await startButton.trigger('click');

    expect(routerPushSpy).toHaveBeenCalledTimes(1);
    expect(routerPushSpy).toHaveBeenCalledWith({ name: 'quiz-start-attempt', params: { quizId: mockQuizzes[0].id } });
  });

  // Test per il click sull'item (se la logica viene mantenuta/modificata)
  /*
  it('navigates somewhere (e.g., details) when quiz item is clicked (if applicable)', async () => {
    const routerPushSpy = vi.spyOn(router, 'push');
    const wrapper = mount(QuizList, {
      props: { quizzes: [mockQuizzes[1]], title: 'Test', emptyMessage: '', loading: false }, // Quiz in corso
      global: { plugins: [router] }
    });

    const quizItem = wrapper.find('.quiz-item');
    await quizItem.trigger('click');

    // Modifica l'aspettativa in base alla logica di navigazione desiderata per il click sull'item
    // expect(routerPushSpy).toHaveBeenCalledWith(`/quiz/${mockQuizzes[1].id}`); // Esempio: navigazione ai dettagli
    expect(routerPushSpy).toHaveBeenCalled(); // Verifica almeno che la navigazione sia avvenuta
  });
  */

});