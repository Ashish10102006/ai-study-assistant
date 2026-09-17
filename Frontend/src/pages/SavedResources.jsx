import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { Bookmark, Trash2, ExternalLink, ArrowRight } from 'lucide-react';

export default function SavedResources() {
  const [savedList, setSavedList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSaved();
  }, []);

  const loadSaved = async () => {
    try {
      const data = await api.get('/api/resources/saved');
      setSavedList(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (id) => {
    try {
      await api.delete(`/api/resources/saved/${id}`);
      setSavedList(prev => prev.filter(item => item.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="container" style={{ padding: 'clamp(1.5rem, 3.5vw, 3rem) var(--container-pad, 1.5rem)', minHeight: '85vh' }}>
      <div style={{ marginBottom: '2rem' }}>
        <span className="badge badge-purple" style={{ marginBottom: '0.6rem' }}>
          Personal Academic Library
        </span>
        <h1 style={{ fontSize: 'clamp(1.75rem, 4vw, 2.4rem)', color: '#fff', marginBottom: '0.5rem', lineHeight: 1.2 }}>
          Saved Resources
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'clamp(0.92rem, 2vw, 1.05rem)' }}>
          Access your bookmarked academic research papers, reference manuals, and tutorials.
        </p>
      </div>

      {savedList.length === 0 ? (
        <div className="glass-card" style={{ padding: 'clamp(2rem, 4vw, 4rem) 1.5rem', textAlign: 'center', color: 'var(--text-muted)', borderRadius: '18px' }}>
          <Bookmark size={44} style={{ opacity: 0.3, marginBottom: '1rem' }} />
          <h3 style={{ fontSize: '1.2rem', color: '#fff', marginBottom: '0.5rem' }}>
            No saved resources yet.
          </h3>
          <p style={{ fontSize: '0.88rem', marginBottom: '1.5rem' }}>
            Save useful learning resources for later while studying or searching the web.
          </p>
          <Link to="/resources" className="btn btn-primary" style={{ minHeight: '44px' }}>
            <span>Explore Resources</span>
          </Link>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '1.25rem' }}>
          {savedList.map(item => (
            <div
              key={item.id}
              className="glass-card"
              style={{
                padding: 'clamp(1.1rem, 2.5vw, 1.5rem)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                borderRadius: '16px'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <span className="badge badge-cyan" style={{ fontSize: '0.72rem' }}>
                    {item.source}
                  </span>
                  <button
                    onClick={() => handleRemove(item.id)}
                    title="Remove from saved"
                    aria-label="Remove from saved"
                    style={{ color: 'var(--text-muted)', padding: '0.35rem', minWidth: '38px', minHeight: '38px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px', background: 'rgba(255, 255, 255, 0.04)' }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = '#ef4444'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                <h3 style={{ fontSize: '1.05rem', color: '#f8fafc', marginBottom: '0.5rem', lineHeight: '1.35', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                  {item.title}
                </h3>

                {item.description && (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '1rem', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                    {item.description}
                  </p>
                )}
              </div>

              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
                style={{ width: '100%', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', minHeight: '44px' }}
              >
                <span>Open Resource</span>
                <ExternalLink size={14} />
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
