import { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Send, Bot, User, Loader2 } from 'lucide-react';
import { chatApi, businessApi } from '../services/api';
import type { Message, Business } from '../types';

export default function Chat() {
  const { id } = useParams<{ id: string }>();
  const [business, setBusiness] = useState<Business | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [userName, setUserName] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (id) {
      loadBusiness();
    }
  }, [id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Focus input on mount
    if (inputRef.current && !userName) {
      inputRef.current.focus();
    }
  }, []);

  const loadBusiness = async () => {
    if (!id) return;
    try {
      const data = await businessApi.get(Number(id));
      setBusiness(data);
    } catch (err) {
      console.error('Failed to load business:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || loading || !id) return;

    // If first message, require user name
    if (!userName.trim()) {
      if (input.trim().length < 2) {
        alert('Please enter your name');
        return;
      }
      setUserName(input.trim());
      setInput('');
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
    console.log('Adding user message:', userMessage);
    setMessages((prev) => {
      const newMessages = [...prev, userMessage];
      console.log('Messages after adding user:', newMessages.length);
      return newMessages;
    });
    setInput('');
    setLoading(true);

    try {
      const response = await chatApi.sendMessage({
        business_id: Number(id),
        user_name: userName,
        user_message: messageText,
        conversation_id: conversationId || undefined,
      });

      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const replyText = response.reply || 'I apologize, but I could not generate a response. Please try again.';
      console.log('Received response:', {
        reply: replyText.substring(0, 100),
        intent: response.intent,
        conversation_id: response.conversation_id
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: replyText,
        sender: 'assistant',
        timestamp: new Date(),
        intent: response.intent,
      };

      console.log('Adding assistant message to state:', assistantMessage);
      setMessages((prev) => {
        const newMessages = [...prev, assistantMessage];
        console.log('Updated messages array:', newMessages.length, 'messages');
        return newMessages;
      });
    } catch (err: any) {
      console.error('Chat error:', err);
      
      // Handle Pydantic validation errors (array of error objects)
      let errorDetail = 'Failed to send message. Please check your connection and try again.';
      
      if (err.response?.data) {
        const errorData = err.response.data;
        
        // If detail is an array (Pydantic validation errors)
        if (Array.isArray(errorData.detail)) {
          const errors = errorData.detail.map((e: any) => {
            const field = e.loc?.join('.') || 'field';
            return `${field}: ${e.msg}`;
          });
          errorDetail = errors.join('; ');
        } 
        // If detail is a string
        else if (typeof errorData.detail === 'string') {
          errorDetail = errorData.detail;
        }
        // If detail is an object, try to stringify it
        else if (errorData.detail && typeof errorData.detail === 'object') {
          errorDetail = JSON.stringify(errorData.detail);
        }
      } else if (err.message) {
        errorDetail = err.message;
      }
      
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
        <div className="border-b border-gray-200 p-4 bg-gray-50 rounded-t-xl">
          <h2 className="text-xl font-semibold">Chat with {business.name}</h2>
          {!userName && (
            <p className="text-sm text-gray-600 mt-1">Please enter your name to start</p>
          )}
        </div>

        {/* Messages */}
        <div 
          className="flex-1 overflow-y-auto p-4" 
          style={{ minHeight: '400px', maxHeight: 'calc(100vh - 300px)' }}
        >
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-12">
              <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>Start a conversation with {business.name}'s AI assistant</p>
              <p className="text-sm mt-2">Ask about services, hours, or upload documents for Q&A</p>
            </div>
          )}

          {messages.map((message) => {
            console.log('Rendering message:', message.id, message.sender, message.text?.substring(0, 50));
            return (
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
                  overflowWrap: 'break-word'
                }}
              >
                <p className="whitespace-pre-wrap break-words">{message.text || '(Empty message)'}</p>
                {message.intent && message.sender === 'assistant' && (
                  <span className={`text-xs mt-2 block ${
                    message.sender === 'user' ? 'text-primary-100' : 'text-gray-500'
                  }`}>
                    Intent: {message.intent}
                  </span>
                )}
              </div>
            </div>
            );
          })}

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
              placeholder={!userName ? "Enter your name..." : "Type your message..."}
              className="input flex-1"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
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

