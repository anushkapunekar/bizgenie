export interface Business {
  id: number;
  name: string;
  description?: string;
  services: string[];
  working_hours: Record<string, { open: string; close: string }>;
  contact_email?: string;
  contact_phone?: string;
  created_at: string;
  updated_at: string;
}

export interface BusinessCreate {
  name: string;
  description?: string;
  services: string[];
  working_hours: Record<string, { open: string; close: string }>;
  contact_email?: string;
  contact_phone?: string;
}

export interface Document {
  id: number;
  business_id: number;
  filename: string;
  file_path: string;
  file_type: string;
  metadata?: Record<string, any>;
  created_at: string;
}

export interface ChatRequest {
  business_id: number;
  user_name: string;
  user_message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  reply: string;
  tool_actions: any[];
  conversation_id: string;
  intent?: string;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  intent?: string;
}

