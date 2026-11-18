import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  BotMessageSquare,
  TicketPlus,
  Ticket,
  BookOpen,
  Users,
  ShieldCheck,
  Settings,
  LogOut,
  User as UserIcon,
  Zap,
  Wrench,
  Clock,
  CheckCircle2,
  Cpu,
  History,
  UsersRound,
  FolderKanban,
  BarChart3,
  Layers,
} from 'lucide-react';

export const Sidebar = () => {
  const { user, logout, isAdmin, isTechnician } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const roleLabel = user ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : '';
  const roleIcon = isAdmin ? '👑' : isTechnician ? '🛠️' : '👤';

  return (
    <aside style={{
      width: '260px',
      height: '100vh',
      backgroundColor: 'var(--bg-secondary)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      flexShrink: 0,
    }}>
      {/* Brand Header */}
      <div style={{
        padding: '1.25rem 1.25rem 1rem',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.2rem' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF',
            boxShadow: '0 0 12px rgba(59, 130, 246, 0.4)',
          }}>
            <Zap size={18} fill="#FFFFFF" />
          </div>
          <div>
            <div style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#FFFFFF' }}>
              QUICKFIXER
            </div>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              Enterprise IT Support
            </div>
          </div>
        </div>
        <div style={{ fontSize: '0.65rem', color: 'var(--accent-primary)', fontWeight: 600, letterSpacing: '0.04em', marginTop: '0.35rem' }}>
          IDENTIFY • DIAGNOSE • RESOLVE
        </div>
      </div>

      {/* User Card */}
      <div style={{
        margin: '0.85rem 0.85rem 0.5rem',
        padding: '0.75rem',
        backgroundColor: 'rgba(23, 32, 51, 0.7)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '50%',
            backgroundColor: 'rgba(59, 130, 246, 0.15)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1rem',
          }}>
            {roleIcon}
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div style={{
              fontWeight: 700,
              fontSize: '0.85rem',
              color: 'var(--text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}>
              {user?.full_name || 'Corporate User'}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.1rem' }}>
              <span style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                {roleLabel}
              </span>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>•</span>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                {user?.id_badge_label}
              </span>
            </div>
          </div>
        </div>
        {user?.team && (
          <div style={{
            fontSize: '0.7rem',
            color: 'var(--text-muted)',
            marginTop: '0.4rem',
            paddingTop: '0.4rem',
            borderTop: '1px dashed var(--border-subtle)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}>
            Queue: {user.team}
          </div>
        )}
      </div>

      {/* Navigation Links */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '0.5rem 0.65rem', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
        {/* EMPLOYEE NAVIGATION */}
        {!isAdmin && !isTechnician && (
          <>
            <NavItem to="/dashboard" icon={LayoutDashboard} label="Overview" />
            <NavItem to="/chat" icon={BotMessageSquare} label="AI IT Assistant" badge="Active" />
            <NavItem to="/tickets/new" icon={TicketPlus} label="Create Ticket" />
            <NavItem to="/tickets" icon={Ticket} label="My Tickets" />
            <NavItem to="/tickets/history" icon={History} label="Ticket History" />
            <NavItem to="/knowledge" icon={BookOpen} label="Knowledge Base" />
          </>
        )}

        {/* TECHNICIAN NAVIGATION */}
        {isTechnician && !isAdmin && (
          <>
            <NavItem to="/technician" icon={LayoutDashboard} label="Overview" />
            <NavItem to="/technician/tickets" icon={Wrench} label="Assigned Tickets" />
            <NavItem to="/technician/team" icon={UsersRound} label="Team Tickets" />
            <NavItem to="/technician/in-progress" icon={Clock} label="In Progress" />
            <NavItem to="/technician/resolved" icon={CheckCircle2} label="Resolved Tickets" />
            <NavItem to="/chat" icon={BotMessageSquare} label="AI IT Assistant" />
            <NavItem to="/knowledge" icon={BookOpen} label="Knowledge Base" />
          </>
        )}

        {/* ADMIN NAVIGATION */}
        {isAdmin && (
          <>
            <NavItem to="/admin" icon={LayoutDashboard} label="Overview" />
            <NavItem to="/admin/tickets" icon={Ticket} label="All Tickets" />
            <NavItem to="/admin/users" icon={Users} label="User Management" />
            <NavItem to="/admin/technicians" icon={Wrench} label="Technician Management" />
            <NavItem to="/admin/teams" icon={FolderKanban} label="Team Management" />
            <NavItem to="/admin/knowledge" icon={BookOpen} label="Knowledge Base" />
            <NavItem to="/admin/analytics" icon={BarChart3} label="AI Analytics" />
            <NavItem to="/admin/audit-logs" icon={ShieldCheck} label="Audit Logs" />
            <NavItem to="/admin/settings" icon={Settings} label="Settings" />
            <NavItem to="/chat" icon={BotMessageSquare} label="AI IT Assistant" />
          </>
        )}

        <div style={{ height: '1px', backgroundColor: 'var(--border-subtle)', margin: '0.5rem 0' }} />
        <NavItem to="/profile" icon={UserIcon} label="My Profile" />
      </nav>

      {/* Footer / Engine Pill & Logout */}
      <div style={{
        padding: '0.85rem',
        borderTop: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.65rem',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.45rem',
          padding: '0.4rem 0.6rem',
          borderRadius: 'var(--radius-sm)',
          backgroundColor: 'rgba(22, 163, 74, 0.1)',
          border: '1px solid rgba(22, 163, 74, 0.25)',
          fontSize: '0.72rem',
          color: '#4ADE80',
          fontWeight: 600,
        }}>
          <div style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: '#22C55E',
            boxShadow: '0 0 6px #22C55E'
          }}></div>
          <Cpu size={13} />
          <span>QuickFix AI • RAG Online</span>
        </div>

        <button
          onClick={handleLogout}
          className="btn btn-ghost"
          style={{ width: '100%', justifyContent: 'flex-start', padding: '0.45rem 0.6rem', fontSize: '0.8rem' }}
        >
          <LogOut size={16} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};

const NavItem = ({ to, icon: Icon, label, badge }) => (
  <NavLink
    to={to}
    end={to === '/dashboard' || to === '/technician' || to === '/admin'}
    style={({ isActive }) => ({
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '0.65rem',
      padding: '0.55rem 0.75rem',
      borderRadius: 'var(--radius-md)',
      color: isActive ? '#FFFFFF' : 'var(--text-secondary)',
      backgroundColor: isActive ? 'var(--accent-primary)' : 'transparent',
      fontWeight: isActive ? 600 : 500,
      fontSize: '0.85rem',
      transition: 'all var(--transition-fast)',
    })}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
      <Icon size={17} />
      <span>{label}</span>
    </div>
    {badge && (
      <span style={{
        fontSize: '0.65rem',
        padding: '0.1rem 0.4rem',
        borderRadius: 'var(--radius-full)',
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        color: '#FFFFFF',
        fontWeight: 700,
      }}>
        {badge}
      </span>
    )}
  </NavLink>
);

