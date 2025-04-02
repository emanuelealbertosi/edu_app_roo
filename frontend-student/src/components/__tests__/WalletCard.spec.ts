import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import WalletCard from '../WalletCard.vue'; // Assicurati che il percorso sia corretto
import type { WalletInfo } from '@/api/dashboard'; // Importa il tipo WalletInfo da api

describe('WalletCard.vue', () => {
  // Usa il tipo corretto WalletInfo e aggiungi recent_transactions vuoto
  const mockWallet: WalletInfo = {
    current_points: 150,
    recent_transactions: []
  };

  it('renders wallet information when wallet data is provided', () => {
    const wrapper = mount(WalletCard, {
      props: {
        wallet: mockWallet,
        loading: false
      }
    });

    // Verifica il titolo
    expect(wrapper.find('h2').text()).toBe('Il Tuo Wallet');

    // Verifica la visualizzazione dei punti
    expect(wrapper.find('.wallet-points strong').text()).toBe(mockWallet.current_points.toString());
    expect(wrapper.find('.wallet-points').text()).toContain('Punti Attuali');

    // Verifica che l'indicatore di caricamento non sia presente
    expect(wrapper.find('.loading-indicator').exists()).toBe(false);
     // Verifica che il messaggio "dati non disponibili" non sia presente
    expect(wrapper.find('.empty-message').exists()).toBe(false);
  });

  it('renders loading indicator when loading is true', () => {
    const wrapper = mount(WalletCard, {
      props: {
        wallet: null, // O mockWallet, non dovrebbe importare in stato di loading
        loading: true
      }
    });

    // Verifica la presenza dell'indicatore di caricamento
    expect(wrapper.find('.loading-indicator').exists()).toBe(true);
    expect(wrapper.find('.loading-indicator').text()).toContain('Caricamento wallet...');

    // Verifica che i punti non siano visualizzati
    expect(wrapper.find('.wallet-points').exists()).toBe(false);
     // Verifica che il messaggio "dati non disponibili" non sia presente
    // Verifica che il messaggio "dati non disponibili" non sia presente (cambiato nome classe nel componente)
    expect(wrapper.find('.empty-message').exists()).toBe(false);
  });

  it('renders "not available" message when wallet is null and not loading', () => {
    const wrapper = mount(WalletCard, {
      props: {
        wallet: null,
        loading: false
      }
    });

     // Verifica la presenza del messaggio "dati non disponibili" (cambiato nome classe nel componente)
    expect(wrapper.find('.empty-message').exists()).toBe(true);
    expect(wrapper.find('.empty-message').text()).toContain('Impossibile caricare le informazioni del portafoglio.');

    // Verifica che l'indicatore di caricamento non sia presente
    expect(wrapper.find('.loading-indicator').exists()).toBe(false);
    // Verifica che i punti non siano visualizzati
    expect(wrapper.find('.wallet-balance').exists()).toBe(false); // Controlla il contenitore del bilancio
  });

   // Rimuoviamo il test con undefined perché la prop non lo accetta
   /* it('renders "not available" message when wallet is undefined and not loading', () => {
    const wrapper = mount(WalletCard, {
      props: {
        wallet: undefined, // Test con undefined
        loading: false
      }
    });

     // Verifica la presenza del messaggio "dati non disponibili"
    expect(wrapper.find('.no-data-message').exists()).toBe(true);
    expect(wrapper.find('.no-data-message').text()).toContain('Dati wallet non disponibili.');

    // Verifica che l'indicatore di caricamento non sia presente
    expect(wrapper.find('.loading-indicator').exists()).toBe(false);
    // Verifica che i punti non siano visualizzati
    expect(wrapper.find('.wallet-points').exists()).toBe(false);
  }); */ // Aggiunto */ per chiudere il commento
});