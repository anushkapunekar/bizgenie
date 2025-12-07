import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Send, Bot, User, Loader2, Edit3 } from "lucide-react";

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
  intent?: string | null;
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

  const [profileDraft, setProfileDraft] = useState({
    name: initialProfile.name,
    email: initialProfile.email ?? "",
  });

  const [profileEditorOpen, setProfileEditorOpen] = useState(
    () => !initialProfile.name
  );
  const [profileError, setProfileError] = useState<string | null>(null);

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
            }))
          );
        }

        if (parsed.conversationId) setConversationId(parsed.conversationId);

        if (parsed.profile) {
          setProfile(parsed.profile);
          setProfileDraft({
            name: parsed.profile.name,
            email: parsed.profile.email ?? "",
          });
        }
      } catch (err) {
        console.error("Hydration error:", err);
      }
    }

    sessionHydratedRef.current = true;
  }, [chatSessionKey]);

  useEffect(() => {
    if (!chatSessionKey) return;

    const payload: StoredChatSession = {
      conversationId,
      profile,
      messages: messages.map((m) => ({
        ...m,
        timestamp: m.timestamp.toISOString(),
        tool_actions: (m as any).tool_actions,
      })),
    };

    sessionStorage.setItem(chatSessionKey, JSON.stringify(payload));
  }, [messages, conversationId, profile, chatSessionKey]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Welcome message
  useEffect(() => {
    if (!business || !readyToChat || !sessionHydratedRef.current) return;
    if (messages.length > 0) return;

    const hours = business.working_hours;
    const day = Object.entries(hours).find(
      ([, v]) => v?.open && v?.close
    );

    let hoursText = "";
    if (day) {
      const [d, v] = day;
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
      },
    ]);
  }, [business, readyToChat, messages.length, profile.name]);

  const handleProfileSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!profileDraft.name.trim()) {
      setProfileError("Please enter your name to start chatting.");
      return;
    }

    const normalized: ChatProfile = {
      name: profileDraft.name.trim(),
    };
    if (profileDraft.email.trim()) {
      normalized.email = profileDraft.email.trim();
    }

    setProfile(normalized);
    setProfileDraft({
      name: normalized.name,
      email: normalized.email ?? "",
    });
    setProfileError(null);
    setProfileEditorOpen(false);
  };

  const handleProfileCancel = () => {
    if (!readyToChat) return;
    setProfileDraft({
      name: profile.name,
      email: profile.email ?? "",
    });
    setProfileError(null);
    setProfileEditorOpen(false);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || !id) return;

    if (!readyToChat) {
      setProfileEditorOpen(true);
      setProfileError("Add your name to begin chatting.");
      return;
    }

    const msgText = input.trim();

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        text: msgText,
        sender: "user",
        timestamp: new Date(),
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const res = await chatApi.sendMessage({
        business_id: Number(id),
        user_name: profile.name,
        user_message: msgText,
        conversation_id: conversationId || undefined,
      });

      if (!conversationId && res.conversation_id) {
        setConversationId(res.conversation_id);
      }

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          text: res.reply || "Error generating reply.",
          sender: "assistant",
          timestamp: new Date(),
          tool_actions: res.tool_actions,
        },
      ]);
    } catch (err) {
      const detail = getApiErrorMessage(
        err,
        "Failed to send message. Please try again."
      );
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          text: `Error: ${detail}`,
          sender: "assistant",
          timestamp: new Date(),
        },
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
    <div className="w-full flex justify-center px-2 md:px-4 lg:px-6">
      <div className="w-full max-w-3xl bg-white rounded-xl shadow-md flex flex-col h-[calc(100vh-180px)]">

        {/* Header */}
        <div className="border-b p-4 bg-gray-50 flex flex-col md:flex-row md:items-center md:justify-between space-y-2 md:space-y-0">
          <div>
            <h2 className="text-xl font-semibold">Chat with {business.name}</h2>
            <p className="text-sm text-gray-600 mt-1">
              {readyToChat
                ? `You are chatting as ${profile.name}${
                    profile.email ? ` · ${profile.email}` : ""
                  }`
                : "Add your name so we can personalize the experience."}
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => {
                setProfileDraft({
                  name: profile.name,
                  email: profile.email ?? "",
                });
                setProfileEditorOpen(true);
                setProfileError(null);
              }}
              className="text-sm text-primary-600 flex items-center space-x-1 hover:text-primary-800"
            >
              <Edit3 className="h-4 w-4" />
              <span>{readyToChat ? "Edit profile" : "Add profile"}</span>
            </button>

            <button
              type="button"
              onClick={() => setShowBookingModal(true)}
              className="text-sm text-primary-600 flex items-center hover:text-primary-800"
            >
              📅 Book Appointment
            </button>
          </div>
        </div>

        {/* Profile editor */}
        {profileEditorOpen && (
          <div className="border-b border-gray-200 bg-white">
            <form onSubmit={handleProfileSubmit} className="p-4 space-y-4">
              {profileError && (
                <div className="text-sm text-red-600 bg-red-50 border border-red-200 px-3 py-2 rounded-lg">
                  {profileError}
                </div>
              )}

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Your name *
                  </label>
                  <input
                    type="text"
                    className="input"
                    value={profileDraft.name}
                    onChange={(e) =>
                      setProfileDraft((prev) => ({
                        ...prev,
                        name: e.target.value,
                      }))
                    }
                    placeholder="Jane Doe"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email (optional)
                  </label>
                  <input
                    type="email"
                    className="input"
                    value={profileDraft.email}
                    onChange={(e) =>
                      setProfileDraft((prev) => ({
                        ...prev,
                        email: e.target.value,
                      }))
                    }
                    placeholder="jane@example.com"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-2">
                {readyToChat && (
                  <button
                    type="button"
                    onClick={handleProfileCancel}
                    className="btn btn-secondary"
                  >
                    Cancel
                  </button>
                )}
                <button type="submit" className="btn btn-primary">
                  Save profile
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Booking Modal */}
        <BookingModal
          open={showBookingModal}
          onClose={() => setShowBookingModal(false)}
          business={business}
          profile={profile}
          onSuccess={(appt) => {
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now().toString(),
                sender: "assistant",
                timestamp: new Date(),
                text: `Your appointment is booked for ${
                  appt.appointment_date.split("T")[0]
                } at ${appt.appointment_date.substring(11, 16)} 🎉`,
              },
            ]);
          }}
        />

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-3 py-4 md:px-6 space-y-4">
          {messages.map((m) => (
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
                    : "bg-gray-200 text-gray-700"
                }`}
              >
                {m.sender === "user" ? (
                  <User className="h-5 w-5" />
                ) : (
                  <Bot className="h-5 w-5" />
                )}
              </div>

              <div
                className={`px-4 py-2 rounded-lg max-w-[85%] md:max-w-[75%] break-words ${
                  m.sender === "user"
                    ? "bg-primary-600 text-white self-end"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                {m.text}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                <Bot className="h-4 w-4 text-gray-600" />
              </div>
              <Loader2 className="animate-spin h-6 w-6 text-gray-600" />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSend} className="border-t px-3 py-4 bg-gray-50 flex items-center space-x-2 md:px-6">
          <div className="flex space-x-2">
            <input
              ref={inputRef}
              type="text"
              className="input flex-1"
              placeholder={
                readyToChat
                  ? "Type your message..."
                  : "Add your name above to start chatting"
              }
              value={input}
              disabled={!readyToChat || loading}
              onChange={(e) => setInput(e.target.value)}
            />

            <button
              type="submit"
              disabled={!readyToChat || loading || !input.trim()}
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
