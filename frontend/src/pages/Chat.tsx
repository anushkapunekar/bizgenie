import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Send, Bot, User, Loader2, Edit3 } from 'lucide-react';
import { chatApi, businessApi } from '../services/api';
import type { Message, Business, ChatProfile } from '../types';
import { getApiErrorMessage } from '../utils/errors';

const CHAT_PROFILE_STORAGE_KEY = 'bizgenie.chatProfile';

const getStoredProfile = (): ChatProfile => {
  try {
    const raw = localStorage.getItem(CHAT_PROFILE_STORAGE_KEY);
    if (!raw) {
      return { name: '' };
    }
    const parsed = JSON.parse(raw);
    return {
      name: parsed.name || '',
      email: parsed.email || '',
    };
  } catch {
    return { name: '' };
  }
};

const persistProfile = (profile: ChatProfile) => {
  localStorage.setItem(CHAT_PROFILE_STORAGE_KEY, JSON.stringify(profile));
};

const getChatSessionKey = (businessId?: string) => (businessId ? `bizgenie.chat.session.${businessId}` : null);

interface StoredMessage {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  intent?: string;
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
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const initialProfile = useMemo(() => getStoredProfile(), []);
  const [profile, setProfile] = useState<ChatProfile>(initialProfile);
  const [profileDraft, setProfileDraft] = useState<{ name: string; email: string }>(() => ({
    name: initialProfile.name,
    email: initialProfile.email ?? '',
  }));
  const [profileEditorOpen, setProfileEditorOpen] = useState(() => !initialProfile.name);
  const [profileError, setProfileError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const sessionHydratedRef = useRef(false);
  const chatSessionKey = useMemo(() => getChatSessionKey(id), [id]);

  const readyToChat = Boolean(profile.name);

  const businessId = id ? Number(id) : null;

  const loadBusiness = useCallback(async () => {
    if (!businessId) return;
    try {
      const data = await businessApi.get(businessId);
      setBusiness(data);
    } catch (error) {
      console.error('Failed to load business:', error);
    }
  }, [businessId]);

  useEffect(() => {
    loadBusiness();
  }, [loadBusiness]);

  useEffect(() => {
    persistProfile(profile);
  }, [profile]);

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
            parsed.messages.map((msg) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
            }))
          );
        }
        if (parsed.conversationId) {
          setConversationId(parsed.conversationId);
        }
        if (parsed.profile) {
          setProfile(parsed.profile);
          setProfileDraft({
            name: parsed.profile.name,
            email: parsed.profile.email ?? '',
          });
          setProfileEditorOpen(!parsed.profile.name);
        }
      } catch (error) {
        console.error('Failed to hydrate chat session', error);
      }
    }
    sessionHydratedRef.current = true;
  }, [chatSessionKey]);

  useEffect(() => {
    if (!chatSessionKey) return;
    const payload: StoredChatSession = {
      conversationId,
      profile,
      messages: messages.map((msg) => ({
        ...msg,
        timestamp: msg.timestamp.toISOString(),
      })),
    };
    sessionStorage.setItem(chatSessionKey, JSON.stringify(payload));
  }, [messages, conversationId, profile, chatSessionKey]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Focus input on mount
    if (inputRef.current && readyToChat) {
      inputRef.current.focus();
    }
  }, [readyToChat]);

  useEffect(() => {
    if (!business || !readyToChat || !sessionHydratedRef.current) return;
    if (messages.length > 0) return;

    const hours = business.working_hours;
    const highlightDay = Object.entries(hours).find(([, value]) => value?.open && value?.close);
    let hoursText = '';
    if (highlightDay) {
      const [day, value] = highlightDay;
      hoursText = `${day.charAt(0).toUpperCase() + day.slice(1)}: ${value?.open} - ${value?.close}`;
    }

    const greeting: Message = {
      id: `welcome-${Date.now()}`,
      text: `Hi ${profile.name}! I'm ${business.name}'s virtual assistant. Ask me about services, pricing, or availability.${hoursText ? ` We're typically open ${hoursText}.` : ''}`,
      sender: 'assistant',
      timestamp: new Date(),
    };
    setMessages([greeting]);
  }, [business, readyToChat, messages.length, profile.name]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleProfileSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!profileDraft.name.trim()) {
      setProfileError('Please enter your name to start chatting.');
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
      email: normalized.email ?? '',
    });
    setProfileError(null);
    setProfileEditorOpen(false);
  };

  const handleProfileCancel = () => {
    if (!readyToChat) return;
    setProfileDraft({
      name: profile.name,
      email: profile.email ?? '',
    });
    setProfileError(null);
    setProfileEditorOpen(false);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || loading || !id) return;

    if (!readyToChat) {
      setProfileEditorOpen(true);
      setProfileError('Add your name to begin chatting.');
      return;
    }

    // Save the message text before clearing input
    const messageText = input.trim();
    
    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    };

    // Add user message immediately
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await chatApi.sendMessage({
        business_id: Number(id),
        user_name: profile.name,
        user_message: messageText,
        conversation_id: conversationId || undefined,
      });

      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const replyText = response.reply || 'I apologize, but I could not generate a response. Please try again.';

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: replyText,
        sender: 'assistant',
        timestamp: new Date(),
        intent: response.intent,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: unknown) {
      console.error('Chat error:', error);
      const errorDetail = getApiErrorMessage(
        error,
        'Failed to send message. Please check your connection and try again.'
      );
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Error: ${errorDetail}`,
        sender: 'assistant',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  if (!business) {
    return (
      <div className="flex justify-center items-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card p-0 flex flex-col h-[calc(100vh-200px)] min-h-[600px]">
        {/* Chat Header */}
        <div className="border-b border-gray-200 p-4 bg-gray-50 rounded-t-xl flex flex-col md:flex-row md:items-center md:justify-between space-y-2 md:space-y-0">
          <div>
            <h2 className="text-xl font-semibold">Chat with {business.name}</h2>
            <p className="text-sm text-gray-600 mt-1">
              {readyToChat
                ? `You are chatting as ${profile.name}${profile.email ? ` · ${profile.email}` : ''}`
                : 'Add your name so we can personalize the experience.'}
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setProfileDraft({
                name: profile.name,
                email: profile.email ?? '',
              });
              setProfileEditorOpen(true);
              setProfileError(null);
            }}
            className="text-sm text-primary-600 flex items-center space-x-1 hover:text-primary-800"
          >
            <Edit3 className="h-4 w-4" />
            <span>{readyToChat ? 'Edit profile' : 'Add profile'}</span>
          </button>
        </div>

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

        {/* Messages */}
        <div 
          className="flex-1 overflow-y-auto p-4" 
          style={{ minHeight: '400px', maxHeight: 'calc(100vh - 300px)' }}
        >
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-12">
              <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              {readyToChat ? (
                <>
                  <p>Start a conversation with {business.name}'s AI assistant</p>
                  <p className="text-sm mt-2">Ask about services, hours, or upload documents for Q&A</p>
                </>
              ) : (
                <p className="text-sm">Add your name above to begin chatting.</p>
              )}
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start space-x-3 mb-4 ${
                message.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}
              style={{ minHeight: '40px' }}
            >
              <div
                className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.sender === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                {message.sender === 'user' ? (
                  <User className="h-5 w-5" />
                ) : (
                  <Bot className="h-5 w-5" />
                )}
              </div>
              <div
                className={`flex-1 rounded-lg p-3 max-w-[80%] ${
                  message.sender === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-900 border border-gray-200'
                }`}
                style={{
                  wordWrap: 'break-word',
                  overflowWrap: 'break-word',
                }}
              >
                <p className="whitespace-pre-wrap break-words">{message.text || '(Empty message)'}</p>
                {message.intent && message.sender === 'assistant' && (
                  <span
                    className={`text-xs mt-2 block ${
                      message.sender === 'user' ? 'text-primary-100' : 'text-gray-500'
                    }`}
                  >
                    Intent: {message.intent}
                  </span>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                <Bot className="h-5 w-5 text-gray-700" />
              </div>
              <div className="bg-gray-100 rounded-lg p-3">
                <Loader2 className="h-5 w-5 animate-spin text-gray-600" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSend} className="border-t border-gray-200 p-4 bg-gray-50 rounded-b-xl">
          <div className="flex items-center space-x-2">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={readyToChat ? "Type your message..." : "Add your name above to start chatting"}
              className="input flex-1"
              disabled={loading || !readyToChat}
            />
            <button
              type="submit"
              disabled={loading || !input.trim() || !readyToChat}
              className="btn btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
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

