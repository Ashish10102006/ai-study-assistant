import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import Hero3DScene from '../components/3d/Hero3DScene';
import TopicCloud3D from '../components/3d/TopicCloud3D';
import HowItWorks3D from '../components/3d/HowItWorks3D';
import StudyCard3D from '../components/3d/StudyCard3D';
import SourceBadge from '../components/SourceBadge';
import { api } from '../services/api';
import {
  Sparkles,
  Send,
  Upload,
  Globe,
  BookOpen,
  HelpCircle,
  Award,
  Layers,
  CheckCircle2,
  ChevronRight,
  ArrowRight,
  ShieldCheck,
  Zap,
  GraduationCap,
  MessageSquare
} from 'lucide-react';

export default function Home() {
  const navigate = useNavigate();
  const [quickQuestion, setQuickQuestion] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('Computer Science');
  const [customTopic, setCustomTopic] = useState('');
  const [recentConversations, setRecentConversations] = useState([]);
  const [sampleResources, setSampleResources] = useState([]);
  const [loadingResources, setLoadingResources] = useState(false);

  useEffect(() => {
    // Fetch recent conversations
    api.get('/api/conversations')
      .then(data => setRecentConversations(data.slice(0, 4)))
      .catch(() => {});

    // Fetch live academic resources
    setLoadingResources(true);
    api.get('/api/resources', { subject: 'Computer Science', topic: 'Data Structures' })
      .then(data => setSampleResources(data.slice(0, 3)))
      .catch(() => {})
      .finally(() => setLoadingResources(false));
  }, []);

  const handleQuickAsk = (e) => {
    e.preventDefault();
    if (!quickQuestion.trim()) return;
    navigate('/study', {
      state: {
        initialQuestion: quickQuestion.trim(),
        subject: selectedSubject,
        customTopic: customTopic.trim() || undefined
      }
    });
  };

  const handleTopicSelect = (topicName) => {
    setSelectedSubject(topicName);
    setCustomTopic('');
    navigate('/study', { state: { subject: topicName } });
  };

  const handleCustomTopicSubmit = (topic) => {
    setCustomTopic(topic);
    navigate('/study', { state: { customTopic: topic, subject: 'Custom Field' } });
  };

  return (
    <div style={{ paddingBottom: '5rem' }}>
      {/* ==========================================================
          1. 3D HERO SECTION
          ========================================================== */}
      <section style={{ position: 'relative', overflow: 'hidden', padding: '3.5rem 0 2rem 0' }}>
        <div className="container">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))',
              gap: '2rem',
              alignItems: 'center'
            }}
          >
            {/* Hero Left Content */}
            <div>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.4rem 1rem',
                  borderRadius: '999px',
                  background: 'rgba(0, 242, 254, 0.08)',
                  border: '1px solid rgba(0, 242, 254, 0.25)',
                  marginBottom: '1.25rem'
                }}
              >
                <Sparkles size={16} color="var(--brand-cyan)" />
                <span style={{ fontSize: '0.82rem', fontWeight: '700', color: 'var(--brand-cyan)', letterSpacing: '0.04em' }}>
                  NEXT-GEN ACADEMIC LEARNING PLATFORM
                </span>
              </div>

              <h1
                style={{
                  fontFamily: 'Outfit',
                  fontSize: 'clamp(2.6rem, 5vw, 4.2rem)',
                  fontWeight: '800',
                  lineHeight: 1.1,
                  marginBottom: '1rem',
                  background: 'linear-gradient(135deg, #ffffff 40%, #a5b4fc 80%, #00f2fe 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}
              >
                AI STUDY ASSISTANT
              </h1>

              <div
                style={{
                  fontSize: '1.4rem',
                  fontWeight: '700',
                  color: 'var(--brand-cyan)',
                  marginBottom: '0.5rem',
                  letterSpacing: '-0.01em'
                }}
              >
                "Ask. Understand. Learn. Master."
              </div>

              <p
                style={{
                  fontSize: '1.15rem',
                  color: 'var(--text-secondary)',
                  marginBottom: '2rem',
                  lineHeight: '1.6',
                  maxWidth: '520px'
                }}
              >
                "Your Personal AI Study Companion." Transform difficult academic topics into crystal-clear explanations, grounded study notes, live web resources, and exam-grade quizzes.
              </p>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
                <Link to="/study" className="btn btn-primary btn-glow" style={{ padding: '0.85rem 1.75rem', fontSize: '1.05rem' }}>
                  <Sparkles size={20} />
                  <span>Start Learning</span>
                </Link>
                <Link to="/materials" className="btn btn-secondary" style={{ padding: '0.85rem 1.6rem', fontSize: '1.05rem' }}>
                  <Upload size={18} />
                  <span>Upload Notes / PDF</span>
                </Link>
              </div>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1.75rem',
                  marginTop: '2.5rem',
                  paddingTop: '1.5rem',
                  borderTop: '1px solid rgba(255, 255, 255, 0.08)'
                }}
              >
                <div>
                  <div style={{ fontWeight: '800', fontSize: '1.3rem', color: '#fff' }}>Gemini 2.5</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Deep Pedagogy</div>
                </div>
                <div style={{ width: '1px', height: '24px', background: 'rgba(255, 255, 255, 0.1)' }} />
                <div>
                  <div style={{ fontWeight: '800', fontSize: '1.3rem', color: '#fff' }}>Tavily API</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Live Academic Sources</div>
                </div>
                <div style={{ width: '1px', height: '24px', background: 'rgba(255, 255, 255, 0.1)' }} />
                <div>
                  <div style={{ fontWeight: '800', fontSize: '1.3rem', color: '#fff' }}>PostgreSQL</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Supabase RLS</div>
                </div>
              </div>
            </div>

            {/* Hero Right 3D Scene */}
            <div>
              <Hero3DScene />
            </div>
          </div>
        </div>
      </section>

      {/* ==========================================================
          2. AI STUDY ASSISTANT & 3. ASK YOUR QUESTION
          ========================================================== */}
      <section style={{ margin: '3.5rem 0' }}>
        <div className="container">
          <div
            className="glass-card"
            style={{
              padding: 'clamp(1.25rem, 3.5vw, 2.5rem)',
              border: '1px solid rgba(0, 242, 254, 0.2)',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5), 0 0 35px rgba(0, 242, 254, 0.1)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: 'var(--grad-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#030712',
                  flexShrink: 0
                }}
              >
                <Sparkles size={20} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.35rem', color: '#f8fafc' }}>Ask Your Academic Question</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                  Instant step-by-step breakdown, real-world analogies, or exam-oriented explanations.
                </p>
              </div>
            </div>

            <form onSubmit={handleQuickAsk}>
              <div
                style={{
                  display: 'flex',
                  gap: '0.75rem',
                  flexWrap: 'wrap'
                }}
              >
                <input
                  type="text"
                  value={quickQuestion}
                  onChange={(e) => setQuickQuestion(e.target.value)}
                  placeholder="e.g. Explain how B-Trees maintain logarithmic depth during node split..."
                  style={{
                    flex: '1 1 240px',
                    minHeight: '52px',
                    fontSize: '1rem',
                    borderRadius: '14px',
                    padding: '0 1.25rem',
                    background: 'rgba(7, 10, 16, 0.8)'
                  }}
                />
                <button
                  type="submit"
                  className="btn btn-primary btn-glow"
                  style={{
                    flex: '0 0 auto',
                    minHeight: '52px',
                    padding: '0 1.75rem',
                    borderRadius: '14px',
                    whiteSpace: 'nowrap',
                    width: 'auto'
                  }}
                >
                  <Send size={18} />
                  <span>Ask AI Assistant</span>
                </button>
              </div>
            </form>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.6rem', marginTop: '1.25rem', alignItems: 'center' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Popular questions:</span>
              {[
                'How does Dijkstra algorithm find shortest path?',
                'Difference between TCP and UDP',
                'Explain ACID properties with bank transfer',
                'Virtual memory paging vs segmentation'
              ].map((q, i) => (
                <button
                  key={i}
                  onClick={() => setQuickQuestion(q)}
                  style={{
                    fontSize: '0.78rem',
                    padding: '0.3rem 0.75rem',
                    borderRadius: '999px',
                    background: 'rgba(255, 255, 255, 0.04)',
                    color: 'var(--text-secondary)',
                    border: '1px solid rgba(255, 255, 255, 0.07)',
                    cursor: 'pointer'
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ==========================================================
          4. SELECT ACADEMIC TOPIC & 5. ENTER CUSTOM TOPIC
          ========================================================== */}
      <section className="container" style={{ margin: '4rem auto' }}>
        <TopicCloud3D
          selectedTopic={selectedSubject}
          onSelectTopic={handleTopicSelect}
          onCustomTopicSubmit={handleCustomTopicSubmit}
        />
      </section>

      {/* ==========================================================
          6. UPLOAD STUDY MATERIAL BANNER
          ========================================================== */}
      <section className="container" style={{ margin: '4rem auto' }}>
        <div
          className="glass-card"
          style={{
            padding: 'clamp(1.25rem, 3.5vw, 2.5rem)',
            background: 'linear-gradient(135deg, rgba(138, 43, 226, 0.15) 0%, rgba(13, 18, 29, 0.9) 100%)',
            border: '1px solid rgba(138, 43, 226, 0.3)',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1.5rem'
          }}
        >
          <div style={{ maxWidth: '600px' }}>
            <span className="badge badge-purple" style={{ marginBottom: '0.75rem' }}>
              Document-Grounded Q&A
            </span>
            <h3 style={{ fontSize: '1.8rem', marginBottom: '0.6rem', color: '#fff' }}>
              Study Directly From Your Course PDFs & Notes
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: '1.5' }}>
              Upload lecture slides, syllabus PDFs, or exam notes. AI Study Assistant extracts authentic text chunks and provides grounded summaries, practice quizzes, and direct answers without hallucination.
            </p>
          </div>
          <Link to="/materials" className="btn btn-primary" style={{ padding: '0.9rem 1.8rem', borderRadius: '14px', flex: '0 0 auto' }}>
            <Upload size={18} />
            <span>Upload Document</span>
          </Link>
        </div>
      </section>

      {/* ==========================================================
          7. WEB LEARNING RESOURCES (TAVILY)
          ========================================================== */}
      <section className="container" style={{ margin: '4rem auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <span className="badge badge-cyan" style={{ marginBottom: '0.5rem' }}>
              Live Knowledge Integration
            </span>
            <h2 style={{ fontSize: '2rem' }}>Verified Web Learning Resources</h2>
            <p style={{ color: 'var(--text-secondary)' }}>
              Real academic references retrieved via Tavily. Zero fabricated URLs or links.
            </p>
          </div>
          <Link to="/resources" style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--brand-cyan)', fontWeight: '600', fontSize: '0.9rem', minHeight: '44px' }}>
            <span>Search All Resources</span>
            <ArrowRight size={16} />
          </Link>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: '1.25rem' }}>
          {sampleResources.map((src, idx) => (
            <SourceBadge key={idx} source={src} />
          ))}
        </div>
      </section>

      {/* ==========================================================
          8. RECENT CONVERSATIONS
          ========================================================== */}
      {recentConversations.length > 0 && (
        <section className="container" style={{ margin: '4rem auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.4rem' }}>Recent Study Sessions</h3>
            <Link to="/conversations" style={{ color: 'var(--brand-cyan)', fontSize: '0.9rem', fontWeight: '600' }}>
              View All History →
            </Link>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))', gap: '1rem' }}>
            {recentConversations.map((c) => (
              <div
                key={c.id}
                onClick={() => navigate(`/chat/${c.id}`)}
                className="glass-card"
                style={{
                  padding: '1.25rem',
                  cursor: 'pointer',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.85rem'
                }}
              >
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '10px',
                    background: 'rgba(0, 242, 254, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--brand-cyan)'
                  }}
                >
                  <MessageSquare size={20} />
                </div>
                <div style={{ overflow: 'hidden' }}>
                  <div style={{ fontWeight: '600', fontSize: '0.95rem', color: '#f8fafc', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    {c.title}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    {c.subject || 'Academic Study'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ==========================================================
          9. STUDY TOOLS (3D CARDS)
          ========================================================== */}
      <section className="container" style={{ margin: '5rem auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <span className="badge badge-emerald" style={{ marginBottom: '0.75rem' }}>
            Targeted Pedagogy Suite
          </span>
          <h2 style={{ fontSize: '2.2rem', marginBottom: '0.5rem' }}>
            Specialized AI Academic Study Tools
          </h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
            Select the exact cognitive tool designed for your study phase.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '1.5rem' }}>
          <StudyCard3D
            title="Explain Simply"
            subtitle="Complex theoretical proofs and algorithms broken down using intuitive real-life analogies and plain language."
            icon="💡"
            badge="Intuition"
            accentColor="#00f2fe"
            onClick={() => navigate('/study?mode=simple')}
          />
          <StudyCard3D
            title="Step-by-Step Breakdown"
            subtitle="Sequential algorithmic execution, mathematical derivations, or protocol handshakes with numbered stages."
            icon="🪜"
            badge="Clarity"
            accentColor="#38bdf8"
            onClick={() => navigate('/study?mode=step_by_step')}
          />
          <StudyCard3D
            title="Generate Study Notes"
            subtitle="Structured Markdown notes with definitions, architectural diagrams, formulas, and high-yield checklists."
            icon="📝"
            badge="Synthesis"
            accentColor="#8a2be2"
            onClick={() => navigate('/study?tab=notes')}
          />
          <StudyCard3D
            title="Interactive Quiz Arena"
            subtitle="Instant MCQ quizzes with pedagogical explanations for correct options and counter-explanations for distractors."
            icon="🎯"
            badge="Recall"
            accentColor="#f72585"
            onClick={() => navigate('/study?tab=quiz')}
          />
          <StudyCard3D
            title="Practice Problem Sets"
            subtitle="Exam-style problem sets, edge case scenarios, and numerical problems with progressive hints."
            icon="🧠"
            badge="Mastery"
            accentColor="#10b981"
            onClick={() => navigate('/study?tab=questions')}
          />
          <StudyCard3D
            title="Revision Mode"
            subtitle="High-yield 5-minute revision summaries focused on exam traps, memory mnemonics, and contrast tables."
            icon="⚡"
            badge="Exam Prep"
            accentColor="#f59e0b"
            onClick={() => navigate('/study?mode=revision')}
          />
        </div>
      </section>

      {/* ==========================================================
          10. HOW AI STUDY ASSISTANT WORKS (3D FLOW)
          ========================================================== */}
      <section className="container">
        <HowItWorks3D />
      </section>

      {/* ==========================================================
          11. WHY AI STUDY ASSISTANT
          ========================================================== */}
      <section className="container" style={{ margin: '5rem auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
          <h2 style={{ fontSize: '2.2rem', marginBottom: '0.5rem' }}>
            Why Students Trust AI Study Assistant
          </h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
            Engineered specifically for academic rigor, verifiable citations, and deep student learning.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '1.5rem' }}>
          <div className="glass-card" style={{ padding: 'clamp(1.25rem, 3vw, 2rem)' }}>
            <ShieldCheck size={32} color="#10b981" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: '#fff' }}>
              Zero Hallucinations Policy
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
              Web resources strictly come from authentic live Tavily queries. Documents are parsed directly using pypdf. We never invent fake sources or URLs.
            </p>
          </div>

          <div className="glass-card" style={{ padding: 'clamp(1.25rem, 3vw, 2rem)' }}>
            <Zap size={32} color="#00f2fe" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: '#fff' }}>
              Powered by Gemini 2.5 Flash
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
              Sub-second response latency with modern pedagogical models. Capable of reasoning over intricate mathematical logic and advanced software architectures.
            </p>
          </div>

          <div className="glass-card" style={{ padding: 'clamp(1.25rem, 3vw, 2rem)' }}>
            <GraduationCap size={32} color="#8a2be2" style={{ marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: '#fff' }}>
              Student-Centered Privacy
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
              Your notes, chat history, and academic profile are protected with Supabase Row Level Security. No student can access another student's data.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
