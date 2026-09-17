import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import {
  MessageSquare,
  Trash2,
  Edit2,
  Plus,
  Search,
  Calendar,
  Sparkles,
  ArrowRight
} from 'lucide-react';

export default function ConversationsList() {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const data = await api.get('/api/conversations');
      setConversations(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;
    try {
      await api.delete(`/api/conversations/${id}`);
      setConversations(prev => prev.filter(c => c.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const handleStartRename = (e, conv) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const handleSaveRename = async (e, id) => {
    e.stopPropagation();
    if (!editTitle.trim()) return;
    try {
      await api.patch(`/api/conversations/${id}`, { title: editTitle.trim() });
      setConversations(prev => prev.map(c => c.id === id ? { ...c, title: editTitle.trim() } : c));
      setEditingId(null);
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = conversations.filter(c =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (c.subject && c.subject.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="container" style={{ padding: '3rem 1.5rem', minHeight: '85vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <span className="badge badge-cyan" style={{ marginBottom: '0.6rem' }}>
            Academic Dialogue History
          </span>
          <h1 style={{ fontSize: '2.4rem', color: '#fff' }}>
            Conversations
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Review, resume, or rename previous study dialogues and question threads.
          </p>
        </div>

        <Link to="/study" className="btn btn-primary">
          <Plus size={18} />
          <span>New Study Session</span>
        </Link>
      </div>

      {/* Search Bar */}
      <div style={{ position: 'relative', maxWidth: '450px', marginBottom: '2rem' }}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search conversations by title or subject..."
          style={{ paddingLeft: '2.5rem', borderRadius: '12px' }}
        />
        <Search size={16} style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
      </div>

      {/* Conversations Grid */}
      {filtered.length === 0 ? (
        <div className="glass-card" style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          <MessageSquare size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
          <h3 style={{ fontSize: '1.2rem', color: '#fff', marginBottom: '0.5rem' }}>
            No conversations yet.
          </h3>
          <p style={{ fontSize: '0.9rem', marginBottom: '1.5rem' }}>
            Ask your first academic question and start learning.
          </p>
          <Link to="/study" className="btn btn-primary">
            <Sparkles size={16} />
            <span>Ask a Question Now</span>
          </Link>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {filtered.map(conv => (
            <div
              key={conv.id}
              onClick={() => navigate(`/chat/${conv.id}`)}
              className="glass-card"
              style={{
                padding: '1.5rem',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.2s ease'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>
                    {conv.subject || 'Academic Study'}
                  </span>
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <button
                      onClick={(e) => handleStartRename(e, conv)}
                      title="Rename"
                      style={{ padding: '0.35rem', color: 'var(--text-muted)' }}
                    >
                      <Edit2 size={15} />
                    </button>
                    <button
                      onClick={(e) => handleDelete(e, conv.id)}
                      title="Delete"
                      style={{ padding: '0.35rem', color: 'var(--text-muted)' }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = '#ef4444'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--text-muted)'; }}
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>

                {editingId === conv.id ? (
                  <div onClick={(e) => e.stopPropagation()} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      style={{ fontSize: '0.9rem', padding: '0.4rem 0.6rem' }}
                    />
                    <button onClick={(e) => handleSaveRename(e, conv.id)} className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
                      Save
                    </button>
                  </div>
                ) : (
                  <h3 style={{ fontSize: '1.15rem', color: '#f8fafc', marginBottom: '0.5rem', lineHeight: '1.35' }}>
                    {conv.title}
                  </h3>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1.25rem', paddingTop: '0.85rem', borderTop: '1px solid rgba(255, 255, 255, 0.06)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: 'var(--brand-cyan)' }}>
                  Continue <ArrowRight size={13} />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
