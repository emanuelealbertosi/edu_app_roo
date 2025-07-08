import { type Router } from 'vue-router';

/**
 * Naviga a una rotta specifica o ricarica la pagina se la rotta è già attiva.
 * @param router L'istanza di Vue Router.
 * @param routeName Il nome della rotta di destinazione.
 */
export function navigateTo(router: Router, routeName: string) {
  // Naviga sempre alla rotta principale della sezione,
  // lasciando che sia il tracker della cronologia a gestire lo stato.
  router.push({ name: routeName });
}