import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import LoginForm from '../LoginForm.vue'; // Assicurati che il percorso sia corretto

describe('LoginForm.vue', () => {
  it('renders the form elements correctly', () => {
    const wrapper = mount(LoginForm);

    // Verifica la presenza dei campi input
    expect(wrapper.find('input[type="text"]').exists()).toBe(true);
    expect(wrapper.find('input[type="password"]').exists()).toBe(true);

    // Verifica la presenza del pulsante di submit
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').text()).toContain('Login');
  });

  it('updates input values on user input', async () => {
    const wrapper = mount(LoginForm);
    const studentCodeInput = wrapper.find('input[type="text"]');
    const pinInput = wrapper.find('input[type="password"]');

    await studentCodeInput.setValue('testuser');
    await pinInput.setValue('1234');

    // Verifica che i valori interni (v-model) siano aggiornati
    // Nota: Vue Test Utils non espone direttamente lo stato interno facilmente come prima.
    // Si testa l'effetto (es. emissione evento) o si verifica il valore DOM.
    expect((studentCodeInput.element as HTMLInputElement).value).toBe('testuser');
    expect((pinInput.element as HTMLInputElement).value).toBe('1234');
  });

  it('emits "submit" event with credentials when form is submitted', async () => {
    const wrapper = mount(LoginForm);
    const studentCodeInput = wrapper.find('input[type="text"]');
    const pinInput = wrapper.find('input[type="password"]');
    const form = wrapper.find('form');

    const testCredentials = {
      student_code: 'testuser',
      pin: '1234'
    };

    await studentCodeInput.setValue(testCredentials.student_code);
    await pinInput.setValue(testCredentials.pin);

    await form.trigger('submit.prevent');

    // Verifica che l'evento 'submit' sia stato emesso
    expect(wrapper.emitted()).toHaveProperty('submit');
    
    // Verifica che l'evento sia stato emesso una volta
    expect(wrapper.emitted('submit')).toHaveLength(1);

    // Verifica che l'evento sia stato emesso con le credenziali corrette
    expect(wrapper.emitted('submit')?.[0]).toEqual([testCredentials]);
  });

  it('disables submit button when submitting', async () => {
    // Monta il componente passando la prop 'isSubmitting' a true
    const wrapper = mount(LoginForm, {
      props: {
        isSubmitting: true
      }
    });

    const submitButton = wrapper.find('button[type="submit"]');
    expect(submitButton.attributes('disabled')).toBeDefined();
    expect(submitButton.text()).toContain('Login in corso...'); 
  });

   it('does not emit "submit" if fields are empty (basic validation check)', async () => {
    const wrapper = mount(LoginForm);
    const form = wrapper.find('form');

    await form.trigger('submit.prevent');

    // Non dovrebbe emettere 'submit' se i campi sono vuoti (assumendo validazione HTML5 o interna)
    // O se il pulsante è disabilitato
    // Questo test è basilare, una validazione più complessa richiederebbe più setup
    expect(wrapper.emitted('submit')).toBeUndefined();
  });

});