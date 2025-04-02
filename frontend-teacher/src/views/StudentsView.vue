<template>
  <div class="students-view">
    <h1>Gestione Studenti</h1>
    <p>Elenco degli studenti associati al tuo account.</p>

    <div v-if="isLoading" class="loading">Caricamento studenti...</div>
    <div v-else-if="error" class="error-message">
      Errore nel caricamento degli studenti: {{ error }}
    </div>
    <div v-else-if="students.length > 0" class="students-list">
      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Cognome</th>
            <th>Codice Studente</th>
            <th>Username</th>
            <!-- Aggiungere altre colonne se necessario -->
          </tr>
        </thead>
        <tbody>
          <tr v-for="student in students" :key="student.id">
            <td>{{ student.first_name }}</td>
            <td>{{ student.last_name }}</td>
            <td>{{ student.student_code }}</td>
            <td>{{ student.username }}</td>
            <!-- Aggiungere altre celle se necessario -->
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="no-students">
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
.students-view {
  padding: 20px;
}

.loading,
.error-message,
.no-students {
  margin-top: 20px;
  font-style: italic;
  color: #666;
}

.error-message {
  color: red;
  font-weight: bold;
}

.students-list {
  margin-top: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

th {
  background-color: #f2f2f2;
}
</style>