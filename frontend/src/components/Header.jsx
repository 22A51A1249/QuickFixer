import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Bot, Bell, Shield, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Header = ({ title = 'QuickFixer IT Workspace', subtitle = 'AI-Powered Enterprise Issue Resolution' }) => {
  const { user, isAdmin, isTechnician } = useAuth();

  return (
    <header style={{
      height: '64px',
      backgroundColor: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
      flexShrink: 0,
    }}>
      <div>
        <h1 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {title}
        </h1>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {subtitle}
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <Link to="/chat" className="btn btn-secondary" style={{ padding: '0.4rem 0.75rem', fontSize: '0.78rem' }}>
          <Sparkles size={14} color="var(--accent-primary)" />
          <span>Ask AI Assistant</span>
        </Link>

        {/* User quick pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          padding: '0.35rem 0.75rem',
          backgroundColor: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-full)',
        }}>
          <div style={{
            width: '26px',
            height: '26px',
            borderRadius: '50%',
            backgroundColor: 'var(--accent-primary)',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 700,
            fontSize: '0.75rem'
          }}>
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
          </div>
          <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
            {user?.full_name}
          </span>
          <span style={{
            fontSize: '0.68rem',
            padding: '0.1rem 0.45rem',
            borderRadius: 'var(--radius-full)',
            backgroundColor: isAdmin ? 'rgba(245, 158, 11, 0.2)' : isTechnician ? 'rgba(59, 130, 246, 0.2)' : 'rgba(22, 163, 74, 0.2)',
            color: isAdmin ? '#FBBF24' : isTechnician ? '#60A5FA' : '#4ADE80',
            fontWeight: 700,
            textTransform: 'uppercase',
          }}>
            {user?.role}
          </span>
        </div>
      </div>
    </header>
  );
};

