import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/adminService';
import {
  BookOpen,
  Upload,
  RefreshCw,
  Search,
  Trash2,
  FileText,
  CheckCircle,
  AlertCircle,
  Eye,
  Cpu,
  Layers,
} from 'lucide-react';

export const KnowledgeBase = () => {
  const { isAdmin } = useAuth();

  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docContent, setDocContent] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);
  const [statusMessage, setStatusMessage] = useState({ type: '', text: '' });

  // Semantic search testing state
  const [searchQuery, setSearchQuery] = useState('AnyConnect VPN connection timed out at 85%');
  const [topK, setTopK] = useState(3);
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await adminService.listDocuments();
      setDocuments(docs);
      if (docs.length > 0 && !selectedDoc) {
        handleViewContent(docs[0].filename);
      }
    } catch (err) {
      console.error('Failed to load knowledge base:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setStatusMessage({ type: '', text: '' });
    try {
      const res = await adminService.uploadDocument(file);
      setStatusMessage({ type: 'success', text: `Document "${file.name}" uploaded. Triggering automatic index rebuild...` });
      // Re-index
      await adminService.reindexKnowledgeBase();
      setStatusMessage({ type: 'success', text: `Document "${file.name}" uploaded and FAISS vector index rebuilt!` });
      await loadDocuments();
    } catch (err) {
      setStatusMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to upload document.' });
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (filename) => {
    if (!confirm(`Are you sure you want to delete "${filename}" from the knowledge base?`)) return;

    try {
      await adminService.deleteDocument(filename);
      setStatusMessage({ type: 'success', text: `Runbook "${filename}" deleted.` });
      await loadDocuments();
      if (selectedDoc === filename) {
        setSelectedDoc(null);
        setDocContent('');
      }
    } catch (err) {
      alert('Delete failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleReindex = async () => {
    setIsReindexing(true);
    setStatusMessage({ type: '', text: '' });
    try {
      const res = await adminService.reindexKnowledgeBase();
      setStatusMessage({ type: 'success', text: res.message });
      await loadDocuments();
    } catch (err) {
      setStatusMessage({ type: 'error', text: 'Reindexing failed: ' + (err.response?.data?.detail || err.message) });
    } finally {
      setIsReindexing(false);
    }
  };

  const handleViewContent = async (filename) => {
    setSelectedDoc(filename);
    try {
      const res = await adminService.getDocumentContent(filename);
      setDocContent(res.content);
    } catch (err) {
      setDocContent('Unable to preview document content.');
    }
  };

  const handleSearchPlayground = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const results = await adminService.searchKnowledgeBase(searchQuery.trim(), topK);
      setSearchResults(results);
    } catch (err) {
      console.error('Search playground error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="page-body">
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.75rem',
      }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800 }}>
            📚 IT Knowledge Base & FAISS Vector Store Hub
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
            Manage standard operating procedures (SOPs), runbook embeddings, and semantic RAG retrieval.
          </p>
        </div>

        {isAdmin && (
          <div style={{ display: 'flex', gap: '0.65rem' }}>
            <label className="btn btn-secondary" style={{ cursor: 'pointer', fontSize: '0.82rem' }}>
              <Upload size={14} />
              <span>{isUploading ? 'Uploading...' : 'Upload Runbook'}</span>
              <input
                type="file"
                accept=".md,.txt,.pdf,.docx"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                disabled={isUploading}
              />
            </label>

            <button
              onClick={handleReindex}
              disabled={isReindexing}
              className="btn btn-primary"
              style={{ fontSize: '0.82rem' }}
            >
              <RefreshCw size={14} className={isReindexing ? 'animate-spin' : ''} />
              <span>{isReindexing ? 'Reindexing Chunks...' : 'Rebuild FAISS Index'}</span>
            </button>
          </div>
        )}
      </div>

      {statusMessage.text && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.75rem 1rem',
          backgroundColor: statusMessage.type === 'success' ? 'var(--color-success-bg)' : 'var(--color-danger-bg)',
          border: `1px solid ${statusMessage.type === 'success' ? 'var(--color-success-border)' : 'var(--color-danger-border)'}`,
          borderRadius: 'var(--radius-md)',
          color: statusMessage.type === 'success' ? '#4ADE80' : '#F87171',
          fontSize: '0.85rem',
          marginBottom: '1.5rem',
        }}>
          {statusMessage.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          <span>{statusMessage.text}</span>
        </div>
      )}

      {/* Semantic Retrieval Playground Card */}
      <div className="card" style={{ marginBottom: '1.75rem' }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Search size={16} color="var(--accent-primary)" />
          <span>Semantic Vector Search Playground (FAISS Cosine Similarity)</span>
        </h3>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
          Test query vectorization through SentenceTransformers (<code>all-MiniLM-L6-v2</code>) and inspect top retrieved chunks:
        </p>

        <form onSubmit={handleSearchPlayground} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
          <div style={{ flex: 1, minWidth: '260px' }}>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Enter technical query to test semantic retrieval..."
              className="input"
            />
          </div>
          <div style={{ width: '100px' }}>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="select"
            >
              <option value={1}>Top 1</option>
              <option value={2}>Top 2</option>
              <option value={3}>Top 3</option>
              <option value={5}>Top 5</option>
            </select>
          </div>
          <button type="submit" disabled={isSearching} className="btn btn-secondary">
            <span>{isSearching ? 'Retrieving...' : 'Search Index'}</span>
          </button>
        </form>

        {searchResults.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {searchResults.map((res, i) => (
              <div key={i} style={{
                padding: '0.85rem',
                backgroundColor: 'rgba(11, 16, 32, 0.7)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                  <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.85rem' }}>
                    #{i + 1} {res.title} ({res.source})
                  </span>
                  <span style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    color: '#4ADE80',
                    backgroundColor: 'rgba(22, 163, 74, 0.15)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-full)'
                  }}>
                    Match Score: {Math.round(res.score * 100)}%
                  </span>
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                  {res.text}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Two Column Document Browser */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(280px, 1fr) minmax(360px, 2fr)',
        gap: '1.5rem',
        alignItems: 'start',
      }}>
        {/* Document List */}
        <div className="card">
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, marginBottom: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <FileText size={16} color="var(--accent-primary)" />
            <span>Indexed Runbook Documents ({documents.length})</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', maxHeight: '500px', overflowY: 'auto' }}>
            {documents.map((doc) => {
              const isSelected = selectedDoc === doc.filename;
              return (
                <div
                  key={doc.filename}
                  onClick={() => handleViewContent(doc.filename)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.65rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'rgba(15, 23, 42, 0.5)',
                    border: `1px solid ${isSelected ? 'var(--accent-primary)' : 'var(--border-subtle)'}`,
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                  }}
                >
                  <div style={{ overflow: 'hidden' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.82rem', color: isSelected ? '#60A5FA' : 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {doc.filename}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {(doc.size_bytes / 1024).toFixed(1)} KB • {doc.modified_at?.substring(0, 10)}
                    </div>
                  </div>

                  {isAdmin && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(doc.filename);
                      }}
                      className="btn-ghost"
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--text-muted)',
                        cursor: 'pointer',
                        padding: '4px',
                      }}
                      title="Delete Runbook"
                    >
                      <Trash2 size={14} color="#EF4444" />
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Document Content Previewer */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem', paddingBottom: '0.65rem', borderBottom: '1px solid var(--border-subtle)' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              📖 {selectedDoc || 'Select Runbook'}
            </h3>
            {selectedDoc && (
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                Markdown Runbook SOP
              </span>
            )}
          </div>

          <div style={{
            backgroundColor: 'rgba(11, 16, 32, 0.7)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem',
            maxHeight: '520px',
            overflowY: 'auto',
            fontSize: '0.85rem',
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-secondary)',
          }}>
            {docContent || 'Select an indexed runbook from the left panel to inspect its standard operating procedures.'}
          </div>
        </div>
      </div>
    </div>
  );
};

