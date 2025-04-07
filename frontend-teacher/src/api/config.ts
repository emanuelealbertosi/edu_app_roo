import axios from 'axios';
import { useAuthStore } from '@/stores/auth'; // Import auth store

const apiClient = axios.create({
  // URL base del backend. Viene letto dalla variabile d'ambiente VITE_API_BASE_URL
  // che viene impostata durante il build Docker.
  // In sviluppo locale (npm run dev), Vite usa il file .env.development o simili.
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/',
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

// Add interceptor for handling 401 Unauthorized errors
apiClient.interceptors.response.use(
  (response) => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    return response;
  },
  (error) => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    const originalRequest = error.config;

    // Check if the error is 401 Unauthorized and it's not a request to the login endpoint itself
    if (error.response && error.response.status === 401 && originalRequest.url !== '/auth/token/') {
      console.warn('API Interceptor: Received 401 Unauthorized. Logging out and redirecting.');
      const authStore = useAuthStore();
      authStore.logout(); // Call the logout action in your auth store

      // Redirect to login page
      // We need to access the router instance here. Since this is a module,
      // we cannot directly use useRouter(). We might need to pass the router instance
      // during setup or handle redirection within the component that catches the error.
      // For simplicity, we'll just log it here and rely on the navigation guard
      // or component-level error handling to perform the redirect.
      // Alternatively, you could emit an event or use a global state management solution.
      // router.push({ name: 'login' }); // This won't work directly here

      // It's often better to let the navigation guard handle the redirect after logout
      // by checking the authentication state on route changes.
    }

    // Return any error which is not 401
    return Promise.reject(error);
  }
);

export default apiClient;