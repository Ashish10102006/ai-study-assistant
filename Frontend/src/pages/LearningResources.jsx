import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import SourceBadge from '../components/SourceBadge';
import Loading3D from '../components/3d/Loading3D';
import { Search, Globe, Filter, Bookmark, ExternalLink, AlertCircle, RefreshCw } from 'lucide-react';

export default function LearningResources() {
  const [query, setQuery] = useState('');
  const [subject, setSubject] = useState('Computer Science');
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Initial load of curated resources
    loadCurated();
  }, [subject]);

  const loadCurated = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get('/api/resources', { subject, topic: 'Fundamental Concepts' });
      setResources(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Curated resources fetch error:', err);
      const msg = err.message || '';
      if (msg.toLowerCase().includes('connect') || msg.toLowerCase().includes('failed') || msg.toLowerCase().includes('not found')) {
        setError('Academic discovery service is currently synchronizing with the backend. Please try searching below or retry.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    setError(null);
    try {
      const data = await api.post('/api/search', {
        query: query.trim(),
        subject,
        max_results: 8
      });
      setResources(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Academic search error:', err);
      setError('Unable to retrieve academic web resources at this moment. Please retry your search shortly.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ padding: 'clamp(1.5rem, 3.5vw, 3rem) var(--container-pad, 1.5rem)', minHeight: '85vh' }}>
      <div style={{ marginBottom: '2rem' }}>
        <span className="badge badge-cyan" style={{ marginBottom: '0.6rem' }}>
          Tavily Academic Discovery
        </span>
        <h1 style={{ fontSize: 'clamp(1.75rem, 4vw, 2.4rem)', color: '#fff', marginBottom: '0.5rem', lineHeight: 1.2 }}>
          Web Learning Resources
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'clamp(0.92rem, 2vw, 1.05rem)', maxWidth: '650px' }}>
          Search official documentation, university lecture portals, research papers, and verified study tutorials.
        </p>
      </div>

      {/* Error / Offline Alert */}
      {error && (
        <div
          style={{
            background: 'rgba(245, 158, 11, 0.12)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: '14px',
            padding: '1rem 1.25rem',
            marginBottom: '1.75rem',
            color: '#fbbf24',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.75rem',
            flexWrap: 'wrap'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <AlertCircle size={20} style={{ flexShrink: 0 }} />
            <span style={{ fontSize: '0.9rem' }}>{error}</span>
          </div>
          <button
            onClick={() => loadCurated()}
            className="btn btn-secondary"
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.82rem', height: 'auto', minHeight: '32px' }}
          >
            <RefreshCw size={14} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="glass-card" style={{ padding: 'clamp(1rem, 2.5vw, 1.75rem)', marginBottom: '2rem', borderRadius: '18px' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 240px', position: 'relative' }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search concepts e.g. 'Operating systems scheduling'..."
              style={{ paddingLeft: '2.75rem', height: '48px', borderRadius: '14px' }}
            />
            <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          </div>

          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            style={{ width: 'auto', minWidth: '150px', flex: '1 1 150px', height: '48px', borderRadius: '14px' }}
          >
            <option value="Computer Science">Computer Science</option>
            <option value="Data Structures">Data Structures</option>
            <option value="Algorithms">Algorithms</option>
            <option value="Operating Systems">Operating Systems</option>
            <option value="DBMS">DBMS</option>
            <option value="Computer Networks">Computer Networks</option>
            <option value="Cybersecurity">Cybersecurity</option>
            <option value="Artificial Intelligence">AI & Machine Learning</option>
            <option value="Mathematics">Mathematics</option>
            <option value="Physics">Physics</option>
            <option value="Chemistry">Chemistry</option>
          </select>

          <button type="submit" disabled={loading} className="btn btn-primary" style={{ height: '48px', padding: '0 1.5rem', borderRadius: '14px', flex: '1 1 140px', justifyContent: 'center' }}>
            <Globe size={18} />
            <span>Search Web</span>
          </button>
        </form>
      </div>

      {/* Results */}
      {loading ? (
        <Loading3D message="Retrieving authentic academic web resources via Tavily..." />
      ) : resources.length === 0 ? (
        <div className="glass-card" style={{ padding: 'clamp(2rem, 4vw, 3.5rem) 1.5rem', textAlign: 'center', color: 'var(--text-muted)', borderRadius: '18px' }}>
          <Globe size={44} style={{ opacity: 0.3, marginBottom: '1rem' }} />
          <h3>No resources found.</h3>
          <p style={{ marginTop: '0.5rem', fontSize: '0.88rem' }}>Try refining your query or selecting another subject.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '1.25rem' }}>
          {resources.map((res, idx) => (
            <SourceBadge key={idx} source={res} />
          ))}
        </div>
      )}
    </div>
  );
}
