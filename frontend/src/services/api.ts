import axios from "axios";
import type {
  Business,
  BusinessCreate,
  Document,
  ChatRequest,
  ChatResponse,
  BusinessLoginPayload,
  AppointmentPayload,
  Appointment,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 60000,
});

api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
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

// ------- Business API -------

export const businessApi = {
  register: async (data: BusinessCreate): Promise<Business> => {
    const res = await api.post<Business>("/business/register", data);
    return res.data;
  },

  login: async (payload: BusinessLoginPayload): Promise<Business> => {
    const res = await api.post<Business>("/business/login", payload);
    return res.data;
  },

  get: async (id: number): Promise<Business> => {
    const res = await api.get<Business>(`/business/${id}`);
    return res.data;
  },

  update: async (id: number, data: Partial<BusinessCreate>): Promise<Business> => {
    const res = await api.patch<Business>(`/business/update/${id}`, data);
    return res.data;
  },

  uploadDocument: async (businessId: number, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await api.post<Document>(
      `/business/upload-docs?business_id=${businessId}`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        timeout: 120000,
      }
    );
    return res.data;
  },

  getDocuments: async (businessId: number): Promise<Document[]> => {
    const res = await api.get<Document[]>(`/business/${businessId}/documents`);
    return res.data;
  },
};

// ------- Chat API -------

export const chatApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const res = await api.post<ChatResponse>("/chat/", request);
    return res.data;
  },
};

// ------- Appointments API -------

export const appointmentsApi = {
  create: async (payload: AppointmentPayload): Promise<Appointment> => {
    const res = await api.post<Appointment>("/appointments/", payload);
    return res.data;
  },
};

// ------- Health -------

export const healthCheck = async (): Promise<{ status: string }> => {
  const res = await api.get<{ status: string }>("/health");
  return res.data;
};

export default api;
