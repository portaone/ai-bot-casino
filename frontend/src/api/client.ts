import axios from 'axios';
import { config } from '@/config';

const apiClient = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: add auth token
apiClient.interceptors.request.use((reqConfig) => {
  const token = localStorage.getItem('aibotcasino-token');
  if (token) {
    reqConfig.headers.Authorization = `Bearer ${token}`;
  }
  return reqConfig;
});

// Response interceptor: handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('aibotcasino-token');
      // Don't redirect - let the component handle it
    }
    return Promise.reject(error);
  }
);

export default apiClient;
