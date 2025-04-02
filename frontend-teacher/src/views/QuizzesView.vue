<template>
  <div class="quizzes-view">
    <h1>Gestione Quiz</h1>
    <p>Qui puoi visualizzare, creare e modificare i tuoi quiz.</p>
    <div class="actions">
      <button @click="createNewQuiz">Crea Nuovo Quiz</button>
    </div>
    <div v-if="isLoading" class="loading">Caricamento quiz...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento dei quiz: {{ error }}
    </div>
    <div v-else-if="quizzes.length > 0" class="quizzes-list">
      <!-- Tabella o lista dei quiz -->
      <ul>
        <!-- Tabella o lista dei quiz -->
        <table>
          <thead>
            <tr>
              <th>Titolo</th>
              <th>Descrizione</th>
              <th>Creato il</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="quiz in quizzes" :key="quiz.id">
              <td>{{ quiz.title }}</td>
              <td>{{ quiz.description || '-' }}</td>
              <td>{{ new Date(quiz.created_at).toLocaleDateString() }}</td>
              <td>
                <button @click="editQuiz(quiz.id)">Modifica</button>
                <button @click="deleteQuiz(quiz.id)">Elimina</button>
              </td>
            </tr>
          </tbody>
        </table>
      </ul>
    </div>
    <div v-else class="no-quizzes">
      Nessun quiz trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router'; // Importa useRouter per la navigazione
import { fetchQuizzes, deleteQuizApi, type Quiz } from '@/api/quizzes'; // Importa anche deleteQuizApi

const quizzes = ref<Quiz[]>([]);
const isLoading = ref(false);
const router = useRouter(); // Istanza del router
const error = ref<string | null>(null);

onMounted(async () => {
  isLoading.value = true;
  error.value = null;
  try {
    quizzes.value = await fetchQuizzes(); // Chiamata API reale
  } catch (err: any) {
    console.error("Errore nel recupero dei quiz:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
  } finally {
    isLoading.value = false;
  }
});

// Placeholder per le funzioni di modifica/eliminazione
const editQuiz = (id: number) => {
  // Naviga alla rotta di modifica passando l'ID
  router.push({ name: 'quiz-edit', params: { id: id.toString() } });
};

const deleteQuiz = async (id: number) => {
  // Chiedi conferma
  if (!confirm(`Sei sicuro di voler eliminare il quiz con ID ${id}? Questa azione non può essere annullata.`)) {
    return;
  }

  // Aggiungere gestione stato di caricamento/errore specifico per l'eliminazione se necessario
  try {
    await deleteQuizApi(id);
    // Rimuovi il quiz dalla lista locale per aggiornare l'UI
    quizzes.value = quizzes.value.filter(quiz => quiz.id !== id);
    // Mostra un messaggio di successo (opzionale)
    console.log(`Quiz ${id} eliminato con successo.`);
    // Potresti usare un sistema di notifiche più robusto qui
  } catch (err: any) {
    console.error(`Errore durante l'eliminazione del quiz ${id}:`, err);
    // Mostra un messaggio di errore all'utente
    error.value = `Errore durante l'eliminazione del quiz: ${err.response?.data?.detail || err.message || 'Errore sconosciuto'}`;
    // Potresti voler resettare l'errore dopo un po'
  }
};

const createNewQuiz = () => {
  router.push({ name: 'quiz-new' }); // Naviga alla rotta di creazione (da definire)
};
</script>

<style scoped>
.quizzes-view {
  padding: 20px;
}

.loading,
.error-message,
.no-quizzes {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}

.error-message {
  color: red;
  font-weight: bold;
}

.quizzes-list {
  margin-top: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}

td button {
  margin-right: 5px;
  padding: 3px 8px;
  cursor: pointer;
}

.actions {
  margin-bottom: 20px;
}

.actions button {
  padding: 8px 15px;
  cursor: pointer;
  background-color: #4CAF50; /* Green */
  color: white;
  border: none;
  border-radius: 4px;
}

.actions button:hover {
  background-color: #45a049;
}
</style>