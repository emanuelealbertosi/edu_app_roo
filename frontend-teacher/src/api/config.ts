import axios from 'axios';
import { useAuthStore } from '@/stores/auth'; // Import auth store

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api', // Your Django API base URL
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add interceptor to include Authorization header
apiClient.interceptors.request.use(
  (config) => {
    // Get store instance *inside* the interceptor to avoid issues with Pinia initialization order
    const authStore = useAuthStore();
    const token = authStore.accessToken; // Assumes your store has an accessToken getter/property
    if (token && config.headers) { // Check if headers exist
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add interceptor for token refresh (implement later)
// apiClient.interceptors.response.use(...)

export default apiClient;