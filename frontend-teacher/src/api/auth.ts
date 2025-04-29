import apiClient from './apiClient'; // Correggi import

// Define expected response structure for teacher/admin login
interface LoginResponse {
  access: string;
  refresh: string;
  // Add user details if returned by login endpoint, otherwise fetch separately
}

// Define the shape of the user object for teachers (matching store)
interface TeacherUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string; // 'TEACHER' or 'ADMIN'
  can_create_public_groups?: boolean; // Aggiunto campo per permesso
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

// Function for token refresh
interface RefreshTokenPayload {
  refresh: string;
}
interface RefreshTokenResponse {
  access: string;
}
export const refreshTokenTeacher = async (payload: RefreshTokenPayload): Promise<RefreshTokenResponse> => {
  console.log('[api/auth] Attempting token refresh...');
  try {
    const response = await apiClient.post<RefreshTokenResponse>('/auth/token/refresh/', payload);
    console.log('[api/auth] Token refresh successful.');
    return response.data;
  } catch (error: any) {
    console.error('[api/auth] Token refresh API error:', error.response?.data || error.message, error);
    // Non lanciare errore qui necessariamente, l'interceptor potrebbe gestirlo,
    // ma è utile loggarlo. L'interceptor rilancerà se necessario.
    throw new Error(error.response?.data?.detail || 'Token refresh failed');
  }
};

// Optional: Add function for logout (e.g., blacklist token) if backend supports it
// export const logoutTeacher = async (refresh: string): Promise<void> => { ... }

// Function to fetch teacher profile data
export const getTeacherProfile = async (): Promise<TeacherUser> => {
  console.log('[api/auth] Fetching teacher profile...');
  try {
    // Assuming the profile endpoint is /api/admin/users/me/ based on router registration
    const response = await apiClient.get<TeacherUser>('/admin/users/me/'); // Use the likely correct endpoint
    console.log('[api/auth] Teacher profile fetched successfully:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('[api/auth] Get teacher profile API error:', error.response?.data || error.message, error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch user profile');
  }
};