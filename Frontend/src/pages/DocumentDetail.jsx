import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import Loading3D from '../components/3d/Loading3D';
import {
  FileText,
  Sparkles,
  CheckSquare,
  HelpCircle,
  BookMarked,
  Send,
  ArrowLeft,
  Layers,
  Copy,
  Check
} from 'lucide-react';

export default function DocumentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [docQuestion, setDocQuestion] = useState('');
  const [docAnswer, setDocAnswer] = useState(null);
  const [answering, setAnswering] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadDoc();
  }, [id]);

  const loadDoc = async () => {
    try {
      const data = await api.get(`/api/documents/${id}`);
      setDocument(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAskDoc = async (e) => {
    e.preventDefault();
    if (!docQuestion.trim()) return;

    setAnswering(true);
    setDocAnswer(null);
    try {
      const res = await api.post(`/api/documents/${id}/ask`, {
        question: docQuestion.trim(),
        explanation_mode: 'simple'
      });
      setDocAnswer(res.answer);
    } catch (err) {
      setDocAnswer('Failed to retrieve answer from document. Please try again.');
    } finally {
      setAnswering(false);
    }
  };

  const handleCopy = () => {
    if (!docAnswer) return;
    navigator.clipboard.writeText(docAnswer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return <Loading3D message="Loading document and extracting chunks..." />;
  }

  if (!document) {
    return (
      <div className="container" style={{ padding: '4rem 1.5rem', textAlign: 'center' }}>
        <h2>Document not found.</h2>
        <button onClick={() => navigate('/materials')} className="btn btn-secondary" style={{ marginTop: '1rem' }}>
          Back to Materials
        </button>
      </div>
    );
  }

  return (
    <div className="container" style={{ padding: '3rem 1.5rem', minHeight: '85vh' }}>
      <button
        onClick={() => navigate('/materials')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          color: 'var(--text-muted)',
          fontSize: '0.9rem',
          marginBottom: '1.5rem',
          background: 'none',
          cursor: 'pointer'
        }}
      >
        <ArrowLeft size={16} />
        <span>Back to Study Materials</span>
      </button>

      {/* Header Info */}
      <div
        className="glass-card"
        style={{
          padding: '2rem',
          marginBottom: '2.5rem',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '1.5rem'
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
            <span className="badge badge-purple">Grounded Document</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Status: {document.processing_status}
            </span>
          </div>
          <h1 style={{ fontSize: '2rem', color: '#fff', marginBottom: '0.4rem' }}>
            {document.file_name}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            {document.chunks_count} Extracted Text Chunks • {(document.file_size / 1024 / 1024).toFixed(2)} MB
          </p>
        </div>

        {/* Action Shortcuts */}
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => navigate('/study', { state: { selectedDocId: document.id, tab: 'notes' } })}
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem' }}
          >
            <BookMarked size={16} />
            <span>Generate Notes</span>
          </button>
          <button
            onClick={() => navigate('/study', { state: { selectedDocId: document.id, tab: 'quiz' } })}
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem' }}
          >
            <CheckSquare size={16} />
            <span>Generate Quiz</span>
          </button>
          <button
            onClick={() => navigate('/study', { state: { selectedDocId: document.id, tab: 'questions' } })}
            className="btn btn-primary"
            style={{ fontSize: '0.85rem' }}
          >
            <HelpCircle size={16} />
            <span>Practice Problems</span>
          </button>
        </div>
      </div>

      {/* Grounded Q&A Bar */}
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2.5rem' }}>
        <h3 style={{ fontSize: '1.3rem', color: '#fff', marginBottom: '0.4rem' }}>
          Ask Questions Grounded Strictly In This Document
        </h3>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          Answers will only use facts extracted from this document. If not present in the document, the AI will honestly state so.
        </p>

        <form onSubmit={handleAskDoc} style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <input
            type="text"
            value={docQuestion}
            onChange={(e) => setDocQuestion(e.target.value)}
            placeholder="e.g. What are the key points in Chapter 2? Explain the main theorem..."
            style={{ borderRadius: '14px', height: '50px' }}
          />
          <button
            type="submit"
            disabled={answering || !docQuestion.trim()}
            className="btn btn-primary"
            style={{ height: '50px', padding: '0 1.5rem', borderRadius: '14px', whiteSpace: 'nowrap' }}
          >
            <Send size={18} />
            <span>Ask Document</span>
          </button>
        </form>

        {answering && <Loading3D message="Analyzing document chunks with Gemini..." />}

        {docAnswer && (
          <div
            style={{
              padding: '1.5rem',
              borderRadius: '14px',
              background: 'rgba(10, 15, 26, 0.85)',
              border: '1px solid rgba(0, 242, 254, 0.25)',
              position: 'relative'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--brand-cyan)' }}>
                DOCUMENT GROUNDED ANSWER
              </span>
              <button
                onClick={handleCopy}
                style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem' }}
              >
                {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.65', color: '#f8fafc', fontSize: '0.95rem' }}>
              {docAnswer}
            </div>
          </div>
        )}
      </div>

      {/* Extracted Chunks Preview */}
      <div>
        <h3 style={{ fontSize: '1.3rem', marginBottom: '1rem', color: '#fff' }}>
          Extracted Document Chunks ({document.preview_chunks?.length || 0})
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {document.preview_chunks?.map((chunk) => (
            <div
              key={chunk.id}
              style={{
                padding: '1.25rem',
                borderRadius: '12px',
                background: 'rgba(15, 23, 42, 0.5)',
                border: '1px solid rgba(255, 255, 255, 0.06)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                <span>Chunk #{chunk.chunk_index + 1}</span>
                {chunk.metadata?.page && <span>Page {chunk.metadata.page}</span>}
              </div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: '1.55' }}>
                {chunk.content}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
