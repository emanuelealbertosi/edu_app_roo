import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useRouter } from 'vue-router' // Importa useRouter
import * as authService from '@/api/auth' // Import auth service (including getTeacherProfile and refreshTokenTeacher)

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
      // Fetch real user data after getting tokens
      // Store the refresh token FIRST
      localStorage.setItem('teacher_refresh_token', response.refresh);
      refreshToken.value = response.refresh;

      // Now fetch the user profile using the new access token
      try {
        await fetchUserProfile(response.access); // Pass the new access token
        // setAuthData is called inside fetchUserProfile on success, using the stored refresh token
      } catch (fetchError) {
        // If fetching profile fails even with new tokens, clear everything and fail login
        console.error("Login succeeded but fetching profile failed:", fetchError);
        // Clear potentially stored refresh token as well
        clearAuthData();
        error.value = 'Login succeeded but failed to retrieve user profile.';
        throw new Error(error.value);
      }

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

  // Action to fetch user profile
  async function fetchUserProfile(currentToken: string | null = accessToken.value) {
    if (!currentToken) {
      console.log("[fetchUserProfile] No token available.");
      clearAuthData(); // Ensure clean state if no token
      return; // Exit if no token
    }

    loading.value = true; // Indicate loading state
    error.value = null;
    console.log("[fetchUserProfile] Attempting to fetch profile...");

    try {
      // Set the current token for the API client (important!)
      // This assumes apiClient has an interceptor or method to set the Authorization header
      // If not, you might need to pass the token explicitly to getTeacherProfile
      // For simplicity, we assume an interceptor sets the header based on accessToken.value
      // We need to temporarily set accessToken.value for the API call if a new token was passed
      const oldToken = accessToken.value;
      accessToken.value = currentToken; // Use the provided token for the API call
      localStorage.setItem('teacher_access_token', currentToken); // Store the potentially new token

      const fetchedUser = await authService.getTeacherProfile();

      // Use setAuthData to update state correctly, keeping the refresh token if it exists
      const currentRefreshToken = refreshToken.value || localStorage.getItem('teacher_refresh_token');
      if (currentRefreshToken) {
          setAuthData(currentToken, currentRefreshToken, fetchedUser);
          console.log("[fetchUserProfile] Profile fetched and auth data set:", fetchedUser);
      } else {
          // This case should ideally not happen if login provides both tokens
          console.error("[fetchUserProfile] Access token exists, but refresh token is missing. Clearing auth data.");
          clearAuthData();
          throw new Error("Refresh token missing after profile fetch.");
      }

    } catch (fetchError: any) {
      console.error("[fetchUserProfile] Failed to fetch user profile:", fetchError);
      error.value = fetchError.message || 'Failed to fetch profile';
      clearAuthData(); // Clear data on error (e.g., invalid token)
      // Don't redirect here, let the caller (e.g., navigation guard) handle it
      // router.push({ name: 'login' });
      throw fetchError; // Re-throw error
    } finally {
       // Restore old token if it was different (only relevant if called with a new token during login)
       // if (accessToken.value !== oldToken) {
       //   accessToken.value = oldToken; // This might be complex, ensure state consistency
       // }
      loading.value = false; // Reset loading state
    }
  }

  // Action for token refresh
  async function refreshTokenAction() {
    const currentRefreshToken = refreshToken.value;
    if (!currentRefreshToken) {
      console.error("Refresh Token Action: No refresh token available.");
      clearAuthData(); // Logout if no refresh token
      throw new Error("No refresh token available.");
    }

    loading.value = true; // Potrebbe essere utile indicare il caricamento
    error.value = null;

    try {
      console.log("Attempting token refresh...");
      const response = await authService.refreshTokenTeacher({ refresh: currentRefreshToken });
      // Aggiorna solo l'access token, il refresh token rimane lo stesso (di solito)
      accessToken.value = response.access;
      localStorage.setItem('teacher_access_token', response.access);
      console.log("Token refreshed successfully via action.");
      // Non aggiornare user qui, solo il token
    } catch (refreshError: any) {
      console.error("Failed to refresh token via action:", refreshError);
      error.value = refreshError.message || 'Failed to refresh token';
      clearAuthData(); // Logout on refresh failure
      throw refreshError; // Rilancia l'errore
    } finally {
      loading.value = false;
    }
  }

  // --- INITIALIZATION LOGIC ---
  // If we find a token on startup, try to fetch the user profile
  if (accessToken.value && !user.value) {
    console.log("Auth Store: Token found in localStorage. Attempting to fetch user profile...");
    fetchUserProfile().catch(err => {
        console.error("Auth Store: Initial profile fetch failed, user will be logged out.", err);
        // Error handling (clearing data) is done within fetchUserProfile
    });
  }
  // --- END OF INITIALIZATION LOGIC ---


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
    clearAuthData, // Expose if needed externally
    fetchUserProfile, // Expose if needed (e.g., for manual refresh)
    refreshTokenAction // Expose the refresh action
  }
})