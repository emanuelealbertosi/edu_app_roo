import { test, expect } from '@playwright/test';

// URL base dell'applicazione frontend (potrebbe essere necessario configurarlo in playwright.config.ts)
const BASE_URL = 'http://localhost:5173'; // Assumendo che Vite giri sulla porta 5173

test.describe('Authentication Flow', () => {

  test.beforeEach(async ({ page }) => {
    // Vai alla pagina di login prima di ogni test
    await page.goto(`${BASE_URL}/login`);
  });

  test('should display login form', async ({ page }) => {
    // Verifica che gli elementi chiave del form siano visibili
    await expect(page.locator('h1:has-text("Login Studente")')).toBeVisible();
    await expect(page.locator('input[type="text"][placeholder="Codice Studente"]')).toBeVisible();
    await expect(page.locator('input[type="password"][placeholder="PIN"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]:has-text("Login")')).toBeVisible();
  });

  test('should show error message with invalid credentials', async ({ page }) => {
    // Inserisci credenziali errate
    await page.locator('input[type="text"]').fill('utenteerrato');
    await page.locator('input[type="password"]').fill('pinerrato');
    
    // Clicca sul pulsante Login
    await page.locator('button[type="submit"]').click();

    // Verifica che un messaggio di errore sia mostrato
    // L'identificatore del messaggio di errore dipende dall'implementazione nel componente LoginForm/LoginView
    const errorMessage = page.locator('.error-message'); // Assumendo una classe .error-message
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('Errore di autenticazione'); // O un messaggio più specifico

    // Verifica di essere ancora sulla pagina di login
    await expect(page).toHaveURL(`${BASE_URL}/login`);
  });

  test('should redirect to dashboard with valid credentials', async ({ page }) => {
    // **ATTENZIONE:** Questo test richiede che esista uno studente con queste credenziali
    // nel backend (o che il backend sia mockato per accettarle).
    const validStudentCode = 'emanuele'; // Usa credenziali valide note
    const validPin = '1234';          // Usa credenziali valide note

    // Inserisci credenziali valide
    await page.locator('input[type="text"]').fill(validStudentCode);
    await page.locator('input[type="password"]').fill(validPin);

    // Clicca sul pulsante Login
    await page.locator('button[type="submit"]').click();

    // Attendi la navigazione alla dashboard
    await page.waitForURL(`${BASE_URL}/dashboard`);

    // Verifica di essere sulla dashboard (controllando un elemento specifico della dashboard)
    await expect(page.locator('h1:has-text("Dashboard Studente")')).toBeVisible();
    await expect(page.locator('nav a:has-text("Dashboard")')).toHaveClass(/router-link-exact-active/); // Verifica link attivo navbar
  });

  test('should redirect logged-in user from login to dashboard', async ({ page }) => {
     // Prima effettua il login per impostare lo stato
     await page.goto(`${BASE_URL}/login`);
     await page.locator('input[type="text"]').fill('emanuele'); // Credenziali valide
     await page.locator('input[type="password"]').fill('1234');
     await page.locator('button[type="submit"]').click();
     await page.waitForURL(`${BASE_URL}/dashboard`); // Attendi login completato

     // Ora prova ad andare di nuovo alla pagina di login
     await page.goto(`${BASE_URL}/login`);

     // Attendi e verifica di essere reindirizzato alla dashboard
     await page.waitForURL(`${BASE_URL}/dashboard`);
     await expect(page.locator('h1:has-text("Dashboard Studente")')).toBeVisible();
  });

  test('should log out and redirect to login', async ({ page }) => {
     // Effettua il login
     await page.goto(`${BASE_URL}/login`);
     await page.locator('input[type="text"]').fill('emanuele'); // Credenziali valide
     await page.locator('input[type="password"]').fill('1234');
     await page.locator('button[type="submit"]').click();
     await page.waitForURL(`${BASE_URL}/dashboard`);

     // Clicca sul pulsante Logout nella navbar
     await page.locator('button.logout-button-nav').click();

     // Attendi la navigazione alla pagina di login
     await page.waitForURL(`${BASE_URL}/login`);

     // Verifica di essere sulla pagina di login
     await expect(page.locator('h1:has-text("Login Studente")')).toBeVisible();

     // Verifica che il token sia stato rimosso (controllando localStorage o provando ad accedere a una rotta protetta)
     // Esempio: prova ad andare alla dashboard, dovresti essere reindirizzato al login
     await page.goto(`${BASE_URL}/dashboard`);
     await page.waitForURL(`${BASE_URL}/login`); // Attende il reindirizzamento
     await expect(page.locator('h1:has-text("Login Studente")')).toBeVisible();
  });

});