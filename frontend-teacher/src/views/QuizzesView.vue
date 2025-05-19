<template>
  <div class="container mx-auto p-4">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Gestione Quiz</h1>
      <div class="flex space-x-2">
        <BaseButton @click="createNewQuiz" variant="primary" class="flex items-center">
          <PlusCircleIcon class="h-5 w-5 mr-2" />
          Crea Nuovo Quiz
        </BaseButton>
        <BaseButton @click="uploadFromFile" variant="success" class="flex items-center">
          <ArrowUpTrayIcon class="h-5 w-5 mr-2" />
          Carica da File
        </BaseButton>
      </div>
    </div>
    <p class="text-gray-600 mb-6">Qui puoi visualizzare, creare e modificare i tuoi quiz.</p>

    <GlobalLoadingIndicator :is-loading="isLoading" />

    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> {{ error }}</span>
    </div>

    <div v-if="!isLoading && quizzes.length > 0" class="overflow-x-auto bg-white shadow-md rounded-lg">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Titolo</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descrizione</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Creato il</th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="quiz in quizzes" :key="quiz.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ quiz.title }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ quiz.description || '-' }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ new Date(quiz.created_at).toLocaleDateString('it-IT') }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
              <BaseButton @click="editQuiz(quiz.id)" variant="warning" size="sm" class="p-2" title="Modifica Quiz">
                <PencilIcon class="h-5 w-5" />
              </BaseButton>
              <BaseButton @click="deleteQuiz(quiz.id)" variant="danger" size="sm" class="p-2" title="Elimina Quiz">
                <TrashIcon class="h-5 w-5" />
              </BaseButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="!isLoading && quizzes.length === 0 && !error" class="text-center text-gray-500 mt-6 py-10 bg-gray-50 rounded-md">
      Nessun quiz trovato. Creane uno nuovo o carica da file!
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router'; // Importa useRouter per la navigazione
import { fetchQuizzes, deleteQuizApi, type Quiz } from '@/api/quizzes'; // Importa anche deleteQuizApi
import BaseButton from '@/components/common/BaseButton.vue';
import GlobalLoadingIndicator from '@/components/common/GlobalLoadingIndicator.vue';
import { PlusCircleIcon, ArrowUpTrayIcon, PencilIcon, TrashIcon } from '@heroicons/vue/24/outline';

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
  router.push({ name: 'quiz-new' }); // Naviga alla rotta di creazione manuale
};

const uploadFromFile = () => {
  router.push({ name: 'quiz-upload' }); // Naviga alla nuova rotta di upload
};
</script>

<style scoped>
/* Gli stili specifici sono stati rimossi per fare affidamento su Tailwind CSS e BaseButton */
</style>