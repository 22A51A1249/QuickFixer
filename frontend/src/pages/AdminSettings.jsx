import React, { useState, useEffect } from 'react';
import { adminService } from '../services/adminService';
import {
  Settings,
  Cpu,
  Key,
  Database,
  CheckCircle,
  AlertCircle,
  Sparkles,
  Sliders,
  ShieldAlert,
} from 'lucide-react';

export const AdminSettings = () => {
  const [health, setHealth] = useState(null);
  const [settingsData, setSettingsData] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [selectedModel, setSelectedModel] = useState('gemini-2.0-flash');
  const [temperature, setTemperature] = useState(0.1);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const [h, s] = await Promise.all([
        adminService.getSystemHealth(),
        adminService.getSettings(),
      ]);
      setHealth(h);
      setSettingsData(s);
      setSelectedModel(s.gemini_model || 'gemini-2.0-flash');
      setTemperature(s.temperature ?? 0.1);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage({ type: '', text: '' });
    try {
      await adminService.updateSettings({
        gemini_api_key: apiKey ? apiKey.trim() : undefined,
        gemini_model: selectedModel,
        temperature: parseFloat(temperature),
      });
      setMessage({ type: 'success', text: 'AI and system settings updated successfully!' });
      setApiKey('');
      await loadSettings();
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update settings.' });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="page-body">
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
          ⚙️ QuickFixer System & AI Configuration
        </h1>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          Configure Google Gemini LLM API credentials, inference parameters, and inspect database connectivity.
        </p>
      </div>

      {message.text && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.75rem 1rem',
          backgroundColor: message.type === 'success' ? 'var(--color-success-bg)' : 'var(--color-danger-bg)',
          border: `1px solid ${message.type === 'success' ? 'var(--color-success-border)' : 'var(--color-danger-border)'}`,
          borderRadius: 'var(--radius-md)',
          color: message.type === 'success' ? '#4ADE80' : '#F87171',
          marginBottom: '1.5rem',
          fontSize: '0.85rem',
        }}>
          {message.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          <span>{message.text}</span>
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(320px, 3fr) minmax(280px, 2fr)',
        gap: '1.5rem',
        alignItems: 'start',
      }}>
        {/* Left Form: AI Settings */}
        <div className="card">
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={18} color="var(--accent-primary)" />
            <span>Google Gemini Model Configuration</span>
          </h3>

          <form onSubmit={handleSave}>
            <div className="form-group">
              <label className="form-label">
                Google Gemini API Key
              </label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder={settingsData?.gemini_api_key_masked || 'Enter Google AI Studio API key...'}
                className="input"
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                {settingsData?.gemini_configured
                  ? '🟢 Gemini API key currently active in backend environment.'
                  : 'ℹ️ No API key set. System runs seamlessly via built-in offline RAG diagnostic engine.'}
              </span>
            </div>

            <div className="form-group">
              <label className="form-label">Active Gemini Model</label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="select"
              >
                <option value="gemini-2.0-flash">gemini-2.0-flash ⭐ (Recommended & Free tier)</option>
                <option value="gemini-1.5-pro">gemini-1.5-pro 🧠 (Deep Technical Reasoning)</option>
                <option value="gemini-1.5-flash">gemini-1.5-flash ⚡ (Fast Standard)</option>
              </select>
            </div>

            <div className="form-group" style={{ marginBottom: '1.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                <label className="form-label" style={{ marginBottom: 0 }}>Temperature ({temperature})</label>
                <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>0.0 = Deterministic, 1.0 = Creative</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
                style={{ width: '100%', accentColor: 'var(--accent-primary)' }}
              />
            </div>

            <button
              type="submit"
              disabled={isSaving}
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.75rem' }}
            >
              <span>{isSaving ? 'Updating...' : 'Save Configuration'}</span>
            </button>
          </form>
        </div>

        {/* Right Panel: System Diagnostics Health */}
        <div className="card" style={{ backgroundColor: 'rgba(23, 32, 51, 0.6)' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Cpu size={18} color="var(--accent-primary)" />
            <span>Operational Diagnostics</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div style={{
              padding: '0.75rem 1rem',
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>SQLite Database:</span>
                <span style={{ fontSize: '0.78rem', color: '#4ADE80', fontWeight: 700 }}>🟢 Operational</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                {health?.database?.path}
              </div>
            </div>

            <div style={{
              padding: '0.75rem 1rem',
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>FAISS Vector Store:</span>
                <span style={{ fontSize: '0.78rem', color: '#4ADE80', fontWeight: 700 }}>🟢 Active</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Chunks Loaded: <strong>{health?.vector_store?.chunks_loaded || 0}</strong> • Runbooks: <strong>{health?.vector_store?.indexed_runbooks || 0}</strong>
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                Embedding: {settingsData?.embedding_model}
              </div>
            </div>

            <div style={{
              padding: '0.75rem 1rem',
              backgroundColor: 'rgba(15, 23, 42, 0.6)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>AI Inference Engine:</span>
                <span style={{ fontSize: '0.78rem', color: health?.ai_engine?.gemini_online ? '#4ADE80' : '#FBBF24', fontWeight: 700 }}>
                  {health?.ai_engine?.gemini_online ? '🟢 Gemini 2.0 Online' : '🛡️ Offline Fallback Ready'}
                </span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                Model: <code>{health?.ai_engine?.model}</code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

