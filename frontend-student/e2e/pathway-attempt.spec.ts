import { test, expect, type Page } from '@playwright/test';

// Funzione helper per il login (potrebbe essere estratta in un file separato)
async function loginStudent(page: Page, studentCode = 'STUDENT1000') {
  await page.goto('/login');
  await page.locator('input[name="student_code"]').fill(studentCode);
  // Assumiamo che non ci sia PIN per questo studente di test o che sia gestito diversamente
  await page.locator('button[type="submit"]').click();
  // Attendi la navigazione alla dashboard o un elemento specifico della dashboard
  await expect(page).toHaveURL('/dashboard');
  await expect(page.locator('h1:has-text("Dashboard Studente")')).toBeVisible();
}

test.describe('Pathway Attempt Flow', () => {
  
  // Test per verificare l'avvio di un percorso dalla dashboard
  test('should navigate to pathway attempt page when clicking start/continue pathway', async ({ page }) => {
    // --- Preparazione (Login) ---
    await loginStudent(page);

    // --- Intercettazione API (Opzionale ma consigliato per test stabili) ---
    // Intercetta la chiamata API della dashboard per fornire dati di test controllati
    // Questo evita dipendenze da dati reali nel DB che potrebbero cambiare.
    await page.route('**/api/student/dashboard/pathways/', async route => {
      const json = [
        // Simula un percorso "in corso" o "non iniziato"
        {
          id: 32, // Usa un ID consistente se possibile
          teacher: 1,
          teacher_username: 'teacher_test',
          title: 'Percorso di Test E2E',
          description: 'Descrizione percorso test.',
          metadata: { points_on_completion: 100 },
          created_at: new Date().toISOString(),
          quiz_details: [
            { id: 1, quiz_id: 101, quiz_title: 'Quiz 1 del Percorso', order: 0 },
            { id: 2, quiz_id: 102, quiz_title: 'Quiz 2 del Percorso', order: 1 }
          ],
          latest_progress: { // Simula progresso "IN_PROGRESS" o null per "Non iniziato"
            id: 1,
            status: 'IN_PROGRESS',
            last_completed_quiz_order: null, // Nessun quiz completato ancora
            started_at: new Date().toISOString(),
            completed_at: null,
            points_earned: null
          } 
          // Se vuoi testare un percorso non iniziato, metti latest_progress: null
        }
      ];
      await route.fulfill({ json });
    });
    
    // Intercetta la chiamata API per i dettagli del tentativo del percorso
    await page.route('**/api/education/pathways/32/attempt/', async route => {
        const json = {
            id: 32,
            teacher: 1,
            teacher_username: "teacher_test",
            title: "Percorso di Test E2E",
            description: "Descrizione percorso test.",
            metadata: { points_on_completion: 100 },
            created_at: "2025-04-03T17:40:00Z", // Esempio data
            quiz_details: [
                { id: 1, quiz_id: 101, quiz_title: "Quiz 1 del Percorso", order: 0 },
                { id: 2, quiz_id: 102, quiz_title: "Quiz 2 del Percorso", order: 1 }
            ],
            progress: {
                id: 1,
                student_info: { id: 1, first_name: "Studente", last_name: "Test", unique_identifier: "STUDENT1000" },
                pathway: 32,
                pathway_title: "Percorso di Test E2E",
                last_completed_quiz_order: null, // Nessuno completato
                started_at: "2025-04-03T17:45:00Z",
                completed_at: null,
                status: "IN_PROGRESS",
                status_display: "In corso",
                points_earned: null
            },
            next_quiz: { // Il prossimo quiz è il primo
                id: 101,
                title: "Quiz 1 del Percorso",
                description: "Descrizione Quiz 1"
            }
        };
         await route.fulfill({ json });
    });

    // Ricarica la dashboard per applicare l'intercettazione (o naviga se non già lì)
    await page.goto('/dashboard');
    await expect(page.locator('h2:has-text("Percorsi in Corso")')).toBeVisible(); // Assicurati che la sezione sia caricata

    // --- Azione ---
    // Trova il percorso di test e clicca il pulsante "Inizia Percorso" o "Continua Percorso"
    // Usiamo un selettore che prenda entrambi i casi (il testo cambia)
    const pathwayCard = page.locator('.pathway-item:has-text("Percorso di Test E2E")');
    await expect(pathwayCard).toBeVisible();
    // Clicca sul bottone specifico dentro la card
    await pathwayCard.locator('button:has-text("Inizia Percorso"), button:has-text("Continua Percorso")').click();

    // --- Verifica ---
    // Verifica che l'URL sia cambiato alla pagina del tentativo
    await expect(page).toHaveURL('/pathway/32/attempt');

    // Verifica che il titolo del percorso sia visibile
    await expect(page.locator('h1:has-text("Percorso di Test E2E")')).toBeVisible();
    
    // Verifica che la sezione "Prossimo Passo" sia visibile
    await expect(page.locator('h2:has-text("Prossimo Passo:")')).toBeVisible();

    // Verifica che il titolo del prossimo quiz sia corretto
    await expect(page.locator('.quiz-info h3:has-text("Quiz 1 del Percorso")')).toBeVisible();
    
    // Verifica che il pulsante "Inizia Quiz" sia visibile
    await expect(page.locator('button:has-text("Inizia Quiz")')).toBeVisible();

    // Verifica (opzionale) la lista dei quiz nel percorso
     await expect(page.locator('.pathway-quiz-list li:has-text("1. Quiz 1 del Percorso")')).toBeVisible();
     await expect(page.locator('.pathway-quiz-list li:has-text("2. Quiz 2 del Percorso")')).toBeVisible();
     // Verifica lo stato del primo quiz (Prossimo)
     await expect(page.locator('.pathway-quiz-list li:has-text("1. Quiz 1 del Percorso") .text-blue-600:has-text("Prossimo")')).toBeVisible();

  });

  // TODO: Aggiungere altri test per casi diversi (es. percorso completato, errore API)
});