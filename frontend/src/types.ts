export interface Business {
    id: number;
    name: string;
    description?: string | null;
    services: string[];
    working_hours: Record<string, { open: string; close: string }>;
    contact_email?: string | null;
    contact_phone?: string | null;
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
  
  export interface BusinessLoginPayload {
    business_id?: number;
    contact_email?: string;
    contact_phone?: string;
    name?: string;
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
  
  export type Sender = "user" | "assistant";
  
  export interface Message {
    id: string;
    text: string;
    sender: Sender;
    timestamp: Date;
    intent?: string | null;
    tool_actions?: any[];
  }
  
  export interface ChatProfile {
    name: string;
    email?: string;
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
    intent?: string | null;
  }
  
  export interface AppointmentPayload {
    business_id: number;
    customer_name: string;
    customer_email?: string | null;
    date: string; // YYYY-MM-DD
    time: string; // HH:MM
  }
  
  export interface Appointment {
    id: number;
    business_id: number;
    customer_name: string;
    customer_email?: string | null;
    customer_phone?: string | null;
    appointment_date: string;
    service?: string | null;
    status: string;
    created_at: string;
  }
  