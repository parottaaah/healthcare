import apiClient from "./client";

export interface AuthResponse {
  message: string;
}

export interface UserResponse {
  id: string;
  email: string;
  name: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  name: string;
  phone_number: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export async function register(payload: RegisterPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/register", payload);
  return data;
}

export async function login(payload: LoginPayload): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", payload);
  return data;
}

export async function getMe(): Promise<UserResponse> {
  const { data } = await apiClient.get<UserResponse>("/auth/me");
  return data;
}

export async function logout(): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/logout");
  return data;
}
