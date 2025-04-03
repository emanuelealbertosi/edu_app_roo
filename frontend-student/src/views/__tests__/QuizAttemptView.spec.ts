import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import QuizAttemptView from '../QuizAttemptView.vue';
import QuizService from '@/api/quiz'; // Servizio reale per mock
import type { QuizAttempt, Question, AttemptDetails } from '@/api/quiz';

// Mock dei componenti domanda (non serve testare la loro logica interna qui)
const MockMcSingle = { template: '<div class="mock-mc-single">MC Single<input type="radio" @change="$emit(\'update:answer\', { answer_option_id: 1 })"></div>', props: ['question'] };
const MockMcMulti = { template: '<div class="mock-mc-multi">MC Multi<input type="checkbox" @change="$emit(\'update:answer\', { answer_option_ids: [1,2] })"></div>', props: ['question'] };
const MockTrueFalse = { template: '<div class="mock-tf">TF<input type="radio" @change="$emit(\'update:answer\', { is_true: true })"></div>', props: ['question'] };
const MockFillBlank = { template: '<div class="mock-fb">FB<input type="text" @input="$emit(\'update:answer\', { answers: { \'1\': $event.target.value } })"></div>', props: ['question'] };
const MockOpenAnswer = { template: '<div class="mock-oa">OA<textarea @input="$emit(\'update:answer\', { text: $event.target.value })"></textarea></div>', props: ['question'] };


// Mock del router
const routes = [
  { path: '/', name: 'home', component: { template: '<div>Home</div>' } },
  { path: '/quiz/:quizId/start', name: 'quiz-start-attempt', component: QuizAttemptView, props: true },
  { path: '/quiz/result/:attemptId', name: 'QuizResult', component: { template: '<div>Results</div>' }, props: true }, // Pagina risultati mock
];
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Mock del servizio QuizService
vi.mock('@/api/quiz', () => ({
  default: {
    startAttempt: vi.fn(),
    getCurrentQuestion: vi.fn(),
    submitAnswer: vi.fn(),
    completeAttempt: vi.fn(),
    // Mock altre funzioni se necessario
  }
}));

// Mock dati
const mockQuizAttempt: QuizAttempt = {
    id: 100,
    quiz: { id: 1, title: 'Test Quiz', description: 'Descrizione', metadata: {} },
    started_at: new Date().toISOString(),
    completed_at: null,
    score: null,
    points_earned: null,
    status: 'in_progress',
};

const mockQuestion1: Question = {
    id: 10, text: 'Domanda 1 (MC Single)', question_type: 'MC_SINGLE', order: 1, metadata: {}, answer_options: [{id: 1, text: 'A', order: 1}] // Corretto
};
const mockQuestion2: Question = {
    id: 11, text: 'Domanda 2 (True/False)', question_type: 'TF', order: 2, metadata: {} // Corretto
};
const mockCompletedAttempt: AttemptDetails = {
    ...mockQuizAttempt,
    id: 100, // Assicurati che l'ID sia lo stesso
    status: 'completed',
    completed_at: new Date().toISOString(),
    score: 0.8,
    points_earned: 10,
    questions: [mockQuestion1, mockQuestion2], // Aggiungi domande se necessario per la vista risultati
    given_answers: [], // Corretto: usa 'given_answers'
};


describe('QuizAttemptView.vue', () => {
  beforeEach(async () => {
    setActivePinia(createPinia());
    // Naviga alla rotta corretta prima di ogni test
    router.push('/quiz/1/start'); 
    await router.isReady(); // Attende che la navigazione sia completa
    vi.clearAllMocks();

    // Mock di base per le chiamate API iniziali
    vi.mocked(QuizService.startAttempt).mockResolvedValue(mockQuizAttempt);
    vi.mocked(QuizService.getCurrentQuestion).mockResolvedValue(mockQuestion1); // Inizia con la domanda 1
  });

  it('calls startAttempt and getCurrentQuestion on mount', async () => {
    mount(QuizAttemptView, {
      global: { plugins: [router], stubs: { /* Stubs per componenti domanda */ } }
    });
    await flushPromises(); // Attende risoluzione chiamate API

    expect(QuizService.startAttempt).toHaveBeenCalledTimes(1);
    expect(QuizService.startAttempt).toHaveBeenCalledWith(1); // quizId dalla rotta
    expect(QuizService.getCurrentQuestion).toHaveBeenCalledTimes(1);
    expect(QuizService.getCurrentQuestion).toHaveBeenCalledWith(mockQuizAttempt.id);
  });

  it('renders the current question component', async () => {
     const wrapper = mount(QuizAttemptView, {
      global: { 
          plugins: [router], 
          stubs: { // Usa i mock definiti sopra
              MultipleChoiceSingleQuestion: MockMcSingle,
              MultipleChoiceMultipleQuestion: MockMcMulti,
              TrueFalseQuestion: MockTrueFalse,
              FillBlankQuestion: MockFillBlank,
              OpenAnswerManualQuestion: MockOpenAnswer,
          } 
      }
    });
    await flushPromises();

    // Dovrebbe renderizzare il mock per MC Single
    expect(wrapper.find('.mock-mc-single').exists()).toBe(true);
    expect(wrapper.find('h3').text()).toContain('Domanda 1');
    expect(wrapper.find('.question-text').text()).toBe(mockQuestion1.text);
  });

  it('calls submitAnswer and fetches next question on submit', async () => {
    // Mock per la seconda domanda e per submitAnswer
    vi.mocked(QuizService.getCurrentQuestion).mockResolvedValueOnce(mockQuestion1).mockResolvedValueOnce(mockQuestion2);
    vi.mocked(QuizService.submitAnswer).mockResolvedValue({ is_correct: true }); // Risposta mock da submit

     const wrapper = mount(QuizAttemptView, {
      global: { plugins: [router], stubs: { MultipleChoiceSingleQuestion: MockMcSingle } }
    });
    await flushPromises(); // Caricamento iniziale

    // Simula l'aggiornamento della risposta dal componente figlio
    // Trova il mock e simula l'emissione dell'evento (o triggera un input/change)
    const mcSingleComponent = wrapper.findComponent(MockMcSingle);
    await mcSingleComponent.find('input').trigger('change'); // Simula selezione
    
    // Attende che il v-model/watcher aggiorni userAnswer
    await wrapper.vm.$nextTick(); 

    // Clicca sul pulsante Invia
    const submitButton = wrapper.find('button:not(:disabled)'); // Trova il pulsante abilitato
    expect(submitButton.text()).toContain('Invia Risposta');
    await submitButton.trigger('click');

    // Verifica chiamata a submitAnswer
    expect(QuizService.submitAnswer).toHaveBeenCalledTimes(1);
    expect(QuizService.submitAnswer).toHaveBeenCalledWith(mockQuizAttempt.id, mockQuestion1.id, { answer_option_id: 1 }); // Verifica payload

    // Attende risoluzione submitAnswer e fetch successiva domanda
    await flushPromises(); 

    // Verifica che getCurrentQuestion sia stato chiamato di nuovo
    expect(QuizService.getCurrentQuestion).toHaveBeenCalledTimes(2); // Chiamata iniziale + dopo submit
     expect(QuizService.getCurrentQuestion).toHaveBeenLastCalledWith(mockQuizAttempt.id);

    // Verifica che la seconda domanda sia visualizzata (o il suo mock)
    expect(wrapper.find('h3').text()).toContain('Domanda 2');
    expect(wrapper.find('.question-text').text()).toBe(mockQuestion2.text);
  });

  it('shows completion button when getCurrentQuestion returns 404', async () => {
     // Mock: prima domanda ok, seconda chiamata a getCurrentQuestion fallisce con 404
    vi.mocked(QuizService.getCurrentQuestion)
        .mockResolvedValueOnce(mockQuestion1) // Prima domanda
        .mockRejectedValue({ response: { status: 404 } }); // Fine domande
    vi.mocked(QuizService.submitAnswer).mockResolvedValue({ is_correct: true });

     const wrapper = mount(QuizAttemptView, {
      global: { plugins: [router], stubs: { MultipleChoiceSingleQuestion: MockMcSingle } }
    });
    await flushPromises(); // Caricamento iniziale

    // Simula risposta e invio
    const mcSingleComponent = wrapper.findComponent(MockMcSingle);
    await mcSingleComponent.find('input').trigger('change');
    await wrapper.vm.$nextTick(); 
    await wrapper.find('button:not(:disabled)').trigger('click');
    await flushPromises(); // Attende submit e fetch fallito

    // Verifica che il container della domanda non sia visibile
    expect(wrapper.find('.question-container').exists()).toBe(false);
    // Verifica che il messaggio/pulsante di completamento sia visibile
    expect(wrapper.text()).toContain('Hai risposto a tutte le domande!');
    expect(wrapper.find('button').text()).toContain('Completa Quiz e Vedi Risultati');
  });

  it('calls completeAttempt and navigates on complete button click', async () => {
    // Simula lo scenario di fine domande
    vi.mocked(QuizService.getCurrentQuestion)
        .mockResolvedValueOnce(mockQuestion1)
        .mockRejectedValue({ response: { status: 404 } });
    vi.mocked(QuizService.submitAnswer).mockResolvedValue({ is_correct: true });
    // Mock per completeAttempt
    vi.mocked(QuizService.completeAttempt).mockResolvedValue(mockCompletedAttempt);
    const routerPushSpy = vi.spyOn(router, 'push');

     const wrapper = mount(QuizAttemptView, {
      global: { plugins: [router], stubs: { MultipleChoiceSingleQuestion: MockMcSingle } }
    });
    await flushPromises(); // Caricamento iniziale
    // Simula risposta e invio
    const mcSingleComponent = wrapper.findComponent(MockMcSingle);
    await mcSingleComponent.find('input').trigger('change');
    await wrapper.vm.$nextTick(); 
    await wrapper.find('button:not(:disabled)').trigger('click');
    await flushPromises(); // Attende submit e fetch fallito

    // Clicca sul pulsante Completa
    const completeButton = wrapper.find('button');
    expect(completeButton.text()).toContain('Completa Quiz');
    await completeButton.trigger('click');

    // Verifica chiamata a completeAttempt
    expect(QuizService.completeAttempt).toHaveBeenCalledTimes(1);
    expect(QuizService.completeAttempt).toHaveBeenCalledWith(mockQuizAttempt.id);

    // Attende risoluzione completeAttempt e navigazione
    await flushPromises();

    // Verifica navigazione alla pagina dei risultati
    expect(routerPushSpy).toHaveBeenCalledTimes(1);
    expect(routerPushSpy).toHaveBeenCalledWith({ name: 'QuizResult', params: { attemptId: mockQuizAttempt.id } });
  });

   it('displays error message if startAttempt fails', async () => {
    const errorMessage = 'Errore API Start';
    vi.mocked(QuizService.startAttempt).mockRejectedValue({ response: { data: { detail: errorMessage } } });
    // Non serve mockare getCurrentQuestion perché fallisce prima

    const wrapper = mount(QuizAttemptView, {
      global: { plugins: [router] }
    });
    await flushPromises();

    expect(wrapper.find('.error-message').exists()).toBe(true);
    expect(wrapper.find('.error-message').text()).toContain(`Errore avvio: ${errorMessage}`);
  });

   it('displays error message if submitAnswer fails', async () => {
    const errorMessage = 'Risposta non valida';
     vi.mocked(QuizService.submitAnswer).mockRejectedValue({ response: { data: { detail: errorMessage } } });

     const wrapper = mount(QuizAttemptView, {
      global: { plugins: [router], stubs: { MultipleChoiceSingleQuestion: MockMcSingle } }
    });
    await flushPromises(); // Caricamento iniziale

    // Simula risposta e invio
    const mcSingleComponent = wrapper.findComponent(MockMcSingle);
    await mcSingleComponent.find('input').trigger('change');
    await wrapper.vm.$nextTick(); 
    await wrapper.find('button:not(:disabled)').trigger('click');
    await flushPromises(); // Attende submit fallito

    expect(wrapper.find('.error-message').exists()).toBe(true);
    expect(wrapper.find('.error-message').text()).toContain(`Errore invio risposta: ${errorMessage}`);
    // Verifica che la domanda corrente sia ancora visualizzata
    expect(wrapper.find('.question-container').exists()).toBe(true); 
  });

});