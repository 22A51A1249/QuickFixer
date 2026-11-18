import React from 'react';
import { useAuth } from '../context/AuthContext';
import { User, Shield, KeyRound, Building, Mail, Award, CheckCircle } from 'lucide-react';

export const Profile = () => {
  const { user } = useAuth();

  return (
    <div className="page-body">
      <div style={{ maxWidth: '680px', margin: '0 auto' }}>
        <div style={{ marginBottom: '1.75rem' }}>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
            👤 Corporate Identity & Access Profile
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            QuickFixer enterprise credentials, access roles, and assigned support queues.
          </p>
        </div>

        <div className="card" style={{ marginBottom: '1.5rem', padding: '1.75rem' }}>
          {/* Avatar and Main Info */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginBottom: '1.5rem', paddingBottom: '1.25rem', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              backgroundColor: 'rgba(59, 130, 246, 0.2)',
              border: '2px solid var(--accent-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.75rem',
              fontWeight: 800,
              color: 'var(--accent-primary)',
            }}>
              {user?.full_name?.charAt(0).toUpperCase()}
            </div>

            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800 }}>
                {user?.full_name}
              </h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
                <span style={{
                  padding: '0.15rem 0.6rem',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: 'rgba(59, 130, 246, 0.15)',
                  color: '#60A5FA',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'capitalize',
                }}>
                  {user?.role}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>•</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
                  {user?.id_badge_label}
                </span>
              </div>
            </div>
          </div>

          {/* Identity Fields Grid */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Mail size={16} color="var(--text-muted)" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Corporate Email:</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>{user?.email}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <User size={16} color="var(--text-muted)" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>System Username:</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>{user?.username}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Building size={16} color="var(--text-muted)" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Support Queue / Department:</div>
                <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-primary)' }}>{user?.team || 'General Employee Pool'}</div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Shield size={16} color="var(--text-muted)" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Account Status:</div>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: user?.is_active ? 'var(--color-success)' : 'var(--color-danger)' }}>
                  {user?.is_active ? '🟢 Verified & Active' : '🔴 Inactive'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Security Policy Card */}
        <div className="card" style={{ padding: '1.25rem', backgroundColor: 'rgba(15, 23, 42, 0.5)' }}>
          <h3 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <KeyRound size={15} color="var(--accent-primary)" />
            <span>Enterprise Security Compliance</span>
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            Access permissions are verified at each request against QuickFixer SQLite RBAC policies.
            Sessions expire automatically after 60 minutes of inactivity. For password resets or elevated role changes, contact your IT Administrator.
          </p>
        </div>
      </div>
    </div>
  );
};

