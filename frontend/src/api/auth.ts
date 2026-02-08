import apiClient from './client';

export interface RegisterRequest {
  first_name: string;
  email: string;
  recaptcha_token?: string;
  callback_url?: string;
  accepted_policies?: Record<string, boolean>;
}

export interface LoginRequest {
  email: string;
  recaptcha_token?: string;
  callback_url?: string;
}

export interface VerifyOtpRequest {
  otp_id: string;
  otp: string;
  recaptcha_token?: string;
}

export interface VerifyMagicLinkRequest {
  otp_id: string;
  magic_token: string;
}

export interface SetupBotRequest {
  bot_name: string;
  avatar_seed: string;
}

export interface AuthResponse {
  otp_id: string;
  otp_expires_at: string;
}

export interface VerifyResponse {
  access_token: string;
  expires_at: string;
  api_token?: string;
  is_new_user: boolean;
}

export interface SetupBotResponse {
  bot_id: string;
  api_token: string;
  mcp_url: string;
}

export interface UserInfo {
  id: string;
  first_name: string;
  email: string;
  bot_id?: string;
  created_at: string;
  mcp_url?: string;
  balance?: number;
}

export const authApi = {
  register: (data: RegisterRequest) =>
    apiClient.post<AuthResponse>('/api/v1/auth/register', data),

  login: (data: LoginRequest) =>
    apiClient.post<AuthResponse>('/api/v1/auth/login', data),

  verifyOtp: (data: VerifyOtpRequest) =>
    apiClient.post<VerifyResponse>('/api/v1/auth/verify-otp', data),

  verifyMagicLink: (data: VerifyMagicLinkRequest) =>
    apiClient.post<VerifyResponse>('/api/v1/auth/verify-magic-link', data),

  setupBot: (data: SetupBotRequest) =>
    apiClient.post<SetupBotResponse>('/api/v1/auth/setup-bot', data),

  regenerateToken: () =>
    apiClient.post<SetupBotResponse>('/api/v1/auth/regenerate-token'),

  getMe: () =>
    apiClient.get<UserInfo>('/api/v1/auth/me'),
};
