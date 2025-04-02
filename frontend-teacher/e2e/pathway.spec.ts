import { test, expect } from '@playwright/test';
import fs from 'fs'; // Importa fs per leggere il token
import path from 'path'; // Importa path

// Percorso al file del token salvato dal setup
const tokenFile = 'playwright/.auth/teacher_token.txt';

test.describe('Gestione Percorsi Educativi', () => {
  // test.describe.configure({ mode: 'serial' }); // Eseguire in serie se necessario

  // Hook eseguito prima di ogni test
  test.beforeEach(async ({ page }) => {
    // Leggi il token dal file
    if (!fs.existsSync(tokenFile)) {
      throw new Error(`Token file not found at ${tokenFile}. Run setup first.`);
    }
    const accessToken = fs.readFileSync(tokenFile, 'utf-8');

    // Vai a una pagina iniziale (es. login) PRIMA di iniettare il token
    await page.goto('/login');

    // Inietta il token nel localStorage
    await page.evaluate(token => {
      localStorage.setItem('teacher_access_token', token);
    }, accessToken);

    // Ora naviga alla pagina principale.
    await page.goto('/');

    // Attendi che la navigazione sia visibile
    await expect(page.getByRole('link', { name: 'Dashboard' })).toBeVisible({ timeout: 15000 });
  });

  test('dovrebbe permettere la creazione di un nuovo percorso', async ({ page }) => {
    const newPathwayTitle = `Percorso Test E2E - ${Date.now()}`;
    const newPathwayDescription = 'Descrizione percorso creata dal test E2E.';

    // 1. Navigare alla pagina Percorsi
    await page.getByRole('link', { name: 'Percorsi' }).click();
    await expect(page).toHaveURL('/pathways');
    // Usa il testo esatto dall'h1 della vista
    await expect(page.locator('h1:has-text("Gestione Percorsi Educativi")')).toBeVisible();

    // 2. Cliccare sul pulsante "Crea Nuovo Percorso"
    //    Assumendo un pulsante con questo testo
    await page.getByRole('button', { name: 'Crea Nuovo Percorso' }).click();

    // 3. Verificare la navigazione al form di creazione
    await expect(page).toHaveURL('/pathways/new');
    // Usa il testo esatto dall'h1 del form
    await expect(page.locator('h1:has-text("Crea Nuovo Percorso")')).toBeVisible();

    // 4. Compilare il form (verificare ID/selettori in PathwayFormView.vue)
    await page.locator('#title').fill(newPathwayTitle); // Assumendo #title
    await page.locator('#description').fill(newPathwayDescription); // Assumendo #description

    // 5. Salvare il percorso
    //    Assumendo un pulsante di salvataggio generico
    await page.locator('button[type="submit"]').click();

    // 6. Verificare il reindirizzamento alla lista percorsi
    await expect(page).toHaveURL('/pathways', { timeout: 10000 });

    // 7. Verificare che il nuovo percorso sia presente nella lista
    //    Assumendo che il titolo sia visibile in una cella <td> della tabella
    await expect(page.locator(`td:has-text("${newPathwayTitle}")`)).toBeVisible();
  });

  // Aggiungere qui test per modifica ed eliminazione percorsi

  test('dovrebbe permettere la modifica di un percorso esistente', async ({ page }) => {
    const pathwayToModifyTitle = `Percorso Da Modificare E2E - ${Date.now()}`;
    const modificationSuffix = ' - Modificato E2E';

    // 1. Creare un percorso da modificare
    await page.getByRole('link', { name: 'Percorsi' }).click();
    await page.getByRole('button', { name: 'Crea Nuovo Percorso' }).click();
    await expect(page).toHaveURL('/pathways/new');
    await page.locator('#title').fill(pathwayToModifyTitle);
    await page.locator('#description').fill('Descrizione iniziale.');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/pathways', { timeout: 10000 }); // Attendi ritorno alla lista

    // 2. Trovare la riga del percorso appena creato e cliccare "Modifica"
    const pathwayRow = page.locator(`tr:has-text("${pathwayToModifyTitle}")`);
    await expect(pathwayRow).toBeVisible({ timeout: 10000 });
    const editButton = pathwayRow.locator('button:has-text("Modifica")');
    await expect(editButton).toBeVisible();
    await editButton.click();

    // 3. Verificare la navigazione alla pagina di modifica
    await expect(page).toHaveURL(/\/pathways\/\d+\/edit/, { timeout: 10000 });
    await expect(page.locator('h1:has-text("Modifica Percorso")')).toBeVisible();

    // 4. Leggere il titolo attuale e modificarlo
    const titleInput = page.locator('#title');
    await expect(titleInput).toBeVisible({ timeout: 10000 }); // Aumentato timeout a 10s
    // Il titolo dovrebbe essere quello appena creato
    expect(await titleInput.inputValue()).toBe(pathwayToModifyTitle);
    const modifiedTitle = pathwayToModifyTitle + modificationSuffix;
    await titleInput.fill(modifiedTitle);

    // 5. Salvare le modifiche
    await page.locator('button[type="submit"]').click();

    // 6. Verificare il reindirizzamento alla lista percorsi
    await expect(page).toHaveURL('/pathways', { timeout: 10000 });

    // 7. Verificare che il percorso con il titolo modificato sia presente nella lista
    await expect(page.locator(`td:has-text("${modifiedTitle}")`)).toBeVisible({ timeout: 10000 });
  });

  test('dovrebbe permettere l\'eliminazione di un percorso', async ({ page }) => {
    const pathwayToDeleteTitle = `Percorso Da Eliminare E2E - ${Date.now()}`;

    // 1. Creare un percorso da eliminare
    await page.getByRole('link', { name: 'Percorsi' }).click();
    await page.getByRole('button', { name: 'Crea Nuovo Percorso' }).click();
    await expect(page).toHaveURL('/pathways/new');
    await page.locator('#title').fill(pathwayToDeleteTitle);
    await page.locator('#description').fill('Da eliminare.');
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL('/pathways', { timeout: 10000 }); // Attendi ritorno alla lista

    // 2. Trovare la riga del percorso appena creato
    const tableBody = page.locator('tbody');
    const pathwayRow = tableBody.locator(`tr:has-text("${pathwayToDeleteTitle}")`);
    await expect(pathwayRow).toBeVisible({ timeout: 10000 });

    // 3. Trovare il pulsante "Elimina" nella riga specifica e cliccarlo
    const deleteButton = pathwayRow.locator('button:has-text("Elimina")');
    await expect(deleteButton).toBeVisible();

    // Gestire esplicitamente la finestra di dialogo 'confirm'
    page.once('dialog', async dialog => {
      console.log(`Dialog message: ${dialog.message()}`);
      await dialog.accept();
    });

    // Attendere la risposta API DELETE dopo aver cliccato
    await Promise.all([
        page.waitForResponse(response =>
            response.url().includes('/api/education/pathways/') && response.request().method() === 'DELETE' && response.status() === 204,
            { timeout: 10000 }
        ),
        deleteButton.click()
    ]);

    // 4. Verificare che la riga del percorso sia scomparsa
    await expect(pathwayRow).not.toBeVisible({ timeout: 10000 });
  });
});