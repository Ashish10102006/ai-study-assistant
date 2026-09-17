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
    <div className="container" style={{ padding: '3rem 1.5rem', minHeight: '85vh' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <span className="badge badge-emerald" style={{ marginBottom: '0.6rem' }}>
          Personal Academic Library
        </span>
        <h1 style={{ fontSize: '2.4rem', color: '#fff', marginBottom: '0.5rem' }}>
          Saved Resources
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem' }}>
          Access your bookmarked academic research papers, reference manuals, and tutorials.
        </p>
      </div>

      {savedList.length === 0 ? (
        <div className="glass-card" style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Bookmark size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
          <h3 style={{ fontSize: '1.2rem', color: '#fff', marginBottom: '0.5rem' }}>
            No saved resources yet.
          </h3>
          <p style={{ fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Save useful learning resources for later while studying or searching the web.
          </p>
          <Link to="/resources" className="btn btn-primary">
            <span>Explore Resources</span>
          </Link>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {savedList.map(item => (
            <div
              key={item.id}
              className="glass-card"
              style={{
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
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
                    style={{ color: 'var(--text-muted)', padding: '0.35rem' }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = '#ef4444'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; }}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                <h3 style={{ fontSize: '1.15rem', color: '#f8fafc', marginBottom: '0.5rem', lineHeight: '1.35' }}>
                  {item.title}
                </h3>

                {item.description && (
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '1rem' }}>
                    {item.description}
                  </p>
                )}
              </div>

              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-secondary"
                style={{ width: '100%', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}
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
