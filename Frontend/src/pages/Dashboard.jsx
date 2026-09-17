import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import StudyCard3D from '../components/3d/StudyCard3D';
import {
  Sparkles,
  BookOpen,
  MessageSquare,
  FileText,
  Bookmark,
  Send,
  Upload,
  ArrowRight,
  HelpCircle,
  Award,
  Layers,
  CheckCircle2,
  Trash2
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [conversations, setConversations] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [savedResources, setSavedResources] = useState([]);
  const [profile, setProfile] = useState(null);
  const [quickQuery, setQuickQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/api/conversations').catch(() => []),
      api.get('/api/documents').catch(() => []),
      api.get('/api/resources/saved').catch(() => []),
      api.get('/api/profile').catch(() => null)
    ]).then(([convs, docs, resources, prof]) => {
      setConversations(convs);
      setDocuments(docs);
      setSavedResources(resources);
      setProfile(prof);
      setLoading(false);
    });
  }, []);

  const handleAskSubmit = (e) => {
    e.preventDefault();
    if (!quickQuery.trim()) return;
    navigate('/study', { state: { initialQuestion: quickQuery.trim() } });
  };

  const studentName = profile?.full_name || user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'Scholar';

  return (
    <div className="container" style={{ padding: '3rem 1.5rem', minHeight: '85vh' }}>
      {/* ==========================================================
          1. WELCOME BACK BANNER
          ========================================================== */}
      <div
        className="glass-card"
        style={{
          padding: '2.5rem',
          marginBottom: '2.5rem',
          background: 'linear-gradient(135deg, rgba(13, 20, 34, 0.9) 0%, rgba(19, 27, 44, 0.7) 100%)',
          border: '1px solid rgba(0, 242, 254, 0.25)',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '1.5rem'
        }}
      >
        <div>
          <span className="badge badge-cyan" style={{ marginBottom: '0.6rem' }}>
            Student Learning Command Center
          </span>
          <h1 style={{ fontSize: '2.2rem', marginBottom: '0.4rem', color: '#fff' }}>
            Welcome Back, {studentName}! 🎓
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem' }}>
            "Ask. Understand. Learn. Master." Ready for your next study milestone?
          </p>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <span>🏫 {profile?.college || 'Engineering College'}</span>
            <span>📚 {profile?.course || 'Computer Science'}</span>
            <span>🗓️ {profile?.year || '3rd Year'}</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <Link to="/study" className="btn btn-primary btn-glow" style={{ padding: '0.75rem 1.5rem' }}>
            <Sparkles size={18} />
            <span>Open AI Assistant</span>
          </Link>
          <Link to="/materials" className="btn btn-secondary" style={{ padding: '0.75rem 1.4rem' }}>
            <Upload size={18} />
            <span>Upload Notes</span>
          </Link>
        </div>
      </div>

      {/* ==========================================================
          2. ASK AI QUICK LAUNCHER
          ========================================================== */}
      <div className="glass-card" style={{ padding: '1.75rem', marginBottom: '2.5rem' }}>
        <form onSubmit={handleAskSubmit} style={{ display: 'flex', gap: '0.75rem' }}>
          <input
            type="text"
            value={quickQuery}
            onChange={(e) => setQuickQuery(e.target.value)}
            placeholder="Ask any academic question to start an instant study session..."
            style={{ borderRadius: '14px', height: '52px', fontSize: '1rem' }}
          />
          <button type="submit" className="btn btn-primary" style={{ height: '52px', padding: '0 1.75rem', borderRadius: '14px' }}>
            <Send size={18} />
            <span>Ask AI</span>
          </button>
        </form>
      </div>

      {/* Grid: 2 Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem', marginBottom: '3rem' }}>
        {/* ==========================================================
            3. RECENT CONVERSATIONS
            ========================================================== */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--brand-cyan)' }}>
              <MessageSquare size={20} />
              <h3 style={{ fontSize: '1.25rem', color: '#fff' }}>Recent Conversations</h3>
            </div>
            <Link to="/conversations" style={{ fontSize: '0.85rem', color: 'var(--brand-cyan)', fontWeight: '600' }}>
              View All →
            </Link>
          </div>

          {conversations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-muted)' }}>
              <p>No conversations yet.</p>
              <Link to="/study" style={{ color: 'var(--brand-cyan)', fontSize: '0.9rem', marginTop: '0.5rem', display: 'inline-block' }}>
                Ask your first academic question and start learning.
              </Link>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {conversations.slice(0, 4).map(c => (
                <div
                  key={c.id}
                  onClick={() => navigate(`/chat/${c.id}`)}
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ overflow: 'hidden' }}>
                    <div style={{ fontWeight: '600', color: '#f8fafc', fontSize: '0.92rem', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {c.title}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {c.subject || 'General'}
                    </div>
                  </div>
                  <ArrowRight size={16} color="var(--text-muted)" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ==========================================================
            4. STUDY MATERIALS & PDFS
            ========================================================== */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#c084fc' }}>
              <FileText size={20} />
              <h3 style={{ fontSize: '1.25rem', color: '#fff' }}>Uploaded Notes & PDFs</h3>
            </div>
            <Link to="/materials" style={{ fontSize: '0.85rem', color: '#c084fc', fontWeight: '600' }}>
              Manage Files →
            </Link>
          </div>

          {documents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-muted)' }}>
              <p>No study materials uploaded yet.</p>
              <Link to="/materials" style={{ color: 'var(--brand-cyan)', fontSize: '0.9rem', marginTop: '0.5rem', display: 'inline-block' }}>
                Upload your notes or PDF to study with AI.
              </Link>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {documents.slice(0, 4).map(d => (
                <div
                  key={d.id}
                  onClick={() => navigate(`/materials/${d.id}`)}
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: '600', color: '#f8fafc', fontSize: '0.92rem' }}>
                      📄 {d.file_name}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {d.chunks_count} chunks • Status: {d.processing_status}
                    </div>
                  </div>
                  <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>
                    Grounded
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ==========================================================
          5. SAVED RESOURCES & ACADEMIC INTERESTS
          ========================================================== */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2rem', marginBottom: '3rem' }}>
        {/* Saved Bookmarks */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981' }}>
              <Bookmark size={20} />
              <h3 style={{ fontSize: '1.25rem', color: '#fff' }}>Saved Web Resources</h3>
            </div>
            <Link to="/saved" style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: '600' }}>
              View Bookmarks →
            </Link>
          </div>

          {savedResources.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-muted)' }}>
              <p>No saved resources yet.</p>
              <Link to="/resources" style={{ color: 'var(--brand-cyan)', fontSize: '0.9rem', marginTop: '0.5rem', display: 'inline-block' }}>
                Save useful learning resources for later.
              </Link>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {savedResources.slice(0, 3).map(r => (
                <a
                  key={r.id}
                  href={r.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: '12px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                    display: 'block'
                  }}
                >
                  <div style={{ fontWeight: '600', color: '#f8fafc', fontSize: '0.92rem' }}>
                    {r.title}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--brand-cyan)' }}>
                    {r.source}
                  </div>
                </a>
              ))}
            </div>
          )}
        </div>

        {/* Academic Interests */}
        <div className="glass-card" style={{ padding: '1.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f59e0b' }}>
              <Award size={20} />
              <h3 style={{ fontSize: '1.25rem', color: '#fff' }}>Your Academic Interests</h3>
            </div>
            <Link to="/profile" style={{ fontSize: '0.85rem', color: '#f59e0b', fontWeight: '600' }}>
              Edit Interests →
            </Link>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem' }}>
            {(profile?.interests && profile.interests.length > 0
              ? profile.interests
              : ['Algorithms', 'Data Structures', 'Operating Systems', 'Computer Networks', 'Artificial Intelligence']
            ).map((item, idx) => (
              <span
                key={idx}
                onClick={() => navigate('/study', { state: { subject: item } })}
                style={{
                  padding: '0.4rem 0.85rem',
                  borderRadius: '999px',
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  fontSize: '0.85rem',
                  color: '#e2e8f0',
                  cursor: 'pointer'
                }}
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ==========================================================
          6. STUDY TOOLS SUITE
          ========================================================== */}
      <div>
        <h3 style={{ fontSize: '1.5rem', marginBottom: '1.5rem', color: '#fff' }}>
          Academic Study Tools
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.25rem' }}>
          <StudyCard3D
            title="Explain Concept"
            subtitle="Understand tough subjects in simple, intuitive student language."
            icon="💡"
            badge="Simple"
            accentColor="#00f2fe"
            onClick={() => navigate('/study?mode=simple')}
          />
          <StudyCard3D
            title="Generate Notes"
            subtitle="Synthesize structured exam notes with definitions and formulas."
            icon="📝"
            badge="Notes"
            accentColor="#8a2be2"
            onClick={() => navigate('/study?tab=notes')}
          />
          <StudyCard3D
            title="Take AI Quiz"
            subtitle="Test active recall with auto-graded conceptual questions."
            icon="🎯"
            badge="Quiz"
            accentColor="#f72585"
            onClick={() => navigate('/study?tab=quiz')}
          />
          <StudyCard3D
            title="Practice Problems"
            subtitle="Solve exam problems with step-by-step guidance."
            icon="🧠"
            badge="Problems"
            accentColor="#10b981"
            onClick={() => navigate('/study?tab=questions')}
          />
        </div>
      </div>
    </div>
  );
}
