import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useRouter } from 'vue-router' // Importa useRouter
import * as authService from '@/api/auth' // Import auth service

// Define the shape of the user object for teachers (adjust as needed)
interface TeacherUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string; // Should be 'TEACHER' or 'ADMIN'
}

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter(); // Ottieni l'istanza del router qui
  const user = ref<TeacherUser | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('teacher_access_token')) // Use a different key than student
  const refreshToken = ref<string | null>(localStorage.getItem('teacher_refresh_token'))
  const error = ref<string | null>(null)
  const loading = ref(false)

  // Computed property for authentication status
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  // Function to set tokens and user info in state and localStorage
  function setAuthData(access: string, refresh: string, userData: TeacherUser) {
    accessToken.value = access
    refreshToken.value = refresh
    user.value = userData
    localStorage.setItem('teacher_access_token', access)
    localStorage.setItem('teacher_refresh_token', refresh)
    error.value = null
  }

  // Function to clear auth data
  function clearAuthData() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('teacher_access_token')
    localStorage.removeItem('teacher_refresh_token')
  }

  // Login action
  async function login(usernameInput: string, passwordInput: string) {
    loading.value = true
    error.value = null
    try {
      // Use username for login with the standard JWT endpoint
      const response = await authService.loginTeacher({ username: usernameInput, password: passwordInput });

      // NOTE: The standard /api/token/ endpoint only returns tokens.
      // We need to make another call to fetch user details after successful login.
      // For now, we'll store a placeholder user or decode the token if possible (requires jwt-decode library).

      // Placeholder user data - replace with actual fetch/decode logic
      const placeholderUser: TeacherUser = {
          id: 0, // Need to fetch this
          username: usernameInput,
          email: '', // Need to fetch this
          first_name: '', // Need to fetch this
          last_name: '', // Need to fetch this
          role: 'TEACHER' // Assume teacher for now, fetch/decode for real role
      };
      // TODO: Implement fetchUserProfile() or decode token to get real user data

      setAuthData(response.access, response.refresh, placeholderUser); // Use placeholder for now
      // La navigazione verrà gestita dal componente che chiama login
      // await router.push({ name: 'dashboard' }); // <-- Rimuovere redirect

    } catch (err: any) {
      clearAuthData();
      error.value = err.message || 'Login failed';
      console.error("Login error:", err); // Log the actual error
      throw err; // Re-throw error for component handling
    } finally {
      loading.value = false;
    }
  }

  // Logout action
  async function logout() {
    console.log("Logging out teacher...");
    // Optional: Add backend call to invalidate token here if implemented
    // try { await authService.logoutTeacher(refreshToken.value); } catch(e) {}
    clearAuthData();
    router.push({ name: 'login' }); // Reindirizza alla pagina di login
  }

  // TODO: Add action to fetch user profile if needed
  // TODO: Add action for token refresh

  // --- MODIFIED INITIALIZATION LOGIC ---
  // If we find a token on startup but don't have user data,
  // set a placeholder user to make isAuthenticated work.
  // A more robust solution would verify the token and fetch real data.
  if (accessToken.value && !user.value) {
    console.warn("Auth Store: Token found in localStorage but no user data. Setting placeholder user for isAuthenticated.");
    user.value = {
        id: 0, // Placeholder ID
        username: 'Unknown', // Placeholder username
        email: '',
        first_name: 'Placeholder',
        last_name: 'User',
        role: 'TEACHER' // Assume TEACHER, could be ADMIN
    };
    // TODO: Ideally, call an API here to verify the token
    // and fetch real user data (e.g., fetchUserProfile()).
  }
  // --- END OF MODIFIED INITIALIZATION LOGIC ---


  return {
    user,
    accessToken,
    refreshToken,
    error,
    loading,
    isAuthenticated,
    login,
    logout,
    setAuthData, // Expose if needed externally
    clearAuthData // Expose if needed externally
  }
})