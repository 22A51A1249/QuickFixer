import React from 'react';

export const StatCard = ({ title, value, icon: Icon, delta, color = 'var(--accent-primary)', subtext }) => {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {title}
        </span>
        {Icon && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '36px',
            height: '36px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'rgba(255, 255, 255, 0.05)',
            color: color
          }}>
            <Icon size={20} />
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem' }}>
        <span style={{ fontSize: '1.85rem', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
          {value}
        </span>
        {delta && (
          <span style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            color: delta.startsWith('+') || delta.includes('active') ? 'var(--color-warning)' : 'var(--color-success)',
          }}>
            {delta}
          </span>
        )}
      </div>

      {subtext && (
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {subtext}
        </span>
      )}
    </div>
  );
};

