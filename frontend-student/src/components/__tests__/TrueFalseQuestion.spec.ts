import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import TrueFalseQuestion from '../questions/TrueFalseQuestion.vue'; // Adatta il percorso
import type { Question, TrueFalseAnswer } from '@/api/quiz';

// Mock della domanda
const mockQuestion: Question = {
  id: 3,
  text: 'Il sole gira intorno alla Terra.',
  question_type: 'TF', // Corretto
  order: 3,
  metadata: {},
  // answer_options non è usato per true_false
};

describe('TrueFalseQuestion.vue', () => {
  it('renders "Vero" and "Falso" options correctly', () => {
    const wrapper = mount(TrueFalseQuestion, {
      props: { question: mockQuestion }
    });

    const options = wrapper.findAll('.option-item');
    expect(options.length).toBe(2);

    // Verifica opzione "Vero"
    const trueOption = options[0];
    expect(trueOption.find('.option-text').text()).toBe('Vero');
    const trueInput = trueOption.find('input[type="radio"]');
    expect(trueInput.exists()).toBe(true);
    expect(trueInput.attributes('value')).toBe('true');

    // Verifica opzione "Falso"
    const falseOption = options[1];
    expect(falseOption.find('.option-text').text()).toBe('Falso');
    const falseInput = falseOption.find('input[type="radio"]');
    expect(falseInput.exists()).toBe(true);
    expect(falseInput.attributes('value')).toBe('false');
  });

  it('emits "update:answer" with { is_true: true } when "Vero" is selected', async () => {
    const wrapper = mount(TrueFalseQuestion, {
      props: { question: mockQuestion }
    });

    const radioInputs = wrapper.findAll('input[type="radio"]');
    
    // Simula la selezione di "Vero"
    await radioInputs[0].setValue(true); 

    expect(wrapper.emitted()).toHaveProperty('update:answer');
    expect(wrapper.emitted('update:answer')).toHaveLength(1);
    const expectedPayload: TrueFalseAnswer = { is_true: true };
    expect(wrapper.emitted('update:answer')?.[0]).toEqual([expectedPayload]);
  });

  it('emits "update:answer" with { is_true: false } when "Falso" is selected', async () => {
    const wrapper = mount(TrueFalseQuestion, {
      props: { question: mockQuestion }
    });

    const radioInputs = wrapper.findAll('input[type="radio"]');
    
    // Simula la selezione di "Falso"
    await radioInputs[1].setValue(true); 

    expect(wrapper.emitted()).toHaveProperty('update:answer');
    expect(wrapper.emitted('update:answer')).toHaveLength(1);
    const expectedPayload: TrueFalseAnswer = { is_true: false };
    expect(wrapper.emitted('update:answer')?.[0]).toEqual([expectedPayload]);
  });

  it('initializes with the provided initialAnswer (true)', () => {
    const initialAnswer: TrueFalseAnswer = { is_true: true }; 
    const wrapper = mount(TrueFalseQuestion, {
      props: { 
        question: mockQuestion,
        initialAnswer: initialAnswer 
      }
    });

    const radioInputs = wrapper.findAll('input[type="radio"]');
    expect((radioInputs[0].element as HTMLInputElement).checked).toBe(true); // Vero
    expect((radioInputs[1].element as HTMLInputElement).checked).toBe(false); // Falso
  });

  it('initializes with the provided initialAnswer (false)', () => {
    const initialAnswer: TrueFalseAnswer = { is_true: false }; 
    const wrapper = mount(TrueFalseQuestion, {
      props: { 
        question: mockQuestion,
        initialAnswer: initialAnswer 
      }
    });

    const radioInputs = wrapper.findAll('input[type="radio"]');
    expect((radioInputs[0].element as HTMLInputElement).checked).toBe(false); // Vero
    expect((radioInputs[1].element as HTMLInputElement).checked).toBe(true); // Falso
  });

   it('resets selection when the question prop changes', async () => {
    const wrapper = mount(TrueFalseQuestion, {
      props: { question: mockQuestion }
    });

    const radioInputs = wrapper.findAll('input[type="radio"]');
    
    // Seleziona un'opzione
    await radioInputs[0].setValue(true); // Seleziona Vero
    expect((radioInputs[0].element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.emitted('update:answer')).toHaveLength(1);

    // Cambia la domanda
    const newMockQuestion: Question = { ...mockQuestion, id: 4, text: 'Nuova domanda V/F?' };
    await wrapper.setProps({ question: newMockQuestion });

    // Verifica che la selezione sia stata resettata
    expect((radioInputs[0].element as HTMLInputElement).checked).toBe(false); 
    expect((radioInputs[1].element as HTMLInputElement).checked).toBe(false); 

    // Verifica che sia stato emesso un evento null
    expect(wrapper.emitted('update:answer')).toHaveLength(2);
    expect(wrapper.emitted('update:answer')?.[1]).toEqual([null]); 
  });

});