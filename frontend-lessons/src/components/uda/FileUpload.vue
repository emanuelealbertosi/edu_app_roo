<template>
  <div class="file-upload">
    <input
      type="file"
      ref="fileInput"
      @change="handleFileChange"
      class="form-control"
      :accept="accept"
    />
    <div v-if="selectedFile" class="mt-2">
      <p class="mb-1">
        File selezionato: <strong>{{ selectedFile.name }}</strong> ({{ formatFileSize(selectedFile.size) }})
      </p>
      <button class="btn btn-sm btn-outline-danger" @click="removeFile">
        Rimuovi
      </button>
    </div>
    <div v-if="currentFileUrl && !selectedFile" class="mt-2">
        <p class="mb-1">File attuale: <a :href="currentFileUrl" target="_blank">{{ getFileNameFromUrl(currentFileUrl) }}</a></p>
        <p class="text-muted small">Seleziona un nuovo file per sostituirlo.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, type PropType } from 'vue';

const props = defineProps({
  accept: {
    type: String,
    default: '*' // Accetta tutti i tipi di file di default
  },
  currentFileUrl: { // URL di un file già esistente, per visualizzazione
    type: String,
    default: ''
  }
});

const emit = defineEmits(['file-selected', 'file-removed']);

const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0];
    emit('file-selected', selectedFile.value);
  } else {
    removeFile(); // Se l'utente deseleziona il file
  }
};

const removeFile = () => {
  selectedFile.value = null;
  if (fileInput.value) {
    fileInput.value.value = ''; // Resetta l'input file
  }
  emit('file-removed');
};

const formatFileSize = (bytes: number, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

const getFileNameFromUrl = (url: string): string => {
  if (!url) return '';
  try {
    const urlParts = url.split('/');
    return urlParts[urlParts.length - 1] || url;
  } catch (e) {
    return url;
  }
};

// Metodo per resettare lo stato del componente dall'esterno se necessario
const reset = () => {
  removeFile();
};

defineExpose({ reset });
</script>

<style scoped>
.file-upload {
  padding: 1rem;
  border: 1px dashed #ccc;
  border-radius: 4px;
  background-color: #f9f9f9;
}
.file-upload:hover {
  border-color: #aaa;
}
</style>