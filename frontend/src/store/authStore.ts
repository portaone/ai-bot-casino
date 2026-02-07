import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  accessToken: string | null;
  apiToken: string | null;
  user: {
    id: string;
    first_name: string;
    email: string;
    bot_id?: string;
  } | null;

  setAuth: (token: string, user: any) => void;
  setApiToken: (token: string) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      apiToken: null,
      user: null,

      setAuth: (token, user) => {
        localStorage.setItem('aibotcasino-token', token);
        set({ accessToken: token, user });
      },

      setApiToken: (token) => {
        set({ apiToken: token });
      },

      logout: () => {
        localStorage.removeItem('aibotcasino-token');
        set({ accessToken: null, apiToken: null, user: null });
      },

      isAuthenticated: () => !!get().accessToken,
    }),
    {
      name: 'aibotcasino-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        apiToken: state.apiToken,
        user: state.user,
      }),
    }
  )
);
