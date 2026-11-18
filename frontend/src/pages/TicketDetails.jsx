import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ticketService } from '../services/ticketService';
import { StatusBadge, PriorityBadge } from '../components/StatusBadge';
import {
  ArrowLeft,
  User,
  Clock,
  Laptop,
  Sparkles,
  Send,
  CheckCircle,
  FileText,
  AlertCircle,
  Wrench,
  Bot,
  MessageSquare,
} from 'lucide-react';

export const TicketDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, isAdmin, isTechnician } = useAuth();

  const [ticket, setTicket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [replyMessage, setReplyMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const [updateSuccess, setUpdateSuccess] = useState('');

  // Status and resolution state for technicians/admins
  const [newStatus, setNewStatus] = useState('');
  const [newPriority, setNewPriority] = useState('');
  const [newAssignee, setNewAssignee] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);

  useEffect(() => {
    loadTicket();
  }, [id]);

  const loadTicket = async () => {
    setIsLoading(true);
    setError('');
    try {
      const [ticketData, messageData] = await Promise.all([
        ticketService.getTicket(id),
        ticketService.getMessages(id),
      ]);
      setTicket(ticketData);
      setMessages(messageData);
      setNewStatus(ticketData.status);
      setNewPriority(ticketData.priority);
      setNewAssignee(ticketData.assigned_to || '');
      setResolutionNotes(ticketData.resolution_notes || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load ticket.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePostReply = async (e) => {
    e.preventDefault();
    if (!replyMessage.trim() || isSending) return;

    setIsSending(true);
    try {
      const newMsg = await ticketService.addMessage(id, replyMessage.trim());
      setMessages(prev => [...prev, newMsg]);
      setReplyMessage('');
    } catch (err) {
      alert('Failed to post reply: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsSending(false);
    }
  };

  const handleUpdateTicket = async (e) => {
    e.preventDefault();
    try {
      const updated = await ticketService.updateStatus(id, {
        status: newStatus,
        priority: newPriority,
        assigned_to: newAssignee,
        resolution_notes: resolutionNotes,
      });
      setTicket(updated);
      setUpdateSuccess('Ticket attributes successfully updated!');
      setTimeout(() => setUpdateSuccess(''), 3000);
    } catch (err) {
      alert('Update failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDraftAISummary = async () => {
    setIsGeneratingSummary(true);
    try {
      const res = await ticketService.generateResolutionSummary(id);
      if (res.resolution_summary) {
        setResolutionNotes(res.resolution_summary);
      }
    } catch (err) {
      alert('Failed to generate AI summary.');
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  if (isLoading) {
    return (
      <div className="page-body" style={{ textAlign: 'center', padding: '4rem' }}>
        <div className="animate-spin" style={{
          width: '32px',
          height: '32px',
          border: '3px solid var(--border-strong)',
          borderTopColor: 'var(--accent-primary)',
          borderRadius: '50%',
          margin: '0 auto 1rem',
        }}></div>
        <p>Loading ticket details...</p>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="page-body">
        <button onClick={() => navigate(-1)} className="btn btn-ghost" style={{ marginBottom: '1rem' }}>
          <ArrowLeft size={16} /> Back
        </button>
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem' }}>
          <AlertCircle size={40} color="var(--color-danger)" style={{ margin: '0 auto 1rem' }} />
          <h2>Ticket Not Found or Access Denied</h2>
          <p style={{ marginTop: '0.5rem', color: 'var(--text-secondary)' }}>{error}</p>
        </div>
      </div>
    );
  }

  const canEditStatus = isAdmin || isTechnician;

  return (
    <div className="page-body">
      {/* Top Navigation */}
      <button
        onClick={() => navigate(-1)}
        className="btn btn-ghost"
        style={{ marginBottom: '1.25rem', padding: '0.35rem 0.65rem' }}
      >
        <ArrowLeft size={16} />
        <span>Back to Tickets</span>
      </button>

      {/* Ticket Header Card */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.4rem' }}>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '1.15rem',
                fontWeight: 800,
                color: 'var(--accent-primary)'
              }}>
                {ticket.id}
              </span>
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
            </div>
            <h1 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-primary)' }}>
              {ticket.title}
            </h1>
          </div>

          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', textAlign: 'right' }}>
            <div>Created: <strong>{ticket.created_at?.substring(0, 16).replace('T', ' ')}</strong></div>
            <div>Updated: <strong>{ticket.updated_at?.substring(0, 16).replace('T', ' ')}</strong></div>
            {ticket.resolved_at && (
              <div style={{ color: 'var(--color-success)' }}>
                Resolved: <strong>{ticket.resolved_at.substring(0, 16).replace('T', ' ')}</strong>
              </div>
            )}
          </div>
        </div>

        {/* Quick Meta Row */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem',
          marginTop: '1.25rem',
          paddingTop: '1rem',
          borderTop: '1px solid var(--border-subtle)',
          fontSize: '0.82rem',
        }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Requester: </span>
            <strong style={{ color: 'var(--text-primary)' }}>{ticket.user_name}</strong>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{ticket.user_email}</div>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Category: </span>
            <strong style={{ color: 'var(--text-primary)' }}>{ticket.category}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Assigned Queue / Tech: </span>
            <strong style={{ color: 'var(--text-primary)' }}>{ticket.assigned_to || 'Unassigned'}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Device Environment: </span>
            <span style={{ color: 'var(--text-primary)' }}>{ticket.device_info || 'Not specified'}</span>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Details & Chat vs Status & Controls */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: canEditStatus ? 'minmax(320px, 3fr) minmax(280px, 2fr)' : '1fr',
        gap: '1.5rem',
        alignItems: 'start',
      }}>
        {/* Left Column: Problem Details & Thread */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Original Incident Description */}
          <div className="card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={16} color="var(--accent-primary)" />
              <span>Original Incident Description</span>
            </h3>
            <div style={{
              backgroundColor: 'rgba(11, 16, 32, 0.6)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '1rem',
              color: 'var(--text-primary)',
              fontSize: '0.88rem',
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap',
            }}>
              {ticket.description}
            </div>
          </div>

          {/* AI Diagnostic Assessment */}
          {ticket.ai_diagnosis && (
            <div className="card" style={{
              backgroundColor: 'rgba(59, 130, 246, 0.08)',
              borderColor: 'rgba(59, 130, 246, 0.25)',
            }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.5rem', color: '#60A5FA', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sparkles size={16} />
                <span>AI Diagnostic Assessment</span>
              </h3>
              <p style={{ color: 'var(--text-primary)', fontSize: '0.86rem', lineHeight: 1.5 }}>
                {ticket.ai_diagnosis}
              </p>
              {ticket.suggested_steps && (
                <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px dashed rgba(59, 130, 246, 0.2)' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#93C5FD', marginBottom: '0.35rem' }}>
                    Recommended Runbook Steps:
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                    {ticket.suggested_steps}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Resolution Summary (if present) */}
          {ticket.resolution_notes && (
            <div className="card" style={{
              backgroundColor: 'var(--color-success-bg)',
              borderColor: 'var(--color-success-border)',
            }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.4rem', color: '#4ADE80', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={16} />
                <span>Resolution Summary</span>
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                {ticket.resolution_notes}
              </p>
            </div>
          )}

          {/* Audit / Conversation Thread */}
          <div className="card">
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <MessageSquare size={16} color="var(--accent-primary)" />
              <span>Communication & Audit Thread ({messages.length} notes)</span>
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginBottom: '1.25rem' }}>
              {messages.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '1.5rem', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
                  No messages on this ticket yet.
                </div>
              ) : (
                messages.map((m, idx) => {
                  const isTech = m.sender === 'technician' || m.sender === 'admin';
                  return (
                    <div key={idx} style={{
                      padding: '0.85rem 1rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isTech ? 'rgba(59, 130, 246, 0.08)' : 'rgba(15, 23, 42, 0.6)',
                      border: `1px solid ${isTech ? 'rgba(59, 130, 246, 0.25)' : 'var(--border-subtle)'}`,
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem', fontSize: '0.74rem' }}>
                        <span style={{ fontWeight: 700, color: isTech ? '#60A5FA' : 'var(--text-primary)' }}>
                          {isTech ? '🛠️ Technician Note' : '👤 Requester'} ({m.sender})
                        </span>
                        <span style={{ color: 'var(--text-muted)' }}>
                          {m.timestamp?.substring(0, 16).replace('T', ' ')}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                        {m.message}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Add reply input form */}
            <form onSubmit={handlePostReply}>
              <textarea
                rows={3}
                value={replyMessage}
                onChange={(e) => setReplyMessage(e.target.value)}
                placeholder="Add technician note or response to employee..."
                className="textarea"
                style={{ marginBottom: '0.75rem' }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  type="submit"
                  disabled={!replyMessage.trim() || isSending}
                  className="btn btn-primary"
                  style={{ fontSize: '0.82rem' }}
                >
                  <Send size={14} />
                  <span>{isSending ? 'Posting...' : 'Post Note'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Right Column: Status Lifecycle & Assignment Controls (Technician / Admin) */}
        {canEditStatus && (
          <div className="card" style={{ position: 'sticky', top: '1rem' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Wrench size={16} color="var(--accent-primary)" />
              <span>Lifecycle & Queue Controls</span>
            </h3>

            {updateSuccess && (
              <div style={{
                padding: '0.65rem 0.85rem',
                backgroundColor: 'var(--color-success-bg)',
                border: '1px solid var(--color-success-border)',
                borderRadius: 'var(--radius-md)',
                color: '#4ADE80',
                fontSize: '0.8rem',
                marginBottom: '1rem',
              }}>
                {updateSuccess}
              </div>
            )}

            <form onSubmit={handleUpdateTicket}>
              <div className="form-group">
                <label className="form-label">Incident Status</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="select"
                >
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Waiting on User">Waiting on User</option>
                  <option value="Resolved">Resolved</option>
                  <option value="Closed">Closed</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Priority Level</label>
                <select
                  value={newPriority}
                  onChange={(e) => setNewPriority(e.target.value)}
                  className="select"
                >
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Assigned Technician / Queue</label>
                <input
                  type="text"
                  value={newAssignee}
                  onChange={(e) => setNewAssignee(e.target.value)}
                  placeholder="e.g. Sarah Connor (NetOps)"
                  className="input"
                />
              </div>

              <div className="form-group" style={{ marginBottom: '1.25rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <label className="form-label" style={{ marginBottom: 0 }}>Resolution Notes</label>
                  <button
                    type="button"
                    onClick={handleDraftAISummary}
                    disabled={isGeneratingSummary}
                    className="btn btn-ghost"
                    style={{ padding: '2px 6px', fontSize: '0.72rem', color: 'var(--accent-primary)' }}
                    title="Draft formal resolution summary using Gemini / AI runbooks"
                  >
                    <Sparkles size={12} />
                    <span>{isGeneratingSummary ? 'Drafting...' : 'Draft with AI'}</span>
                  </button>
                </div>
                <textarea
                  rows={4}
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  placeholder="Detailed root cause and steps performed to restore service..."
                  className="textarea"
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', padding: '0.65rem' }}
              >
                <span>Save Changes</span>
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

