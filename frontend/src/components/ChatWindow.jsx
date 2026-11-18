import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage } from './ChatMessage';
import { chatService } from '../services/chatService';
import { useAuth } from '../context/AuthContext';
import {
  Send,
  Sparkles,
  Trash2,
  Ticket,
  Star,
  CheckCircle,
  AlertCircle,
  Clock,
  ShieldCheck,
  Check,
  X,
} from 'lucide-react';

const INITIAL_MESSAGE = {
  role: 'assistant',
  content: `👋 **Welcome to QuickFixer AI IT Support Assistant!**

Describe your technical issue, error message, or inquiry (e.g., *VPN disconnection, MFA reset, sudden laptop shutdown, or print queue jam*).

I analyze company runbooks and diagnose issues in real time.`,
  sources: [],
  used_gemini: false,
  query_type: 'general_inquiry',
  approval_status: null,
};

export const ChatWindow = ({ initialPrompt = '' }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [input, setInput] = useState(initialPrompt);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => `sess_${Date.now()}`);
  const [rating, setRating] = useState(0);
  const [ratingSubmitted, setRatingSubmitted] = useState(false);
  const [escalateSuccess, setEscalateSuccess] = useState(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    if (initialPrompt) {
      setInput(initialPrompt);
      textareaRef.current?.focus();
    }
  }, [initialPrompt]);

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || isLoading) return;

    const userMsg = { role: 'user', content: query.trim() };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      // Send conversation history without sources metadata
      const cleanHistory = updatedMessages.map(m => ({ role: m.role, content: m.content }));
      const response = await chatService.sendMessage(query.trim(), cleanHistory, sessionId);

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
          sources: response.sources || [],
          used_gemini: response.used_gemini,
          query_type: response.query_type,
          approval_status: response.approval_status,
          ticket_id: response.ticket_id,
        },
      ]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: '⚠️ Unable to reach the QuickFixer AI service desk backend. Please ensure the backend server is running and try again.',
          sources: [],
          used_gemini: false,
          query_type: 'error',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearHistory = () => {
    setMessages([INITIAL_MESSAGE]);
    setSessionId(`sess_${Date.now()}`);
    setEscalateSuccess(null);
    setRating(0);
    setRatingSubmitted(false);
    setShowClearConfirm(false);
  };

  const handleDirectEscalate = async () => {
    if (messages.length < 2) return;
    setIsLoading(true);
    try {
      const cleanHistory = messages.map(m => ({ role: m.role, content: m.content }));
      const ticket = await chatService.escalateToTicket(cleanHistory);
      setEscalateSuccess(ticket);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `🎫 **Incident Ticket Created:** \`${ticket.id}\` — **${ticket.title}**
- **Priority:** \`${ticket.priority}\`
- **Assigned Team:** \`${ticket.assigned_to}\`
- **AI Diagnosis:** ${ticket.ai_diagnosis}

Our support team has been notified. You can track this ticket anytime under **My Tickets**.`,
          sources: [],
          used_gemini: false,
          query_type: 'ticket_creation',
        },
      ]);
    } catch (err) {
      console.error('Escalation error:', err);
      alert('Failed to escalate ticket. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (stars) => {
    setRating(stars);
    try {
      await chatService.submitFeedback(stars, 'User CSAT rating from chat', sessionId);
      setRatingSubmitted(true);
      setTimeout(() => setRatingSubmitted(false), 3000);
    } catch (err) {
      console.warn('Feedback submit error:', err);
    }
  };

  // Quick Runbook shortcuts
  const quickRunbooks = [
    { label: '🌐 Cisco AnyConnect VPN Drops', prompt: 'My Cisco AnyConnect VPN fails to connect and times out at 85%.' },
    { label: '🔑 MFA Push Issue', prompt: 'I got a new phone and my Microsoft Authenticator MFA push notifications are not arriving.' },
    { label: '💻 Sudden System Freeze & Shutdown', prompt: 'My laptop suddenly froze and shut down unexpectedly while I was working.' },
    { label: '✉️ Outlook Crashes on Shared Mailbox', prompt: 'Outlook crashes with an access violation error when I open a shared department mailbox.' },
  ];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 120px)',
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-lg)',
      overflow: 'hidden',
    }}>
      {/* Chat Sub-Header */}
      <div style={{
        padding: '0.85rem 1.25rem',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: 'rgba(15, 23, 42, 0.4)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Sparkles size={18} color="var(--accent-primary)" />
          <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
            QuickFixer Conversational AI
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            ({sessionId})
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {showClearConfirm ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--color-warning)' }}>Clear history?</span>
              <button onClick={handleClearHistory} className="btn btn-danger" style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem' }}>
                <Check size={12} /> Yes
              </button>
              <button onClick={() => setShowClearConfirm(false)} className="btn btn-ghost" style={{ padding: '0.25rem 0.5rem', fontSize: '0.72rem' }}>
                <X size={12} /> No
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowClearConfirm(true)}
              className="btn btn-ghost"
              style={{ padding: '0.35rem 0.65rem', fontSize: '0.78rem' }}
              title="Clear active conversation"
            >
              <Trash2 size={14} />
              <span>Clear Chat</span>
            </button>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Quick prompt pills at the top */}
        {messages.length === 1 && (
          <div style={{ marginBottom: '1.25rem' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600, marginBottom: '0.5rem' }}>
              ⚡ Quick Runbook Shortcuts:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {quickRunbooks.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(item.prompt)}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.76rem', padding: '0.35rem 0.75rem' }}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message items */}
        {messages.map((m, idx) => (
          <ChatMessage
            key={idx}
            msg={m}
            onRetry={m.role === 'assistant' && idx > 0 ? () => handleSend(messages[idx - 1]?.content) : null}
          />
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.85rem 1rem',
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-lg)',
            width: 'fit-content',
            marginBottom: '1rem',
          }}>
            <div className="animate-spin" style={{
              width: '16px',
              height: '16px',
              border: '2px solid var(--border-strong)',
              borderTopColor: 'var(--accent-primary)',
              borderRadius: '50%'
            }}></div>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
              QuickFixer AI analyzing runbooks and evaluating diagnostics...
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Actions Drawer (Escalate & CSAT Feedback) */}
      {messages.length > 2 && (
        <div style={{
          padding: '0.65rem 1.25rem',
          backgroundColor: 'rgba(15, 23, 42, 0.7)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              onClick={handleDirectEscalate}
              disabled={isLoading}
              className="btn btn-secondary"
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
            >
              <Ticket size={14} color="var(--color-warning)" />
              <span>Escalate to Support Ticket</span>
            </button>
            {escalateSuccess && (
              <span style={{ fontSize: '0.75rem', color: 'var(--color-success)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <CheckCircle size={14} /> Created {escalateSuccess.id}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Rate resolution:
            </span>
            <div style={{ display: 'flex', gap: '0.2rem' }}>
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => handleFeedback(star)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    padding: '2px',
                    color: star <= rating ? '#F59E0B' : 'var(--text-muted)',
                  }}
                  title={`Rate ${star}/5 stars`}
                >
                  <Star size={16} fill={star <= rating ? '#F59E0B' : 'none'} />
                </button>
              ))}
            </div>
            {ratingSubmitted && (
              <span style={{ fontSize: '0.72rem', color: 'var(--color-success)' }}>
                Thank you!
              </span>
            )}
          </div>
        </div>
      )}

      {/* Input Form Bar */}
      <div style={{
        padding: '0.85rem 1.25rem',
        borderTop: '1px solid var(--border-subtle)',
        backgroundColor: 'var(--bg-secondary)',
      }}>
        <div style={{
          display: 'flex',
          gap: '0.65rem',
          alignItems: 'flex-end',
        }}>
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your IT issue. For example: My company laptop suddenly shut down..."
            className="textarea"
            style={{
              minHeight: '44px',
              maxHeight: '120px',
              resize: 'none',
              padding: '0.65rem 0.85rem',
              fontSize: '0.9rem',
            }}
          />

          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="btn btn-primary"
            style={{
              height: '44px',
              padding: '0 1.25rem',
              borderRadius: 'var(--radius-md)',
              flexShrink: 0,
            }}
          >
            <Send size={16} />
            <span>Send</span>
          </button>
        </div>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: '0.35rem',
          fontSize: '0.7rem',
          color: 'var(--text-muted)',
        }}>
          <span>Press <strong>Enter</strong> to send, <strong>Shift + Enter</strong> for new line</span>
          <span>Security Notice: Never submit corporate plaintext passwords</span>
        </div>
      </div>
    </div>
  );
};
