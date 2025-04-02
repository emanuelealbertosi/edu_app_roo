import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import OpenAnswerManualQuestion from '../questions/OpenAnswerManualQuestion.vue'; // Adatta il percorso
import type { Question, OpenAnswerManualAnswer } from '@/api/quiz';

// Mock della domanda
const mockQuestion: Question = {
  id: 5,
  text: 'Descrivi il ciclo dell\'acqua.',
  question_type: 'open_answer_manual',
  order: 5,
  metadata: {},
  // answer_options non è usato
};

describe('OpenAnswerManualQuestion.vue', () => {
  it('renders a textarea correctly', () => {
    const wrapper = mount(OpenAnswerManualQuestion, {
      props: { question: mockQuestion }
    });

    const textarea = wrapper.find('textarea.answer-textarea');
    expect(textarea.exists()).toBe(true);
    expect(textarea.attributes('placeholder')).toBe('Scrivi qui la tua risposta...');
    expect(textarea.attributes('aria-label')).toContain(mockQuestion.text);
  });

  it('emits "update:answer" with { text: value } when text is entered', async () => {
    const wrapper = mount(OpenAnswerManualQuestion, {
      props: { question: mockQuestion }
    });

    const textarea = wrapper.find('textarea.answer-textarea');
    const testAnswer = 'L\'acqua evapora, forma nuvole, piove.';
    
    await textarea.setValue(testAnswer);

    expect(wrapper.emitted()).toHaveProperty('update:answer');
    const lastEmit = wrapper.emitted('update:answer')?.slice(-1)[0];
    const expectedPayload: OpenAnswerManualAnswer = { text: testAnswer };
    expect(lastEmit?.[0]).toEqual(expectedPayload);
  });

  it('emits "update:answer" with null when text is cleared or only whitespace', async () => {
    const wrapper = mount(OpenAnswerManualQuestion, {
      props: { question: mockQuestion }
    });

    const textarea = wrapper.find('textarea.answer-textarea');
    
    // Inserisci testo e verifica emissione
    await textarea.setValue('Testo iniziale');
    expect(wrapper.emitted('update:answer')?.slice(-1)[0]).toEqual([{ text: 'Testo iniziale' }]);

    // Svuota il textarea
    await textarea.setValue('');
    expect(wrapper.emitted('update:answer')?.slice(-1)[0]).toEqual([null]);

    // Inserisci solo spazi
    await textarea.setValue('   ');
     expect(wrapper.emitted('update:answer')?.slice(-1)[0]).toEqual([null]);
  });


  it('initializes with the provided initialAnswer', () => {
    const initialText = 'Risposta iniziale fornita.';
    const initialAnswer: OpenAnswerManualAnswer = { text: initialText }; 
    const wrapper = mount(OpenAnswerManualQuestion, {
      props: { 
        question: mockQuestion,
        initialAnswer: initialAnswer 
      }
    });

    const textarea = wrapper.find('textarea.answer-textarea');
    expect((textarea.element as HTMLTextAreaElement).value).toBe(initialText);
  });

   it('resets text when the question prop changes', async () => {
    const wrapper = mount(OpenAnswerManualQuestion, {
      props: { question: mockQuestion }
    });

    const textarea = wrapper.find('textarea.answer-textarea');
    
    // Inserisci testo
    await textarea.setValue('Risposta alla prima domanda');
    expect((textarea.element as HTMLTextAreaElement).value).toBe('Risposta alla prima domanda');
    expect(wrapper.emitted('update:answer')?.slice(-1)[0]).toEqual([{ text: 'Risposta alla prima domanda' }]);


    // Cambia la domanda
    const newMockQuestion: Question = { ...mockQuestion, id: 6, text: 'Nuova domanda aperta?' };
    await wrapper.setProps({ question: newMockQuestion });

    // Verifica che il textarea sia stato svuotato
    expect((textarea.element as HTMLTextAreaElement).value).toBe(''); 

    // Verifica che sia stato emesso un evento null (perché il testo è vuoto dopo il reset)
    // Nota: l'emissione avviene nel watcher del testo, che viene triggerato dal reset.
    expect(wrapper.emitted('update:answer')?.slice(-1)[0]).toEqual([null]); 
  });

});