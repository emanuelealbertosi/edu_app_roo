import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import MultipleChoiceSingleQuestion from '../questions/MultipleChoiceSingleQuestion.vue'; // Adatta il percorso
import type { Question, MultipleChoiceSingleAnswer } from '@/api/quiz';

// Mock della domanda
const mockQuestion: Question = {
  id: 1,
  text: 'Qual è la capitale dell\'Italia?',
  question_type: 'multiple_choice_single',
  order: 1,
  metadata: {},
  answer_options: [
    { id: 10, text: 'Parigi', order: 1 },
    { id: 11, text: 'Roma', order: 2 },
    { id: 12, text: 'Berlino', order: 3 },
  ],
};

describe('MultipleChoiceSingleQuestion.vue', () => {
  it('renders all answer options correctly', () => {
    const wrapper = mount(MultipleChoiceSingleQuestion, {
      props: { question: mockQuestion }
    });

    const options = wrapper.findAll('.option-item');
    expect(options.length).toBe(mockQuestion.answer_options?.length);

    // Verifica il testo di ogni opzione
    options.forEach((optionWrapper, index) => {
      expect(optionWrapper.find('.option-text').text()).toBe(mockQuestion.answer_options?.[index]?.text);
      // Verifica che l'input radio abbia il valore corretto
      expect(optionWrapper.find('input[type="radio"]').attributes('value')).toBe(mockQuestion.answer_options?.[index]?.id.toString());
    });
  });

  it('emits "update:answer" with the correct option ID when an option is selected', async () => {
    const wrapper = mount(MultipleChoiceSingleQuestion, {
      props: { question: mockQuestion }
    });

    const radioInputs = wrapper.findAll('input[type="radio"]');
    
    // Simula la selezione della seconda opzione (Roma, id: 11)
    await radioInputs[1].setValue(true); // Imposta il radio button come selezionato

    // Verifica che l'evento sia stato emesso
    expect(wrapper.emitted()).toHaveProperty('update:answer');
    expect(wrapper.emitted('update:answer')).toHaveLength(1);

    // Verifica che l'evento contenga l'oggetto corretto
    const expectedPayload: MultipleChoiceSingleAnswer = { answer_option_id: 11 };
    expect(wrapper.emitted('update:answer')?.[0]).toEqual([expectedPayload]);

     // Simula la selezione della terza opzione (Berlino, id: 12)
    await radioInputs[2].setValue(true);
    expect(wrapper.emitted('update:answer')).toHaveLength(2); // Ora 2 eventi emessi
    const expectedPayload2: MultipleChoiceSingleAnswer = { answer_option_id: 12 };
    expect(wrapper.emitted('update:answer')?.[1]).toEqual([expectedPayload2]);
  });

  it('initializes with the provided initialAnswer', () => {
    const initialAnswer: MultipleChoiceSingleAnswer = { answer_option_id: 12 }; // Berlino
    const wrapper = mount(MultipleChoiceSingleQuestion, {
      props: { 
        question: mockQuestion,
        initialAnswer: initialAnswer 
      }
    });

    const radioInputs = wrapper.findAll('input[type="radio"]');
    // Verifica che il radio button corrispondente all'initialAnswer sia selezionato
    expect((radioInputs[2].element as HTMLInputElement).checked).toBe(true);
    // Verifica che gli altri non siano selezionati
    expect((radioInputs[0].element as HTMLInputElement).checked).toBe(false);
    expect((radioInputs[1].element as HTMLInputElement).checked).toBe(false);
  });

   it('resets selection when the question prop changes', async () => {
    const wrapper = mount(MultipleChoiceSingleQuestion, {
      props: { question: mockQuestion }
    });

    const radioInputs = wrapper.findAll('input[type="radio"]');
    
    // Seleziona un'opzione
    await radioInputs[1].setValue(true);
    expect((radioInputs[1].element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.emitted('update:answer')).toHaveLength(1);

    // Cambia la domanda (simulato cambiando l'ID)
    const newMockQuestion: Question = { ...mockQuestion, id: 2, text: 'Nuova domanda?' };
    await wrapper.setProps({ question: newMockQuestion });

    // Verifica che la selezione sia stata resettata
    expect((radioInputs[1].element as HTMLInputElement).checked).toBe(false); 
    // Verifica che sia stato emesso un evento null per resettare la risposta nel parent
    expect(wrapper.emitted('update:answer')).toHaveLength(2);
    expect(wrapper.emitted('update:answer')?.[1]).toEqual([null]); 
  });

});