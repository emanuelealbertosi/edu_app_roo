import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import MultipleChoiceMultipleQuestion from '../questions/MultipleChoiceMultipleQuestion.vue'; // Adatta il percorso
import type { Question, MultipleChoiceMultipleAnswer } from '@/api/quiz';

// Mock della domanda
const mockQuestion: Question = {
  id: 2,
  text: 'Quali sono città italiane?',
  question_type: 'multiple_choice_multiple',
  order: 2,
  metadata: {},
  answer_options: [
    { id: 20, text: 'Roma', order: 1 },
    { id: 21, text: 'Parigi', order: 2 },
    { id: 22, text: 'Milano', order: 3 },
    { id: 23, text: 'Londra', order: 4 },
  ],
};

describe('MultipleChoiceMultipleQuestion.vue', () => {
  it('renders all answer options correctly as checkboxes', () => {
    const wrapper = mount(MultipleChoiceMultipleQuestion, {
      props: { question: mockQuestion }
    });

    const options = wrapper.findAll('.option-item');
    expect(options.length).toBe(mockQuestion.answer_options?.length);

    options.forEach((optionWrapper, index) => {
      expect(optionWrapper.find('.option-text').text()).toBe(mockQuestion.answer_options?.[index]?.text);
      // Verifica che sia un input checkbox
      const input = optionWrapper.find('input[type="checkbox"]');
      expect(input.exists()).toBe(true);
      expect(input.attributes('value')).toBe(mockQuestion.answer_options?.[index]?.id.toString());
    });
     // Verifica l'istruzione aggiuntiva
    expect(wrapper.find('.instruction').text()).toContain('(Seleziona tutte le risposte corrette)');
  });

  it('emits "update:answer" with an array of selected IDs', async () => {
    const wrapper = mount(MultipleChoiceMultipleQuestion, {
      props: { question: mockQuestion }
    });

    const checkboxes = wrapper.findAll('input[type="checkbox"]');
    
    // Simula la selezione della prima e terza opzione (Roma, Milano - id: 20, 22)
    await checkboxes[0].setValue(true); // Seleziona Roma
    await checkboxes[2].setValue(true); // Seleziona Milano

    // Verifica che l'evento sia stato emesso (potrebbe essere emesso ad ogni cambio)
    expect(wrapper.emitted()).toHaveProperty('update:answer');
    
    // L'ultimo evento emesso dovrebbe contenere l'array corretto
    const lastEmit = wrapper.emitted('update:answer')?.slice(-1)[0];
    const expectedPayload: MultipleChoiceMultipleAnswer = { answer_option_ids: [20, 22] };
    // Ordina gli array prima del confronto per evitare problemi di ordine
    expectedPayload.answer_option_ids.sort((a, b) => a - b);
    const emittedPayload = lastEmit?.[0] as MultipleChoiceMultipleAnswer;
    emittedPayload?.answer_option_ids.sort((a, b) => a - b); // Ordina anche l'array emesso
    expect(emittedPayload).toEqual(expectedPayload);

    // Deseleziona la prima opzione (Roma)
    await checkboxes[0].setValue(false);
    const lastEmit2 = wrapper.emitted('update:answer')?.slice(-1)[0];
    const expectedPayload2: MultipleChoiceMultipleAnswer = { answer_option_ids: [22] };
    expect(lastEmit2?.[0]).toEqual(expectedPayload2);

     // Deseleziona anche la terza (Milano) - nessuna selezione
    await checkboxes[2].setValue(false);
    const lastEmit3 = wrapper.emitted('update:answer')?.slice(-1)[0];
    expect(lastEmit3?.[0]).toBeNull(); // Dovrebbe emettere null se nessuna opzione è selezionata
  });

  it('initializes with the provided initialAnswer', () => {
    const initialAnswer: MultipleChoiceMultipleAnswer = { answer_option_ids: [21, 23] }; // Parigi, Londra
    const wrapper = mount(MultipleChoiceMultipleQuestion, {
      props: { 
        question: mockQuestion,
        initialAnswer: initialAnswer 
      }
    });

    const checkboxes = wrapper.findAll('input[type="checkbox"]');
    // Verifica che le checkbox corrispondenti siano selezionate
    expect((checkboxes[1].element as HTMLInputElement).checked).toBe(true); // Parigi
    expect((checkboxes[3].element as HTMLInputElement).checked).toBe(true); // Londra
    // Verifica che le altre non siano selezionate
    expect((checkboxes[0].element as HTMLInputElement).checked).toBe(false); // Roma
    expect((checkboxes[2].element as HTMLInputElement).checked).toBe(false); // Milano
  });

   it('resets selection when the question prop changes', async () => {
    const wrapper = mount(MultipleChoiceMultipleQuestion, {
      props: { question: mockQuestion }
    });

    const checkboxes = wrapper.findAll('input[type="checkbox"]');
    
    // Seleziona opzioni
    await checkboxes[0].setValue(true);
    await checkboxes[2].setValue(true);
    expect((checkboxes[0].element as HTMLInputElement).checked).toBe(true);
    expect((checkboxes[2].element as HTMLInputElement).checked).toBe(true);
    const lastEmitBeforeChange = wrapper.emitted('update:answer')?.slice(-1)[0];
    expect(lastEmitBeforeChange?.[0]).toEqual({ answer_option_ids: [20, 22] });


    // Cambia la domanda
    const newMockQuestion: Question = { 
        ...mockQuestion, 
        id: 3, 
        text: 'Nuova domanda multipla?',
        answer_options: [ // Nuove opzioni
             { id: 30, text: 'A', order: 1 },
             { id: 31, text: 'B', order: 2 },
        ]
    };
    await wrapper.setProps({ question: newMockQuestion });

    // Attende che Vue aggiorni il DOM e i watcher reagiscano
    await wrapper.vm.$nextTick(); 

    // Verifica che le nuove opzioni siano renderizzate
    const newCheckboxes = wrapper.findAll('input[type="checkbox"]');
    expect(newCheckboxes.length).toBe(2);
    expect(newCheckboxes[0].attributes('value')).toBe('30');
    expect(newCheckboxes[1].attributes('value')).toBe('31');

    // Verifica che la selezione sia stata resettata (nessuna checkbox selezionata)
    expect((newCheckboxes[0].element as HTMLInputElement).checked).toBe(false); 
    expect((newCheckboxes[1].element as HTMLInputElement).checked).toBe(false); 

    // Verifica che sia stato emesso un evento null per resettare la risposta nel parent
    const lastEmitAfterChange = wrapper.emitted('update:answer')?.slice(-1)[0];
    expect(lastEmitAfterChange?.[0]).toBeNull(); 
  });

});