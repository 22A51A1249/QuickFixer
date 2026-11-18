import React from 'react';
import { useLocation } from 'react-router-dom';
import { ChatWindow } from '../components/ChatWindow';

export const Chat = () => {
  const location = useLocation();
  const initialPrompt = location.state?.initialPrompt || '';

  return (
    <div className="page-body" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
          💬 AI IT Support Assistant
        </h1>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          Stateful LangGraph orchestration with verified corporate runbook retrieval & automatic ticket escalation.
        </p>
      </div>

      <ChatWindow initialPrompt={initialPrompt} />
    </div>
  );
};

