import apiClient from './config';

// Define expected response structure for teacher/admin login
interface LoginResponse {
  access: string;
  refresh: string;
  // Add user details if returned by login endpoint, otherwise fetch separately
}

// Define expected payload for teacher/admin login
interface LoginCredentials {
  username?: string; // Use username for teachers/admins
  email?: string;    // Or email if supported
  password?: string;
}


export const loginTeacher = async (credentials: LoginCredentials): Promise<LoginResponse> => {
  console.log('[api/auth] Attempting teacher login with credentials:', credentials); // Log prima della chiamata
  try {
    // Use the standard JWT token obtain endpoint for teachers/admins
    console.log('[api/auth] Sending POST request to /api/auth/token/'); // Corrected URL
    const response = await apiClient.post<LoginResponse>('/auth/token/', credentials); // Corrected URL
    console.log('[api/auth] Login API call successful:', response.data); // Log dopo successo
    return response.data;
  } catch (error: any) {
    console.error('[api/auth] Teacher login API error:', error.response?.data || error.message, error); // Log errore completo
    throw new Error(error.response?.data?.detail || 'Login failed');
  }
};

// Optional: Add function for token refresh if needed
// export const refreshToken = async (refresh: string): Promise<{ access: string }> => { ... }

// Optional: Add function for logout (e.g., blacklist token) if backend supports it
// export const logoutTeacher = async (refresh: string): Promise<void> => { ... }

// Optional: Add function to fetch teacher profile data
// export const getTeacherProfile = async (): Promise<TeacherUser> => { ... }