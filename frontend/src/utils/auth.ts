import axios from "axios";

const API_BASE = "http://localhost:5000/api/v1";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    email: string;
    display_name: string;
    role: string;
    is_active: boolean;
  };
}

export interface SignupRequest {
  email: string;
  password: string;
  display_name?: string;
}

// ── Token Management ──────────────────────────────────────────────────────────

export function setAuthToken(token: string) {
  localStorage.setItem("access_token", token);
  // Add token to axios default headers for all future requests
  axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
}

export function getAuthToken(): string | null {
  return localStorage.getItem("access_token");
}

export function clearAuthToken() {
  localStorage.removeItem("access_token");
  delete axios.defaults.headers.common["Authorization"];
}

// ── Initialize axios with stored token ────────────────────────────────────────

const storedToken = getAuthToken();
if (storedToken) {
  axios.defaults.headers.common["Authorization"] = `Bearer ${storedToken}`;
}

// ── Auth API Calls ────────────────────────────────────────────────────────────

export async function login(data: LoginRequest): Promise<AuthResponse> {
  try {
    console.log("Login attempt with:", data.email);
    const response = await axios.post<AuthResponse>(
      `${API_BASE}/auth/login`,
      data
    );
    console.log("Login successful, token:", response.data.access_token.substring(0, 10) + "...");
    // Store token for future requests
    setAuthToken(response.data.access_token);
    return response.data;
  } catch (error: any) {
    console.error("Login error:", error.response?.status, error.response?.data);
    const message = error.response?.data?.error || error.message;
    throw new Error(message);
  }
}

export async function signup(data: SignupRequest): Promise<AuthResponse> {
  try {
    const response = await axios.post<AuthResponse>(
      `${API_BASE}/auth/register`,
      data
    );
    return response.data;
  } catch (error: any) {
    const message = error.response?.data?.error || error.message;
    throw new Error(message);
  }
}

export async function logout(): Promise<void> {
  try {
    await axios.post(`${API_BASE}/auth/logout`);
  } catch (error) {
    // Still clear local token even if logout fails
    console.error("Logout error:", error);
  } finally {
    clearAuthToken();
  }
}

export async function getCurrentUser() {
  try {
    const response = await axios.get(`${API_BASE}/auth/me`);
    return response.data;
  } catch (error: any) {
    console.error("getCurrentUser error:", error.response?.status, error.response?.data);
    const message = error.response?.data?.error || error.message;
    throw new Error(message);
  }
}
