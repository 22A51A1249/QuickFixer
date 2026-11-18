import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert } from 'lucide-react';

export const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-secondary)',
        gap: '0.75rem'
      }}>
        <div className="animate-spin" style={{
          width: '28px',
          height: '28px',
          border: '3px solid var(--border-strong)',
          borderTopColor: 'var(--accent-primary)',
          borderRadius: '50%'
        }}></div>
        <span>Verifying enterprise credentials...</span>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: 'var(--bg-primary)',
        padding: '2rem'
      }}>
        <div className="card" style={{ maxWidth: '480px', textAlign: 'center', padding: '2.5rem' }}>
          <ShieldAlert size={48} color="var(--color-danger)" style={{ margin: '0 auto 1rem' }} />
          <h2 style={{ marginBottom: '0.75rem' }}>Access Denied</h2>
          <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
            Your account role (<strong>{user.role}</strong>) does not have authorization to view this enterprise workspace.
          </p>
          <button
            className="btn btn-primary"
            onClick={() => {
              if (user.role === 'admin') window.location.href = '/admin';
              else if (user.role === 'technician') window.location.href = '/technician';
              else window.location.href = '/dashboard';
            }}
          >
            Return to Authorized Dashboard
          </button>
        </div>
      </div>
    );
  }

  return children;
};

