import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import {
  Upload,
  FileText,
  Trash2,
  HelpCircle,
  Sparkles,
  BookMarked,
  CheckSquare,
  AlertCircle,
  CheckCircle2,
  FileSearch,
  ArrowRight
} from 'lucide-react';

export default function StudyMaterials() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const data = await api.get('/api/documents');
      setDocuments(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFileUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.upload('/api/documents/upload', formData);
      await loadDocuments();
    } catch (err) {
      setError(err.message || 'File upload failed. Please ensure file is PDF, TXT, or MD under 25MB.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (e, docId) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this study document?')) return;
    try {
      await api.delete(`/api/documents/${docId}`);
      setDocuments(prev => prev.filter(d => d.id !== docId));
    } catch (err) {
      console.error(err);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="container" style={{ padding: '3rem 1.5rem', minHeight: '85vh' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <span className="badge badge-purple" style={{ marginBottom: '0.6rem' }}>
          Document Intelligence
        </span>
        <h1 style={{ fontSize: '2.4rem', marginBottom: '0.5rem', color: '#fff' }}>
          Study Materials & Notes
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '650px' }}>
          Upload your lecture slides, syllabus PDFs, or revision notes. Ground Gemini AI explanations strictly within your course materials.
        </p>
      </div>

      {error && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            marginBottom: '2rem',
            color: '#f87171',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}
        >
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Drag & Drop Upload Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragOver ? 'var(--brand-cyan)' : 'rgba(255, 255, 255, 0.15)'}`,
          borderRadius: '20px',
          padding: '3.5rem 2rem',
          textAlign: 'center',
          background: dragOver ? 'rgba(0, 242, 254, 0.05)' : 'rgba(15, 22, 36, 0.5)',
          marginBottom: '3rem',
          transition: 'all 0.25s ease'
        }}
      >
        <div
          style={{
            width: '64px',
            height: '64px',
            borderRadius: '18px',
            background: 'var(--grad-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem auto',
            color: '#030712'
          }}
        >
          <Upload size={28} />
        </div>

        <h3 style={{ fontSize: '1.3rem', color: '#fff', marginBottom: '0.5rem' }}>
          Drag & Drop your study file here
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          Supports PDF, TXT, and Markdown files up to 25MB.
        </p>

        <label className="btn btn-primary" style={{ cursor: 'pointer', display: 'inline-flex' }}>
          <input
            type="file"
            accept=".pdf,.txt,.md"
            onChange={(e) => e.target.files && handleFileUpload(e.target.files[0])}
            disabled={uploading}
            style={{ display: 'none' }}
          />
          <span>{uploading ? 'Processing File...' : 'Browse Computer'}</span>
        </label>
      </div>

      {/* Uploaded Documents List */}
      <div>
        <h3 style={{ fontSize: '1.4rem', marginBottom: '1.25rem', color: '#fff' }}>
          Your Processed Course Documents
        </h3>

        {documents.length === 0 ? (
          <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            <FileText size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
            <h4 style={{ fontSize: '1.1rem', color: '#e2e8f0', marginBottom: '0.4rem' }}>
              No study materials uploaded yet.
            </h4>
            <p style={{ fontSize: '0.9rem' }}>
              Upload your notes or PDF above to study with grounded AI.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            {documents.map((doc) => (
              <div
                key={doc.id}
                onClick={() => navigate(`/materials/${doc.id}`)}
                className="glass-card"
                style={{
                  padding: '1.5rem',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                    <div
                      style={{
                        width: '44px',
                        height: '44px',
                        borderRadius: '12px',
                        background: 'rgba(192, 132, 252, 0.1)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#c084fc'
                      }}
                    >
                      <FileText size={22} />
                    </div>
                    <button
                      onClick={(e) => handleDelete(e, doc.id)}
                      title="Delete document"
                      style={{
                        color: 'var(--text-muted)',
                        padding: '0.4rem',
                        borderRadius: '8px',
                        background: 'rgba(255, 255, 255, 0.04)'
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = '#ef4444'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  <h4 style={{ fontSize: '1.1rem', color: '#f8fafc', marginBottom: '0.4rem', wordBreak: 'break-all' }}>
                    {doc.file_name}
                  </h4>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    {(doc.file_size / 1024 / 1024).toFixed(2)} MB • {doc.chunks_count || 0} Text Chunks
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
                    <span
                      style={{
                        fontSize: '0.72rem',
                        fontWeight: '700',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '6px',
                        background: doc.processing_status === 'COMPLETED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: doc.processing_status === 'COMPLETED' ? '#10b981' : '#f59e0b'
                      }}
                    >
                      {doc.processing_status}
                    </span>
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingTop: '1rem',
                    borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                    color: 'var(--brand-cyan)',
                    fontSize: '0.85rem',
                    fontWeight: '600'
                  }}
                >
                  <span>Study Document</span>
                  <ArrowRight size={15} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
