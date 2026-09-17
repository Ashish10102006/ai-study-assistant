import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import SourceBadge from '../components/SourceBadge';
import Loading3D from '../components/3d/Loading3D';
import { Search, Globe, Filter, Bookmark, ExternalLink } from 'lucide-react';

export default function LearningResources() {
  const [query, setQuery] = useState('');
  const [subject, setSubject] = useState('Computer Science');
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    // Initial load of curated resources
    loadCurated();
  }, [subject]);

  const loadCurated = async () => {
    setLoading(true);
    try {
      const data = await api.get('/api/resources', { subject, topic: 'Fundamental Concepts' });
      setResources(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const data = await api.post('/api/search', {
        query: query.trim(),
        subject,
        max_results: 8
      });
      setResources(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container" style={{ padding: '3rem 1.5rem', minHeight: '85vh' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <span className="badge badge-cyan" style={{ marginBottom: '0.6rem' }}>
          Tavily Academic Discovery
        </span>
        <h1 style={{ fontSize: '2.4rem', color: '#fff', marginBottom: '0.5rem' }}>
          Web Learning Resources
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', maxWidth: '650px' }}>
          Search official documentation, university lecture portals, research papers, and verified study tutorials.
        </p>
      </div>

      {/* Search & Filter Bar */}
      <div className="glass-card" style={{ padding: '1.75rem', marginBottom: '2.5rem' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 300px', position: 'relative' }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search concepts e.g. 'Operating systems scheduling algorithms', 'B-tree implementation'..."
              style={{ paddingLeft: '2.75rem', height: '52px', borderRadius: '14px' }}
            />
            <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          </div>

          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            style={{ width: 'auto', minWidth: '180px', height: '52px', borderRadius: '14px' }}
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

          <button type="submit" disabled={loading} className="btn btn-primary" style={{ height: '52px', padding: '0 1.75rem', borderRadius: '14px' }}>
            <Globe size={18} />
            <span>Search Web</span>
          </button>
        </form>
      </div>

      {/* Results */}
      {loading ? (
        <Loading3D message="Retrieving authentic academic web resources via Tavily..." />
      ) : resources.length === 0 ? (
        <div className="glass-card" style={{ padding: '3.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <Globe size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
          <h3>No resources found.</h3>
          <p style={{ marginTop: '0.5rem' }}>Try refining your query or selecting another subject.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {resources.map((res, idx) => (
            <SourceBadge key={idx} source={res} />
          ))}
        </div>
      )}
    </div>
  );
}
