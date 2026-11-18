import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ticketService } from '../services/ticketService';
import {
  TicketPlus,
  Sparkles,
  CheckCircle,
  AlertCircle,
  Cpu,
  Layers,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { PriorityBadge } from '../components/StatusBadge';

export const SubmitTicket = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [deviceInfo, setDeviceInfo] = useState('Windows 11 Enterprise (Corporate Laptop)');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [createdTicket, setCreatedTicket] = useState(null);

  // Live AI triage preview state
  const [triagePreview, setTriagePreview] = useState(null);
  const [isTriaging, setIsTriaging] = useState(false);

  useEffect(() => {
    if (description.trim().length < 8) {
      setTriagePreview(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsTriaging(true);
      try {
        const preview = await ticketService.previewTriage(description.trim());
        setTriagePreview(preview);
      } catch (e) {
        console.warn('Triage preview failed:', e);
      } finally {
        setIsTriaging(false);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [description]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) {
      setError('Please provide both an incident title and detailed description.');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      const ticket = await ticketService.createTicket({
        title: title.trim(),
        description: description.trim(),
        device_info: deviceInfo,
        category: triagePreview ? triagePreview.category : null,
        priority: triagePreview ? triagePreview.priority : null,
      });
      setCreatedTicket(ticket);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit ticket. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (createdTicket) {
    return (
      <div className="page-body">
        <div className="card" style={{ maxWidth: '640px', margin: '2rem auto', textAlign: 'center', padding: '2.5rem' }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            backgroundColor: 'var(--color-success-bg)',
            border: '1px solid var(--color-success-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem',
            color: '#4ADE80',
          }}>
            <CheckCircle size={32} />
          </div>

          <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
            Ticket Submitted Successfully!
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Your support request has been logged in QuickFixer and assigned to the service desk queue.
          </p>

          <div style={{
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem',
            textAlign: 'left',
            marginBottom: '1.75rem',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Ticket ID:</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-primary)' }}>
                {createdTicket.id}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Priority:</span>
              <PriorityBadge priority={createdTicket.priority} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Category:</span>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 600 }}>
                {createdTicket.category}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Assigned Team:</span>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-primary)' }}>
                {createdTicket.assigned_to || 'Tier 1 Service Desk'}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button
              onClick={() => navigate(`/tickets/${createdTicket.id}`)}
              className="btn btn-primary"
            >
              <span>View Ticket Details</span>
              <ArrowRight size={16} />
            </button>
            <button
              onClick={() => {
                setCreatedTicket(null);
                setTitle('');
                setDescription('');
                setTriagePreview(null);
              }}
              className="btn btn-secondary"
            >
              Submit Another Ticket
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-body">
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
          🎫 Submit IT Support Ticket
        </h1>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          Log an incident or hardware request with real-time semantic triage and priority classification.
        </p>
      </div>

      {error && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.75rem 1rem',
          backgroundColor: 'var(--color-danger-bg)',
          border: '1px solid var(--color-danger-border)',
          borderRadius: 'var(--radius-md)',
          color: '#F87171',
          marginBottom: '1.5rem',
        }}>
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(300px, 3fr) minmax(280px, 2fr)',
        gap: '1.5rem',
        alignItems: 'start',
      }}>
        {/* Left Form Column */}
        <div className="card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Incident Title / Brief Summary *</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Cisco AnyConnect VPN fails to connect with gateway timeout"
                className="input"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Detailed Description & Error Messages *</label>
              <textarea
                rows={6}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what happened, exact error codes, what you were trying to do, and business impact..."
                className="textarea"
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Device & Operating System</label>
              <select
                value={deviceInfo}
                onChange={(e) => setDeviceInfo(e.target.value)}
                className="select"
              >
                <option value="Windows 11 Enterprise (Corporate Laptop)">Windows 11 Enterprise (Corporate Laptop)</option>
                <option value="Windows 10 Pro (Workstation)">Windows 10 Pro (Workstation)</option>
                <option value="macOS Sonoma (MacBook Pro)">macOS Sonoma (MacBook Pro)</option>
                <option value="Ubuntu 22.04 LTS (Engineering VM)">Ubuntu 22.04 LTS (Engineering VM)</option>
                <option value="iOS / Android Corporate Mobile">iOS / Android Corporate Mobile</option>
              </select>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '1rem',
              marginTop: '1.25rem',
              paddingTop: '1rem',
              borderTop: '1px solid var(--border-subtle)',
            }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Requester:</span>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {user?.full_name}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Corporate Email:</span>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {user?.email}
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary"
              style={{ width: '100%', marginTop: '1.5rem', padding: '0.75rem' }}
            >
              {isSubmitting ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div className="animate-spin" style={{ width: '16px', height: '16px', border: '2px solid #FFF', borderTopColor: 'transparent', borderRadius: '50%' }}></div>
                  <span>Logging Incident Ticket...</span>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <TicketPlus size={16} />
                  <span>Submit Ticket</span>
                </div>
              )}
            </button>
          </form>
        </div>

        {/* Right AI Triage Live Panel */}
        <div className="card" style={{ backgroundColor: 'rgba(23, 32, 51, 0.6)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Sparkles size={18} color="var(--accent-primary)" />
            <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
              AI Triage & Classification Engine
            </h3>
          </div>

          {isTriaging ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', padding: '2rem 0' }}>
              <div className="animate-spin" style={{ width: '16px', height: '16px', border: '2px solid var(--border-strong)', borderTopColor: 'var(--accent-primary)', borderRadius: '50%' }}></div>
              <span style={{ fontSize: '0.82rem' }}>Analyzing semantics & predicting routing...</span>
            </div>
          ) : triagePreview ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.65rem 0.85rem',
                backgroundColor: 'rgba(15, 23, 42, 0.6)',
                borderRadius: 'var(--radius-md)',
              }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Predicted Category:</span>
                <span style={{ fontWeight: 700, color: 'var(--accent-primary)', fontSize: '0.85rem' }}>
                  {triagePreview.category}
                </span>
              </div>

              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.65rem 0.85rem',
                backgroundColor: 'rgba(15, 23, 42, 0.6)',
                borderRadius: 'var(--radius-md)',
              }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Assessed Urgency / Priority:</span>
                <PriorityBadge priority={triagePreview.priority} />
              </div>

              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.65rem 0.85rem',
                backgroundColor: 'rgba(15, 23, 42, 0.6)',
                borderRadius: 'var(--radius-md)',
              }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Recommended Queue:</span>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.82rem' }}>
                  {triagePreview.recommended_team}
                </span>
              </div>

              <div style={{
                padding: '0.75rem',
                backgroundColor: 'rgba(15, 23, 42, 0.6)',
                borderRadius: 'var(--radius-md)',
              }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.4rem', fontWeight: 600 }}>
                  Immediate Self-Service Recommendations:
                </div>
                <ul style={{ paddingLeft: '1.25rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                  {triagePreview.immediate_actions?.map((step, i) => (
                    <li key={i} style={{ marginBottom: '0.2rem' }}>{step}</li>
                  ))}
                </ul>
              </div>

              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Cpu size={12} />
                <span>Confidence score: {Math.round(triagePreview.confidence * 100)}%</span>
              </div>
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '2.5rem 1rem',
              color: 'var(--text-muted)',
              fontSize: '0.82rem',
            }}>
              <Layers size={32} color="var(--border-strong)" style={{ margin: '0 auto 0.75rem' }} />
              <p>Type a description of your issue on the left.</p>
              <p style={{ fontSize: '0.75rem', marginTop: '0.25rem' }}>
                Our AI model will automatically analyze sentiment, detect category, determine priority, and suggest initial troubleshooting.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

