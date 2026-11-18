import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Copy, Check, ChevronDown, ChevronRight, BookOpen, AlertTriangle, Cpu, RotateCcw } from 'lucide-react';

export const ChatMessage = ({ msg, onRetry }) => {
  const isUser = msg.role === 'user';
  const [copied, setCopied] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isOutOfScope = msg.query_type === 'out_of_scope';

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '1.25rem',
      maxWidth: '100%',
    }}>
      <div style={{
        display: 'flex',
        gap: '0.75rem',
        maxWidth: isUser ? '85%' : '90%',
        flexDirection: isUser ? 'row-reverse' : 'row',
      }}>
        {/* Avatar */}
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          backgroundColor: isUser ? 'var(--accent-primary)' : isOutOfScope ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.2)',
          border: `1px solid ${isUser ? 'transparent' : isOutOfScope ? 'var(--color-danger)' : 'var(--accent-primary)'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#FFFFFF',
          flexShrink: 0,
        }}>
          {isUser ? <User size={16} /> : isOutOfScope ? <AlertTriangle size={16} color="var(--color-danger)" /> : <Bot size={16} color="#60A5FA" />}
        </div>

        {/* Bubble */}
        <div style={{
          backgroundColor: isUser ? 'var(--accent-primary)' : 'var(--bg-card)',
          border: `1px solid ${isUser ? 'transparent' : isOutOfScope ? 'rgba(239, 68, 68, 0.3)' : 'var(--border-subtle)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '1rem 1.25rem',
          color: isUser ? '#FFFFFF' : 'var(--text-primary)',
          boxShadow: 'var(--shadow-sm)',
        }}>
          {/* Header info for assistant */}
          {!isUser && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '0.5rem',
              paddingBottom: '0.4rem',
              borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
              fontSize: '0.75rem',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{ fontWeight: 700, color: '#60A5FA' }}>QuickFixer AI</span>
                {isOutOfScope && (
                  <span style={{
                    fontSize: '0.68rem',
                    padding: '0.1rem 0.4rem',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    color: '#F87171',
                    fontWeight: 600,
                  }}>
                    Guardrail Triggered
                  </span>
                )}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <button
                  onClick={handleCopy}
                  title="Copy response"
                  className="btn-ghost"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--text-muted)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.2rem',
                    fontSize: '0.72rem',
                    padding: '2px 4px',
                  }}
                >
                  {copied ? <Check size={13} color="var(--color-success)" /> : <Copy size={13} />}
                  <span>{copied ? 'Copied' : 'Copy'}</span>
                </button>

                {onRetry && (
                  <button
                    onClick={onRetry}
                    title="Retry query"
                    className="btn-ghost"
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.2rem',
                      fontSize: '0.72rem',
                      padding: '2px 4px',
                    }}
                  >
                    <RotateCcw size={13} />
                    <span>Retry</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Markdown content */}
          <div className="prose">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {msg.content}
            </ReactMarkdown>
          </div>

          {/* Verified Runbook Citations Accordion */}
          {!isUser && msg.sources && msg.sources.length > 0 && (
            <div style={{
              marginTop: '0.85rem',
              paddingTop: '0.65rem',
              borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            }}>
              <button
                onClick={() => setSourcesOpen(!sourcesOpen)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--accent-primary)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: '2px 0',
                }}
              >
                <BookOpen size={14} />
                <span>Verified Runbook Citations ({msg.sources.length} sources)</span>
                {sourcesOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>

              {sourcesOpen && (
                <div style={{
                  marginTop: '0.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.45rem',
                }}>
                  {msg.sources.map((src, i) => (
                    <div key={i} style={{
                      padding: '0.55rem 0.75rem',
                      backgroundColor: 'rgba(11, 16, 32, 0.6)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.78rem',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                          📄 {src.title || src.source}
                        </span>
                        <span style={{
                          fontSize: '0.7rem',
                          color: '#4ADE80',
                          fontWeight: 700,
                          backgroundColor: 'rgba(22, 163, 74, 0.15)',
                          padding: '1px 6px',
                          borderRadius: 'var(--radius-full)'
                        }}>
                          {Math.round((src.score || 0) * 100)}% match
                        </span>
                      </div>
                      <p style={{
                        fontSize: '0.74rem',
                        color: 'var(--text-secondary)',
                        fontStyle: 'italic',
                        lineHeight: 1.4,
                      }}>
                        "{src.snippet}"
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Engine & Intent Footer for assistant messages */}
          {!isUser && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              marginTop: '0.65rem',
              paddingTop: '0.45rem',
              borderTop: '1px dashed rgba(255, 255, 255, 0.05)',
              fontSize: '0.7rem',
              color: 'var(--text-muted)',
            }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Cpu size={12} />
                {msg.used_gemini ? '⚡ Google Gemini LLM' : '🛡️ Internal RAG Diagnostic Engine'}
              </span>
              <span>•</span>
              <span style={{ textTransform: 'capitalize' }}>
                Intent: {msg.query_type?.replace(/_/g, ' ') || 'Troubleshooting'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
