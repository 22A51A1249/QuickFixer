import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ticketService } from '../services/ticketService';
import { StatCard } from '../components/StatCard';
import { TicketTable } from '../components/TicketTable';
import {
  Wrench,
  Clock,
  AlertTriangle,
  CheckCircle,
  FileText,
  UserCheck,
  Filter,
} from 'lucide-react';

export const TechnicianDashboard = ({ defaultFilter = 'All' }) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(defaultFilter);

  useEffect(() => {
    setActiveTab(defaultFilter);
  }, [defaultFilter]);

  useEffect(() => {
    fetchTechnicianTickets();
  }, []);

  const fetchTechnicianTickets = async () => {
    setIsLoading(true);
    try {
      const data = await ticketService.listTickets();
      setTickets(data);
    } catch (err) {
      console.error('Failed to load technician queue:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const assignedToMe = tickets.filter(t => {
    const assigned = (t.assigned_to || '').toLowerCase();
    return assigned.includes(user?.full_name?.toLowerCase()) || assigned.includes(user?.username?.toLowerCase());
  }).length;

  const teamTickets = tickets.filter(t => {
    if (!user?.team) return false;
    const assigned = (t.assigned_to || '').toLowerCase();
    return assigned.includes(user.team.toLowerCase());
  }).length;

  const openTickets = tickets.filter(t => t.status === 'Open').length;
  const inProgressTickets = tickets.filter(t => t.status === 'In Progress').length;
  const highPriorityTickets = tickets.filter(t => t.priority === 'Critical' || t.priority === 'High').length;
  const resolvedTickets = tickets.filter(t => t.status === 'Resolved' || t.status === 'Closed').length;

  // Filter based on active tab
  const getFilteredTickets = () => {
    if (activeTab === 'Assigned to Me') {
      return tickets.filter(t => {
        const assigned = (t.assigned_to || '').toLowerCase();
        return assigned.includes(user?.full_name?.toLowerCase()) || assigned.includes(user?.username?.toLowerCase());
      });
    }
    if (activeTab === 'Team Tickets') {
      return tickets.filter(t => {
        if (!user?.team) return true;
        const assigned = (t.assigned_to || '').toLowerCase();
        return assigned.includes(user.team.toLowerCase());
      });
    }
    if (activeTab === 'In Progress') {
      return tickets.filter(t => t.status === 'In Progress');
    }
    if (activeTab === 'Resolved') {
      return tickets.filter(t => t.status === 'Resolved' || t.status === 'Closed');
    }
    return tickets;
  };

  return (
    <div className="page-body">
      {/* Header Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.75rem',
      }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            🛠️ Technician Workspace & Queue Dispatch
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Technician: <strong>{user?.full_name}</strong> | ID: <code>{user?.id_badge_label}</code> | Queue: <strong>{user?.team || 'General IT Queue'}</strong>
          </p>
        </div>

        <button
          onClick={() => navigate('/tickets/new')}
          className="btn btn-secondary"
          style={{ fontSize: '0.85rem' }}
        >
          <span>Log Incoming Incident</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2rem',
      }}>
        <StatCard
          title="Assigned to Me"
          value={assignedToMe}
          icon={UserCheck}
          color="var(--accent-primary)"
          delta={`${assignedToMe} active in queue`}
        />
        <StatCard
          title="Open Queue"
          value={openTickets}
          icon={Clock}
          color="var(--color-warning)"
          delta={`${openTickets} unassigned/open`}
        />
        <StatCard
          title="Critical & High Priority"
          value={highPriorityTickets}
          icon={AlertTriangle}
          color="var(--color-danger)"
          delta="Urgent attention required"
        />
        <StatCard
          title="Resolved Tickets"
          value={resolvedTickets}
          icon={CheckCircle}
          color="var(--color-success)"
          subtext="Closed with runbook solutions"
        />
      </div>

      {/* Queue View Tabs */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        marginBottom: '1.25rem',
        borderBottom: '1px solid var(--border-subtle)',
        paddingBottom: '0.5rem',
      }}>
        {['All Tickets', 'Assigned to Me', 'Team Tickets', 'In Progress', 'Resolved'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: 'transparent',
              border: 'none',
              padding: '0.45rem 0.85rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.82rem',
              fontWeight: activeTab === tab ? 700 : 500,
              color: activeTab === tab ? 'var(--accent-primary)' : 'var(--text-secondary)',
              backgroundColor: activeTab === tab ? 'rgba(59, 130, 246, 0.12)' : 'transparent',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Ticket Table */}
      <TicketTable
        tickets={getFilteredTickets()}
        isLoading={isLoading}
        showRequester={true}
        showAssignee={true}
        baseDetailPath="/tickets"
      />
    </div>
  );
};

