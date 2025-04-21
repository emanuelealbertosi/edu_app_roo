<template>
  <div class="students-view p-4 md:p-6"> <!-- Added padding -->
    <h1 class="text-2xl font-semibold mb-4">Gestione Studenti</h1> <!-- Styled heading -->
    <p class="text-gray-600 mb-6">Elenco degli studenti associati al tuo account.</p> <!-- Styled paragraph -->

    <div v-if="isLoading" class="text-center py-10 text-gray-500">Caricamento studenti...</div> <!-- Styled loading -->
    <div v-else-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6" role="alert"> <!-- Styled error -->
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento degli studenti: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="students.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-gray-200 bg-white">
        <thead class="bg-gray-50">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nome</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cognome</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Codice Studente</th> <!-- Ripristinato -->
            <!-- <th>Username</th> --> <!-- Rimosso come da richiesta -->
            <!-- Aggiungere altre colonne se necessario -->
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="student in students" :key="student.id" class="hover:bg-gray-50 transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ student.first_name }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ student.last_name }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ student.student_code }}</td> <!-- Ripristinato -->
            <!-- <td>{{ student.username }}</td> --> <!-- Rimosso come da richiesta -->
            <!-- Aggiungere altre celle se necessario -->
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-gray-500"> <!-- Styled no students -->
      Nessuno studente trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { fetchStudents, type Student } from '@/api/students'; // Importa la funzione API e il tipo

const students = ref<Student[]>([]); // Conterrà l'elenco degli studenti
const isLoading = ref(false); // Stato di caricamento
const error = ref<string | null>(null); // Messaggio di errore

onMounted(async () => {
  isLoading.value = true;
  error.value = null;
  try {
    students.value = await fetchStudents();
    // console.log('Studenti ricevuti:', students.value); // Rimosso log di debug
  } catch (err: any) {
    console.error("Errore nel recupero degli studenti:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
    // Potresti voler gestire tipi specifici di errore qui (es. 401, 403)
  } finally {
    isLoading.value = false;
  }
});
</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
/* Puoi aggiungere qui stili molto specifici se necessario */
</style>