import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import QuizResultView from '../QuizResultView.vue';
import QuizService from '@/api/quiz'; // Servizio reale per mock
import type { AttemptDetails, Question } from '@/api/quiz'; // Rimosso AnswerOption dall'import

// Mock del router
const routes = [
  { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
  { path: '/dashboard', name: 'dashboard', component: { template: '<div>Dashboard</div>' } },
  { path: '/quiz/result/:attemptId', name: 'QuizResult', component: QuizResultView, props: true },
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Mock del servizio QuizService
vi.mock('@/api/quiz', () => ({
  default: {
    getAttemptDetails: vi.fn(),
    // Mock altre funzioni se non servono qui
  }
}));

// Definisci localmente il tipo AnswerOption basato sulla struttura usata
interface AnswerOption {
  id: number;
  text: string;
  order: number;
  is_correct?: boolean; // Aggiunto opzionale basato sul mock
}

// Mock dati
const mockAnswerOptions: AnswerOption[] = [
    { id: 1, text: 'Opzione A', order: 1, is_correct: false }, // Aggiunto is_correct
    { id: 2, text: 'Opzione B', order: 2, is_correct: true }, // Aggiunto is_correct
];

const mockQuestions: Question[] = [
  { id: 10, text: 'Domanda 1 (MC Single)', question_type: 'multiple_choice_single', order: 1, metadata: {}, answer_options: mockAnswerOptions },
  { id: 11, text: 'Domanda 2 (True/False)', question_type: 'true_false', order: 2, metadata: {} },
  { id: 12, text: 'Domanda 3 (Open Manual)', question_type: 'open_answer_manual', order: 3, metadata: {} },
];

const mockAttemptDetails: AttemptDetails = {
  id: 50,
  quiz: { id: 1, title: 'Quiz Completato', description: 'Descrizione Risultati', metadata: {} },
  started_at: new Date(Date.now() - 600000).toISOString(), // 10 min fa
  completed_at: new Date().toISOString(),
  score: 0.75,
  points_earned: 15,
  status: 'completed',
  questions: mockQuestions,
  student_answers: [
    { question_id: 10, selected_answers: { answer_option_id: 2 }, is_correct: true, score: null, answered_at: new Date().toISOString() }, // Risposta corretta
    { question_id: 11, selected_answers: { is_true: false }, is_correct: false, score: null, answered_at: new Date().toISOString() }, // Risposta errata
    { question_id: 12, selected_answers: { text: 'Risposta aperta' }, is_correct: null, score: null, answered_at: new Date().toISOString() }, // In attesa
  ],
};

const mockPendingAttemptDetails: AttemptDetails = {
    ...mockAttemptDetails,
    status: 'pending_manual_grading',
    score: null, // Punteggio non ancora calcolato
    points_earned: null, // Punti non ancora assegnati
    completed_at: new Date().toISOString(), // Ma completato
};


describe('QuizResultView.vue', () => {
  beforeEach(async () => {
    setActivePinia(createPinia());
    // Naviga alla rotta corretta prima di ogni test
    router.push('/quiz/result/50'); // Usa l'ID del mock attempt
    await router.isReady(); 
    vi.clearAllMocks();
    // Mock di base per getAttemptDetails
    vi.mocked(QuizService.getAttemptDetails).mockResolvedValue(mockAttemptDetails);
  });

  it('renders loading state initially and fetches results', async () => {
    const wrapper = mount(QuizResultView, {
      global: { plugins: [router] }
    });

    expect(wrapper.find('.loading').exists()).toBe(true);
    expect(QuizService.getAttemptDetails).toHaveBeenCalledTimes(1);
    expect(QuizService.getAttemptDetails).toHaveBeenCalledWith(50); // Verifica ID dalla rotta

    await flushPromises(); // Attende caricamento

    expect(wrapper.find('.loading').exists()).toBe(false);
    expect(wrapper.find('.results-container').exists()).toBe(true);
  });

  it('displays general attempt information correctly', async () => {
     const wrapper = mount(QuizResultView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.find('h2').text()).toBe(mockAttemptDetails.quiz.title);
    expect(wrapper.find('.results-container > p').text()).toContain(mockAttemptDetails.quiz.description);
    expect(wrapper.find('.results-container > p').text()).toContain(mockAttemptDetails.status);
    expect(wrapper.find('.summary-scores strong').text()).toContain(mockAttemptDetails.score?.toString());
    expect(wrapper.find('.summary-scores').text()).toContain(mockAttemptDetails.points_earned?.toString());
  });

  it('displays pending status correctly', async () => {
    vi.mocked(QuizService.getAttemptDetails).mockResolvedValue(mockPendingAttemptDetails);
     const wrapper = mount(QuizResultView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.find('.results-container > p').text()).toContain(mockPendingAttemptDetails.status);
    // Verifica che il messaggio specifico per pending sia mostrato
    expect(wrapper.find('.summary-scores.pending').exists()).toBe(true);
    expect(wrapper.find('.summary-scores.pending').text()).toContain('correzione manuale');
    // Verifica che punteggio e punti non siano mostrati
    expect(wrapper.text()).not.toContain('Punteggio Finale:');
    expect(wrapper.text()).not.toContain('Punti Guadagnati:');
  });


  it('displays details for each question and answer', async () => {
     const wrapper = mount(QuizResultView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    const answerItems = wrapper.findAll('.answer-item');
    expect(answerItems.length).toBe(mockQuestions.length);

    // Domanda 1 (MC Single - Corretta)
    const item1 = answerItems[0];
    expect(item1.find('.question-text strong').text()).toContain(mockQuestions[0].text);
    const answer1 = item1.find('.student-answer');
    expect(answer1.classes()).toContain('correct-answer');
    expect(answer1.text()).toContain('Tua Risposta: Opzione B'); // Testo dell'opzione con id 2
    expect(answer1.text()).toContain('Esito: Corretta');

    // Domanda 2 (True/False - Errata)
    const item2 = answerItems[1];
    expect(item2.find('.question-text strong').text()).toContain(mockQuestions[1].text);
    const answer2 = item2.find('.student-answer');
    expect(answer2.classes()).toContain('incorrect-answer');
    expect(answer2.text()).toContain('Tua Risposta: Falso');
    expect(answer2.text()).toContain('Esito: Errata');

    // Domanda 3 (Open Manual - Pending)
    const item3 = answerItems[2];
    expect(item3.find('.question-text strong').text()).toContain(mockQuestions[2].text);
    const answer3 = item3.find('.student-answer');
    expect(answer3.classes()).toContain('pending-answer');
    expect(answer3.text()).toContain(`Tua Risposta: ${mockAttemptDetails.student_answers[2].selected_answers.text}`);
    expect(answer3.text()).toContain('Esito: In attesa di correzione');
  });

  it('displays error message if fetching results fails', async () => {
    const errorMessage = 'Errore API Risultati';
    vi.mocked(QuizService.getAttemptDetails).mockRejectedValue(new Error(errorMessage));

    const wrapper = mount(QuizResultView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.find('.error-message').exists()).toBe(true);
    expect(wrapper.find('.error-message').text()).toContain('Impossibile caricare i risultati del quiz.');
  });

  it('navigates back to dashboard on button click', async () => {
    const routerPushSpy = vi.spyOn(router, 'push');
     const wrapper = mount(QuizResultView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    await wrapper.find('.back-button').trigger('click');
    expect(routerPushSpy).toHaveBeenCalledWith('/dashboard');
  });

});