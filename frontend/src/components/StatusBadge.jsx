import React from 'react';

export const StatusBadge = ({ status }) => {
  const norm = (status || '').toLowerCase().replace(/_/g, ' ');

  if (norm.includes('open')) {
    return <span className="badge badge-open">🔵 Open</span>;
  }
  if (norm.includes('progress')) {
    return <span className="badge badge-in-progress">🔄 In Progress</span>;
  }
  if (norm.includes('waiting')) {
    return <span className="badge badge-waiting">⏳ Waiting</span>;
  }
  if (norm.includes('resolved')) {
    return <span className="badge badge-resolved">✅ Resolved</span>;
  }
  if (norm.includes('closed')) {
    return <span className="badge badge-closed">⬛ Closed</span>;
  }

  return <span className="badge badge-open">{status}</span>;
};

export const PriorityBadge = ({ priority }) => {
  const norm = (priority || '').toLowerCase();

  if (norm.includes('critical')) {
    return <span className="badge priority-critical">🔴 Critical</span>;
  }
  if (norm.includes('high')) {
    return <span className="badge priority-high">🟠 High</span>;
  }
  if (norm.includes('medium')) {
    return <span className="badge priority-medium">🟡 Medium</span>;
  }
  if (norm.includes('low')) {
    return <span className="badge priority-low">🟢 Low</span>;
  }

  return <span className="badge priority-medium">{priority}</span>;
};

