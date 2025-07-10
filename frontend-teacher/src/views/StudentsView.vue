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
    <!-- Filtro -->
    <div class="mb-4">
      <input
        type="text"
        v-model="searchQuery"
        placeholder="Cerca per nome, cognome, codice studente o gruppo..."
        class="mt-1 block w-full px-3 py-2 bg-white border border-neutral-DEFAULT rounded-md shadow-sm placeholder-neutral-dark focus:outline-none focus:ring-primary focus:border-primary sm:text-sm"
      />
    </div>

    <div v-if="isLoading" class="text-center py-10 text-neutral-dark">Caricamento studenti...</div>
    <div v-else-if="error" class="bg-error/10 border border-error text-error px-4 py-3 rounded relative mb-6" role="alert">
      <strong class="font-bold">Errore!</strong>
      <span class="block sm:inline"> Errore nel caricamento degli studenti: {{ error }}</span>
    </div>
    
    <div v-else-if="filteredAndSortedStudents.length > 0" class="overflow-x-auto shadow-md rounded-lg mt-6">
      <table class="min-w-full divide-y divide-neutral-DEFAULT bg-white">
        <thead class="bg-neutral-lightest">
          <tr>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('first_name')">
              Nome
              <span v-if="sortKey === 'first_name'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('last_name')">
              Cognome
              <span v-if="sortKey === 'last_name'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('student_code')">
              Codice Studente
              <span v-if="sortKey === 'student_code'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-neutral-darker uppercase tracking-wider cursor-pointer hover:text-primary" @click="sortBy('groups')">
              Gruppi
              <span v-if="sortKey === 'groups'"><ChevronUpIcon v-if="sortOrder === 'asc'" class="h-4 w-4 inline-block" /><ChevronDownIcon v-else class="h-4 w-4 inline-block" /></span>
            </th>
            <th scope="col" class="px-6 py-3 text-right text-xs font-medium text-neutral-darker uppercase tracking-wider">Azioni</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-neutral-DEFAULT">
          <tr v-for="student in filteredAndSortedStudents" :key="student.id" class="hover:bg-neutral-lightest transition-colors duration-150">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-neutral-darkest">{{ student.first_name }}</td>
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
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="text-center py-10 text-neutral-dark">
      <span v-if="searchQuery">Nessuno studente trovato per "{{ searchQuery }}".</span>
      <span v-else>Nessuno studente trovato.</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { getMyStudents } from '@/api/students';
import type { Student } from '@/types/users';
import BaseButton from '@/components/common/BaseButton.vue';
import { ChartBarIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/vue/24/outline';

const students = ref<Student[]>([]);
const isLoading = ref(false);
const error = ref<string | null>(null);
const router = useRouter();
const searchQuery = ref('');
const sortKey = ref('last_name');
const sortOrder = ref('asc');

const filteredAndSortedStudents = computed(() => {
  const query = searchQuery.value.toLowerCase().trim();

  const filtered = query
    ? students.value.filter(s => {
        const firstName = s.first_name.toLowerCase();
        const lastName = s.last_name.toLowerCase();
        const studentCode = s.student_code.toLowerCase();
        const inGroup = s.groups && s.groups.some(group => group.name.toLowerCase().includes(query));
        return firstName.includes(query) || lastName.includes(query) || studentCode.includes(query) || inGroup;
      })
    : students.value;

  return filtered.slice().sort((a, b) => {
    let valA: any;
    let valB: any;

    if (sortKey.value === 'groups') {
      valA = a.groups && a.groups.length > 0 ? a.groups[0].name.toLowerCase() : '';
      valB = b.groups && b.groups.length > 0 ? b.groups[0].name.toLowerCase() : '';
    } else {
      valA = a[sortKey.value as keyof Student];
      valB = b[sortKey.value as keyof Student];

      if (typeof valA === 'string' && typeof valB === 'string') {
        valA = valA.toLowerCase();
        valB = valB.toLowerCase();
      }
    }
    
    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1;
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

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
  console.log(`TODO: Implementare navigazione a dettagli/modifica per studente ID: ${studentId}`);
};

const sortBy = (key: string) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};
</script>

<style scoped>
/* Stili specifici rimossi in favore di Tailwind */
/* Puoi aggiungere qui stili molto specifici se necessario */
</style>