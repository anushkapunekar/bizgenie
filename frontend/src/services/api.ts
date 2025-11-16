import axios from 'axios';
import type { Business, BusinessCreate, Document, ChatRequest, ChatResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 second timeout for LLM responses
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', {
      url: error.config?.url,
      status: error.response?.status,
      message: error.message,
      detail: error.response?.data?.detail,
    });
    return Promise.reject(error);
  }
);

// Business API
export const businessApi = {
  register: async (data: BusinessCreate): Promise<Business> => {
    const response = await api.post<Business>('/business/register', data);
    return response.data;
  },

  get: async (id: number): Promise<Business> => {
    const response = await api.get<Business>(`/business/${id}`);
    return response.data;
  },

  update: async (id: number, data: Partial<BusinessCreate>): Promise<Business> => {
    const response = await api.patch<Business>(`/business/update/${id}`, data);
    return response.data;
  },

  uploadDocument: async (businessId: number, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<Document>(
      `/business/upload-docs?business_id=${businessId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes for file upload
      }
    );
    return response.data;
  },

  getDocuments: async (businessId: number): Promise<Document[]> => {
    const response = await api.get<Document[]>(`/business/${businessId}/documents`);
    return response.data;
  },
};

// Chat API
export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat/', request);
    return response.data;
  },
};

// Health check
export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await api.get<{ status: string }>('/health');
  return response.data;
};

export default api;

