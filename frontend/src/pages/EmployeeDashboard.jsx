import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ticketService } from '../services/ticketService';
import { StatCard } from '../components/StatCard';
import { TicketTable } from '../components/TicketTable';
import {
  Sparkles,
  Ticket,
  Clock,
  CheckCircle,
  FileText,
  KeyRound,
  Wifi,
  Mail,
  AppWindow,
  Laptop,
  ShieldAlert,
  ArrowRight,
  PlusCircle,
} from 'lucide-react';

export const EmployeeDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const data = await ticketService.listTickets();
        setTickets(data);
      } catch (err) {
        console.error('Failed to load tickets:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchTickets();
  }, []);

  const openTickets = tickets.filter(t => t.status === 'Open').length;
  const inProgress = tickets.filter(t => t.status === 'In Progress').length;
  const resolved = tickets.filter(t => t.status === 'Resolved' || t.status === 'Closed').length;

  const quickCategories = [
    {
      title: 'Account & Login',
      icon: KeyRound,
      prompt: 'I am unable to log in to my company account. My credentials seem locked or MFA is not working.',
      color: '#3B82F6',
    },
    {
      title: 'Network & VPN',
      icon: Wifi,
      prompt: 'My Cisco AnyConnect VPN disconnects every few minutes or times out during TLS handshake.',
      color: '#10B981',
    },
    {
      title: 'Email & Collaboration',
      icon: Mail,
      prompt: 'Microsoft Outlook repeatedly freezes and crashes when opening my shared department mailbox.',
      color: '#8B5CF6',
    },
    {
      title: 'Software Issues',
      icon: AppWindow,
      prompt: 'My company application crashes unexpectedly with an error code and access violation.',
      color: '#F59E0B',
    },
    {
      title: 'Hardware Problems',
      icon: Laptop,
      prompt: 'My system suddenly froze and switched off. The laptop refuses to boot or display video.',
      color: '#EF4444',
    },
    {
      title: 'Security Issues',
      icon: ShieldAlert,
      prompt: 'I received a suspicious phishing email asking to verify my single sign-on corporate credentials.',
      color: '#EC4899',
    },
  ];

  const handleCategorySelect = (prompt) => {
    navigate('/chat', { state: { initialPrompt: prompt } });
  };

  return (
    <div className="page-body">
      {/* Welcome Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '2rem',
        padding: '1.75rem 2rem',
        background: 'linear-gradient(135deg, #172033 0%, #111827 100%)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-md)',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <span style={{ fontSize: '1.65rem' }}>👋</span>
            <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>
              Welcome back, {user?.full_name}!
            </h1>
          </div>
          <p style={{ fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
            How can QuickFixer help you resolve technical issues today?
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => navigate('/chat')}
            className="btn btn-primary"
            style={{ padding: '0.65rem 1.25rem', fontSize: '0.9rem' }}
          >
            <Sparkles size={16} />
            <span>Launch AI Assistant</span>
          </button>
          <button
            onClick={() => navigate('/tickets/new')}
            className="btn btn-secondary"
            style={{ padding: '0.65rem 1.25rem', fontSize: '0.9rem' }}
          >
            <PlusCircle size={16} />
            <span>Submit Ticket</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2rem',
      }}>
        <StatCard
          title="My Open Tickets"
          value={openTickets}
          icon={Ticket}
          color="var(--accent-primary)"
          delta={`${openTickets} awaiting review`}
        />
        <StatCard
          title="In Progress"
          value={inProgress}
          icon={Clock}
          color="var(--color-warning)"
          delta={`${inProgress} active`}
        />
        <StatCard
          title="Resolved Tickets"
          value={resolved}
          icon={CheckCircle}
          color="var(--color-success)"
          subtext="Successfully resolved issues"
        />
        <StatCard
          title="Total Requests"
          value={tickets.length}
          icon={FileText}
          color="#8B5CF6"
          subtext="Lifetime submitted tickets"
        />
      </div>

      {/* Quick Issue Categories Grid */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
              Guided Issue Categories
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Select a common issue domain to initiate instant AI-guided runbook troubleshooting:
            </p>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1rem',
        }}>
          {quickCategories.map((cat, idx) => {
            const Icon = cat.icon;
            return (
              <div
                key={idx}
                onClick={() => handleCategorySelect(cat.prompt)}
                className="card"
                style={{
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '1rem',
                  padding: '1.15rem',
                  transition: 'transform var(--transition-fast), border-color var(--transition-fast)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.borderColor = cat.color;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                }}
              >
                <div style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: `${cat.color}20`,
                  border: `1px solid ${cat.color}40`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: cat.color,
                  flexShrink: 0,
                }}>
                  <Icon size={20} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                    {cat.title}
                  </div>
                  <div style={{
                    fontSize: '0.78rem',
                    color: 'var(--text-muted)',
                    lineHeight: 1.4,
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}>
                    {cat.prompt}
                  </div>
                </div>
                <ArrowRight size={16} color="var(--text-muted)" style={{ marginTop: '0.2rem' }} />
              </div>
            );
          })}
        </div>
      </div>

      {/* My Recent Tickets Section */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700 }}>
              Recent Support Tickets
            </h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Track status updates and technician communications on your reported incidents:
            </p>
          </div>
          <button
            onClick={() => navigate('/tickets')}
            className="btn btn-ghost"
            style={{ fontSize: '0.82rem' }}
          >
            <span>View All My Tickets</span>
            <ArrowRight size={14} />
          </button>
        </div>

        <TicketTable
          tickets={tickets.slice(0, 5)}
          isLoading={isLoading}
          showRequester={false}
          baseDetailPath="/tickets"
        />
      </div>
    </div>
  );
};
