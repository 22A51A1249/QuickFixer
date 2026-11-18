import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Zap, Eye, EyeOff, Lock, User, AlertCircle, ArrowRight, Shield } from 'lucide-react';

export const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier.trim() || !password) {
      setError('Please provide your corporate username or email, and password.');
      return;
    }

    setError('');
    setIsSubmitting(true);

    try {
      const user = await login(identifier.trim(), password);
      // Route dynamically to appropriate role workspace
      if (from !== '/' && from !== '/login') {
        navigate(from, { replace: true });
      } else {
        if (user.role === 'admin') navigate('/admin', { replace: true });
        else if (user.role === 'technician') navigate('/technician', { replace: true });
        else navigate('/dashboard', { replace: true });
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid corporate credentials. Please try again.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick fill helper for demo convenience
  const fillCredentials = (userType) => {
    if (userType === 'admin') {
      setIdentifier('admin');
      setPassword('ApexAdmin2026!');
    } else if (userType === 'tech') {
      setIdentifier('tech_sarah');
      setPassword('Password123!');
    } else {
      setIdentifier('emp_david');
      setPassword('Password123!');
    }
    setError('');
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--bg-primary)',
      padding: '2rem 1rem',
      backgroundImage: 'radial-gradient(ellipse at 50% 20%, rgba(59, 130, 246, 0.12) 0%, transparent 60%)',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '440px',
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-lg)',
        padding: '2.5rem',
      }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '52px',
            height: '52px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%)',
            color: '#FFFFFF',
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.4)',
            marginBottom: '1rem',
          }}>
            <Zap size={28} fill="#FFFFFF" />
          </div>

          <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
            QuickFixer
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            AI-Powered Enterprise IT Support & Issue Resolution
          </p>
          <div style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', fontWeight: 600, letterSpacing: '0.06em', marginTop: '0.4rem' }}>
            IDENTIFY • DIAGNOSE • RESOLVE
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.65rem',
            padding: '0.75rem 1rem',
            backgroundColor: 'var(--color-danger-bg)',
            border: '1px solid var(--color-danger-border)',
            borderRadius: 'var(--radius-md)',
            color: '#F87171',
            fontSize: '0.82rem',
            marginBottom: '1.25rem',
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '1px' }} />
            <div>{error}</div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username or Corporate Email</label>
            <div style={{ position: 'relative' }}>
              <User size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="e.g. admin or emp_david"
                className="input"
                style={{ paddingLeft: '2.4rem' }}
                autoComplete="username"
                disabled={isSubmitting}
              />
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '1.5rem' }}>
            <label className="form-label">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Corporate password"
                className="input"
                style={{ paddingLeft: '2.4rem', paddingRight: '2.5rem' }}
                autoComplete="current-password"
                disabled={isSubmitting}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: '4px',
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.75rem', fontSize: '0.92rem' }}
          >
            {isSubmitting ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div className="animate-spin" style={{ width: '16px', height: '16px', border: '2px solid #FFF', borderTopColor: 'transparent', borderRadius: '50%' }}></div>
                <span>Authenticating with QuickFixer...</span>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>Sign In to Service Desk</span>
                <ArrowRight size={16} />
              </div>
            )}
          </button>
        </form>

        {/* Quick Demo Role Selector */}
        <div style={{
          marginTop: '2rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid var(--border-subtle)',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
            Quick Demo Role Accounts
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => fillCredentials('employee')}
              className="btn btn-secondary"
              style={{ fontSize: '0.74rem', padding: '0.35rem 0.65rem' }}
            >
              👤 Employee
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('tech')}
              className="btn btn-secondary"
              style={{ fontSize: '0.74rem', padding: '0.35rem 0.65rem' }}
            >
              🛠️ Technician
            </button>
            <button
              type="button"
              onClick={() => fillCredentials('admin')}
              className="btn btn-secondary"
              style={{ fontSize: '0.74rem', padding: '0.35rem 0.65rem' }}
            >
              👑 Admin
            </button>
          </div>
        </div>

        {/* Security badge footer */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.4rem',
          marginTop: '1.5rem',
          fontSize: '0.7rem',
          color: 'var(--text-muted)',
        }}>
          <Shield size={12} color="var(--accent-primary)" />
          <span>RBAC Protected • ITIL v4 Compliant</span>
        </div>
      </div>
    </div>
  );
};
