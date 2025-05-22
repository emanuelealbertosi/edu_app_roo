<template>
  <!-- Padding ok -->
  <div class="students-view p-4 md:p-6">
    <!-- Stile titolo aggiornato -->
    <div class="bg-primary text-white p-4 rounded-md mb-6"> <!-- Contenitore per titolo e sottotitolo -->
      <h1 class="text-2xl font-semibold mb-1">Gestione Studenti</h1> <!-- Rimosso stile individuale, aggiunto mb-1 -->
      <!-- Stile paragrafo aggiornato -->
      <p class="opacity-90">Elenco degli studenti associati al tuo account.</p> <!-- Rimosso stile individuale, aggiunta opacità -->
    </div>

    <!-- Elenco Studenti Esistenti -->
    <!-- Stile titolo aggiornato -->
    <h2 class="text-xl font-semibold mb-4 mt-8 text-neutral-darkest">Studenti Esistenti</h2>
    <!-- Stile loading aggiornato -->
    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento studenti...</div>
    <!-- Stile errore aggiornato -->
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento degli studenti: {{ error }}</span>
    </div>
    <!-- Responsive Table Container -->
    <div v-else-if="students.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <!-- Stile tabella aggiornato -->
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white">
        <!-- Stile thead aggiornato -->
        <thead class="bg-neutral-lightest">
          <tr>
            <!-- Stile th aggiornato -->
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Nome</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Cognome</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Codice Studente</th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider">Gruppi</th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
            <!-- Rimosso come da richiesta -->
            <!-- <th>Username</th> -->
            <!-- Aggiungere altre colonne se necessario -->
          </tr>
        </thead>
        <!-- Stile tbody aggiornato -->
        <tbody class="bg-white divide-y divide-neutral-DEFAULT">
          <!-- Stile tr aggiornato -->
          <tr v-for="student in students" :key="student.id" class="hover:bg-neutral-lightest transition-colors duration-150">
            <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ student.first_name }}</td>
            <!-- Stile td aggiornato -->
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ student.last_name }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">{{ student.student_code }}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-neutral-darker">
              <div v-if="student.groups && student.groups.length > 0" class="flex flex-wrap gap-1">
                <RouterLink
                  v-for="group in student.groups"
                  :key="group.id"
                  :to="{ name: 'GroupDetail', params: { id: group.id.toString() } }"
                  class="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200 hover:text-blue-800 transition-colors"
                  title="Visualizza Dettaglio Gruppo"
                >
                  {{ group.name }}
                </RouterLink>
              </div>
              <span v-else class="text-xs text-neutral-medium">Nessun gruppo</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-right">
              <div class="flex items-center justify-end space-x-2">
                <RouterLink
                  :to="{ name: 'student-progress-detail', params: { studentId: student.id.toString() } }"
                  class="p-2 inline-flex items-center text-secondary hover:text-secondary-dark bg-secondary-lightest hover:bg-secondary-lighter rounded-md"
                  title="Visualizza Progressi Studente"
                >
                  <ChartBarIcon class="h-5 w-5" />
                </RouterLink>
              </div>
            </td>
            <!-- Rimosso come da richiesta -->
            <!-- <td>{{ student.username }}</td> -->
            <!-- Aggiungere altre celle se necessario -->
          </tr>
        </tbody>
      </table>
    </div>
    <!-- Stile no students aggiornato -->
    <div v-else class="text-center py-10 text-neutral-dark">
      Nessuno studente trovato.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'; // Aggiungi nextTick
import { useRouter } from 'vue-router';
import { getMyStudents } from '@/api/students'; // Usa il nome corretto della funzione
import type { Student } from '@/types/users'; // Importa il tipo dalla sua fonte originale
// Rimosso import per createRegistrationToken
import BaseButton from '@/components/common/BaseButton.vue'; // Importa BaseButton
import { EyeIcon, ChartBarIcon } from '@heroicons/vue/24/outline'; // Aggiunto ChartBarIcon
 
const students = ref<Student[]>([]); // Conterrà l'elenco degli studenti
const isLoading = ref(false); // Stato di caricamento
const error = ref<string | null>(null); // Messaggio di errore caricamento studenti
const router = useRouter();

// Rimosso stato per generazione link

onMounted(async () => {
  isLoading.value = true;
  error.value = null;
  try {
    const studentsRes = await getMyStudents(); // Usa il nome corretto e salva la risposta
    students.value = studentsRes.data; // Estrai l'array dalla proprietà 'data'
    // console.log('Studenti ricevuti:', students.value); // Rimosso log di debug
  } catch (err: any) {
    console.error("Errore nel recupero degli studenti:", err);
    error.value = err.message || 'Si è verificato un errore sconosciuto.';
    // Potresti voler gestire tipi specifici di errore qui (es. 401, 403)
  } finally {
    isLoading.value = false;
  }
});

// Rimosse funzioni generateRegistrationLink e copyLinkToClipboard

const viewStudentDetails = (studentId: number) => {
  // TODO: Questa funzione potrebbe essere usata per navigare a una vista di modifica dettagli studente,
  // per ora il link diretto ai progressi è più utile.
  console.log(`TODO: Implementare navigazione a dettagli/modifica per studente ID: ${studentId}`);
  // router.push({ name: 'student-edit-detail', params: { studentId: studentId.toString() } }); // Esempio se esistesse
};
</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
/* Puoi aggiungere qui stili molto specifici se necessario */
</style>