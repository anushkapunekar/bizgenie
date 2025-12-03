import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Send, Bot, User, Loader2 } from "lucide-react";
import { chatApi, businessApi } from "../services/api";
import type { Message, Business, ChatProfile } from "../types";
import { getApiErrorMessage } from "../utils/errors";
import BookingModal from "../components/BookingModal";

const CHAT_PROFILE_STORAGE_KEY = "bizgenie.chatProfile";

const getStoredProfile = (): ChatProfile => {
  try {
    const raw = localStorage.getItem(CHAT_PROFILE_STORAGE_KEY);
    if (!raw) return { name: "" };
    const parsed = JSON.parse(raw);
    return { name: parsed.name || "", email: parsed.email || "" };
  } catch {
    return { name: "" };
  }
};

const persistProfile = (profile: ChatProfile) => {
  localStorage.setItem(CHAT_PROFILE_STORAGE_KEY, JSON.stringify(profile));
};

const getChatSessionKey = (businessId?: string) =>
  businessId ? `bizgenie.chat.session.${businessId}` : null;

interface StoredMessage {
  id: string;
  text: string;
  sender: "user" | "assistant";
  timestamp: string;
  intent?: string;
  tool_actions?: any[];
}

interface StoredChatSession {
  conversationId?: string | null;
  messages: StoredMessage[];
  profile?: ChatProfile;
}

export default function Chat() {
  const { id } = useParams<{ id: string }>();
  const [business, setBusiness] = useState<Business | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  const [showBookingModal, setShowBookingModal] = useState(false);

  const initialProfile = useMemo(() => getStoredProfile(), []);
  const [profile, setProfile] = useState<ChatProfile>(initialProfile);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const sessionHydratedRef = useRef(false);

  const chatSessionKey = useMemo(() => getChatSessionKey(id), [id]);
  const readyToChat = Boolean(profile.name);
  const businessId = id ? Number(id) : null;

  // Load business
  const loadBusiness = useCallback(async () => {
    if (!businessId) return;
    try {
      const data = await businessApi.get(businessId);
      setBusiness(data);
    } catch (error) {
      console.error("Failed to load business:", error);
    }
  }, [businessId]);

  useEffect(() => {
    loadBusiness();
  }, [loadBusiness]);

  useEffect(() => {
    persistProfile(profile);
  }, [profile]);

  // Hydrate session
  useEffect(() => {
    if (!chatSessionKey) {
      sessionHydratedRef.current = true;
      return;
    }

    const saved = sessionStorage.getItem(chatSessionKey);
    if (saved) {
      try {
        const parsed: StoredChatSession = JSON.parse(saved);

        if (parsed.messages?.length) {
          setMessages(
            parsed.messages.map((m) => ({
              ...m,
              timestamp: new Date(m.timestamp),
            })) as any
          );
        }

        if (parsed.conversationId) setConversationId(parsed.conversationId);

        if (parsed.profile) {
          setProfile(parsed.profile);
        }
      } catch (err) {
        console.error("Hydration error:", err);
      }
    }

    sessionHydratedRef.current = true;
  }, [chatSessionKey]);

  // Persist session
  useEffect(() => {
    if (!chatSessionKey) return;

    const payload: StoredChatSession = {
      conversationId,
      profile,
      messages: messages.map((m: any) => ({
        ...m,
        timestamp: m.timestamp.toISOString(),
        tool_actions: m.tool_actions,
      })),
    };

    sessionStorage.setItem(chatSessionKey, JSON.stringify(payload));
  }, [messages, conversationId, profile, chatSessionKey]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Welcome message
  useEffect(() => {
    if (!business || !readyToChat || !sessionHydratedRef.current) return;
    if (messages.length > 0) return;

    const hours = business.working_hours || {};
    const day = Object.entries(hours).find(
      ([, v]: any) => v?.open && v?.close
    );

    let hoursText = "";
    if (day) {
      const [d, v]: any = day;
      hoursText = `${d.charAt(0).toUpperCase() + d.slice(1)}: ${
        v.open
      } - ${v.close}`;
    }

    setMessages([
      {
        id: `welcome-${Date.now()}`,
        text: `Hi ${profile.name}! I'm ${business.name}'s virtual assistant. Ask me about services, pricing, or availability.${
          hoursText ? ` We're typically open ${hoursText}.` : ""
        }`,
        sender: "assistant",
        timestamp: new Date(),
      } as any,
    ]);
  }, [business, readyToChat, messages.length, profile.name]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || !id) return;

    const msg = input.trim();

    // Add user message to UI
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        text: msg,
        sender: "user",
        timestamp: new Date(),
      } as any,
    ]);

    setInput("");
    setLoading(true);

    try {
      const res = await chatApi.sendMessage({
        business_id: Number(id),
        user_name: profile.name,
        user_message: msg,
        conversation_id: conversationId || undefined,
      });

      if (!conversationId && res.conversation_id) {
        setConversationId(res.conversation_id);
      }

      const replyText =
        res.reply ?? "Sorry, I couldn’t generate a response. Please try again.";

      const toolActions: any[] = (res as any).tool_actions || [];

      // --- 7.2: detect booking intent or calendar tool use ---
      const botReplyLower = (replyText || "").toLowerCase();
      const bookingKeywords = [
        "book",
        "appointment",
        "schedule",
        "reserve",
        "slot",
        "meeting",
      ];

      const userAskedBooking = bookingKeywords.some((k) =>
        msg.toLowerCase().includes(k)
      );

      const botMentionedBooking = bookingKeywords.some((k) =>
        botReplyLower.includes(k)
      );

      const botUsedCalendarTool = toolActions.some(
        (a) => a.tool === "calendar" && a.action === "create_event"
      );

      if ((userAskedBooking || botMentionedBooking) && !botUsedCalendarTool) {
        setShowBookingModal(true);
      }

      const assistantMsg: any = {
        id: (Date.now() + 1).toString(),
        text: replyText,
        sender: "assistant",
        timestamp: new Date(),
        tool_actions: toolActions,
      };

      if (botUsedCalendarTool) {
        setMessages((prev) => [
          ...prev,
          assistantMsg,
          {
            id: (Date.now() + 2).toString(),
            text: "Your appointment has been created successfully! 📅✨",
            sender: "assistant",
            timestamp: new Date(),
          } as any,
        ]);
      } else {
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch (error) {
      const detail = getApiErrorMessage(
        error,
        "Failed to send message. Please try again."
      );
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          text: `Error: ${detail}`,
          sender: "assistant",
          timestamp: new Date(),
        } as any,
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!business) {
    return (
      <div className="flex items-center justify-center h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card flex flex-col h-[calc(100vh-200px)] min-h-[600px]">
        {/* Header */}
        <div className="border-b p-4 bg-gray-50 flex justify-between items-center rounded-t-xl">
          <div>
            <h2 className="text-xl font-semibold">Chat with {business.name}</h2>
            <p className="text-sm text-gray-600">
              {readyToChat
                ? `You are chatting as ${profile.name}`
                : "You can start chatting directly."}
            </p>
          </div>

          <button
            onClick={() => setShowBookingModal(true)}
            className="text-sm text-primary-600 hover:text-primary-800"
          >
            📅 Book Appointment
          </button>
        </div>

        {/* Booking Modal */}
        <BookingModal
          open={showBookingModal}
          onClose={() => setShowBookingModal(false)}
          business={business}
          profile={profile}
          onSuccess={(appt: any) => {
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now().toString(),
                sender: "assistant",
                timestamp: new Date(),
                text: `Your appointment is booked for ${appt.date} at ${appt.time} 🎉`,
              } as any,
            ]);
          }}
        />

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.map((m: any) => (
            <div
              key={m.id}
              className={`flex mb-4 ${
                m.sender === "user"
                  ? "flex-row-reverse space-x-reverse"
                  : "space-x-3"
              }`}
            >
              <div
                className={`w-8 h-8 flex justify-center items-center rounded-full ${
                  m.sender === "user"
                    ? "bg-primary-600 text-white"
                    : "bg-gray-200"
                }`}
              >
                {m.sender === "user" ? (
                  <User className="h-5 w-5" />
                ) : (
                  <Bot className="h-5 w-5" />
                )}
              </div>

              <div
                className={`p-3 rounded-lg max-w-[80%] break-words ${
                  m.sender === "user"
                    ? "bg-primary-600 text-white"
                    : "bg-gray-100"
                }`}
              >
                {m.text}

                {m.tool_actions &&
                  m.tool_actions.map((t: any, i: number) => (
                    <div
                      key={i}
                      className="mt-2 text-xs bg-white border px-2 py-1 rounded"
                    >
                      {t.action || t.tool}
                    </div>
                  ))}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex space-x-3">
              <Bot className="h-5 w-5 text-gray-600" />
              <Loader2 className="h-6 w-6 animate-spin text-gray-600" />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSend} className="border-t p-4 bg-gray-50 rounded-b-xl">
          <div className="flex space-x-2">
            <input
              ref={inputRef}
              type="text"
              className="input flex-1"
              placeholder="Type your message..."
              value={input}
              disabled={loading}
              onChange={(e) => setInput(e.target.value)}
            />

            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn btn-primary flex items-center"
            >
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
