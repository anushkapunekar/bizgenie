import axios from "axios";
import type {
  Business,
  BusinessCreate,
  Document,
  ChatRequest,
  ChatResponse,
  BusinessLoginPayload,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(
      `API Request: ${config.method?.toUpperCase()} ${config.url}`
    );
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(
      `API Response: ${response.status} ${response.config.url}`
    );
    return response;
  },
  (error) => {
    console.error("API Response Error:", {
      url: error.config?.url,
      status: error.response?.status,
      message: error.message,
      detail: error.response?.data?.detail,
    });
    return Promise.reject(error);
  }
);

// -----------------------------
// BUSINESS API
// -----------------------------
export const businessApi = {
  register: async (data: BusinessCreate): Promise<Business> => {
    const r = await api.post<Business>("/business/register", data);
    return r.data;
  },

  login: async (payload: BusinessLoginPayload): Promise<Business> => {
    const r = await api.post<Business>("/business/login", payload);
    return r.data;
  },

  get: async (id: number): Promise<Business> => {
    const r = await api.get<Business>(`/business/${id}`);
    return r.data;
  },

  update: async (id: number, data: Partial<BusinessCreate>): Promise<Business> => {
    const r = await api.patch<Business>(`/business/update/${id}`, data);
    return r.data;
  },

  uploadDocument: async (businessId: number, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append("file", file);

    const r = await api.post<Document>(
      `/business/upload-docs?business_id=${businessId}`,
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      }
    );

    return r.data;
  },

  getDocuments: async (businessId: number): Promise<Document[]> => {
    const r = await api.get<Document[]>(`/business/${businessId}/documents`);
    return r.data;
  },
};

// -----------------------------
// CHAT API
// -----------------------------
export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const r = await api.post<ChatResponse>("/chat/", request);
    return r.data;
  },
};

// -----------------------------
// APPOINTMENTS API
// -----------------------------
export const appointmentsApi = {
  create: async (payload: {
    business_id: number;
    customer_name: string;
    customer_email?: string | null;
    date: string;
    time: string;
  }) => {
    const r = await api.post("/appointments/", payload);
    return r.data;
  },
};

// -----------------------------
// HEALTH CHECK
// -----------------------------
export const healthCheck = async (): Promise<{ status: string }> => {
  const r = await api.get<{ status: string }>("/health");
  return r.data;
};

export default api;
