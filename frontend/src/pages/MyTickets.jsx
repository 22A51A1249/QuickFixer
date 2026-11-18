import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ticketService } from '../services/ticketService';
import { TicketTable } from '../components/TicketTable';
import { Search, PlusCircle, AlertCircle, CheckCircle2 } from 'lucide-react';

export const MyTickets = ({ showHistoryOnly = false }) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [trackerId, setTrackerId] = useState('');
  const [trackerResult, setTrackerResult] = useState(null);
  const [trackerError, setTrackerError] = useState('');
  const [isTracking, setIsTracking] = useState(false);

  useEffect(() => {
    fetchTickets();
  }, [showHistoryOnly]);

  const fetchTickets = async () => {
    setIsLoading(true);
    try {
      const data = await ticketService.listTickets();
      if (showHistoryOnly) {
        setTickets(data.filter(t => t.status === 'Resolved' || t.status === 'Closed'));
      } else {
        setTickets(data);
      }
    } catch (err) {
      console.error('Failed to load tickets:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTrackTicket = async (e) => {
    e.preventDefault();
    if (!trackerId.trim()) return;

    setTrackerError('');
    setTrackerResult(null);
    setIsTracking(true);

    try {
      const ticket = await ticketService.getTicket(trackerId.trim().toUpperCase());
      setTrackerResult(ticket);
    } catch (err) {
      if (err.response?.status === 404) {
        setTrackerError(`Ticket "${trackerId.trim().toUpperCase()}" was not found.`);
      } else if (err.response?.status === 403) {
        setTrackerError('Access Denied: You do not have permission to access this ticket.');
      } else {
        setTrackerError('Failed to lookup ticket. Please try again.');
      }
    } finally {
      setIsTracking(false);
    }
  };

  return (
    <div className="page-body">
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.75rem',
      }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
            📋 My IT Support Tickets
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Showing support incidents submitted by {user?.full_name} ({user?.email})
          </p>
        </div>

        <button
          onClick={() => navigate('/tickets/new')}
          className="btn btn-primary"
        >
          <PlusCircle size={16} />
          <span>New Support Ticket</span>
        </button>
      </div>

      {/* Quick Status Tracker Card */}
      <div className="card" style={{ marginBottom: '1.75rem', padding: '1.25rem' }}>
        <form onSubmit={handleTrackTicket} style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '240px' }}>
            <input
              type="text"
              placeholder="Track any ticket status by ID (e.g. TICK-1001)..."
              value={trackerId}
              onChange={(e) => setTrackerId(e.target.value)}
              className="input"
              style={{ padding: '0.55rem 0.85rem', fontSize: '0.85rem' }}
            />
          </div>
          <button
            type="submit"
            disabled={isTracking || !trackerId.trim()}
            className="btn btn-secondary"
            style={{ padding: '0.55rem 1rem' }}
          >
            <Search size={15} />
            <span>Track Status</span>
          </button>
        </form>

        {trackerError && (
          <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#F87171', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <AlertCircle size={15} />
            <span>{trackerError}</span>
          </div>
        )}

        {trackerResult && (
          <div style={{
            marginTop: '1rem',
            padding: '1rem',
            backgroundColor: 'rgba(15, 23, 42, 0.7)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--accent-primary)' }}>
                  {trackerResult.id}
                </span>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {trackerResult.title}
                </span>
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Status: <strong>{trackerResult.status}</strong> • Priority: <strong>{trackerResult.priority}</strong> • Assigned: <strong>{trackerResult.assigned_to || 'Unassigned'}</strong>
              </div>
            </div>
            <button
              onClick={() => navigate(`/tickets/${trackerResult.id}`)}
              className="btn btn-primary"
              style={{ fontSize: '0.78rem', padding: '0.35rem 0.75rem' }}
            >
              Open Ticket View
            </button>
          </div>
        )}
      </div>

      {/* Main Ticket Table */}
      <TicketTable
        tickets={tickets}
        isLoading={isLoading}
        showRequester={false}
        showAssignee={true}
        baseDetailPath="/tickets"
      />
    </div>
  );
};

