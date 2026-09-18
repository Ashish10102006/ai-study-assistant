import React from 'react';
import { Link } from 'react-router-dom';
import { Brain, Sparkles, Globe, Shield, Terminal } from 'lucide-react';

export default function Footer() {
  return (
    <footer
      style={{
        borderTop: '1px solid var(--border-subtle)',
        background: 'rgba(5, 7, 11, 0.95)',
        padding: '4rem 0 2rem 0',
        marginTop: 'auto'
      }}
    >
      <div className="container">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))',
            gap: '2.5rem',
            marginBottom: '3rem'
          }}
        >
          {/* Brand Col */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1rem' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  background: 'var(--grad-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#030712'
                }}
              >
                <Brain size={20} />
              </div>
              <span style={{ fontFamily: 'Outfit', fontWeight: '800', fontSize: '1.2rem', color: '#fff' }}>
                AI STUDY <span style={{ color: 'var(--brand-cyan)' }}>ASSISTANT</span>
              </span>
            </div>
            <p style={{ fontSize: '0.95rem', fontWeight: '600', color: '#f8fafc', marginBottom: '0.4rem' }}>
              "Ask. Understand. Learn. Master."
            </p>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
              "Your Personal AI Study Companion." Built for scholars to master complex academic topics with grounded Gemini AI and verified web learning resources.
            </p>
          </div>

          {/* Quick Learning Tools */}
          <div>
            <h4 style={{ fontSize: '1rem', color: '#f8fafc', marginBottom: '1.2rem' }}>
              Study Tools
            </h4>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <li><Link to="/study?mode=simple" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Explain Simply</Link></li>
              <li><Link to="/study?mode=step_by_step" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Step-by-Step Breakdown</Link></li>
              <li><Link to="/study?tab=notes" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Generate Study Notes</Link></li>
              <li><Link to="/study?tab=quiz" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Interactive Quiz Arena</Link></li>
              <li><Link to="/study?tab=questions" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Exam Practice Problems</Link></li>
            </ul>
          </div>

          {/* Subjects */}
          <div>
            <h4 style={{ fontSize: '1rem', color: '#f8fafc', marginBottom: '1.2rem' }}>
              Academic Fields
            </h4>
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
              <li><Link to="/study?subject=Computer Science" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Computer Science & Coding</Link></li>
              <li><Link to="/study?subject=Operating Systems" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Operating Systems & Networks</Link></li>
              <li><Link to="/study?subject=DBMS" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Database Management Systems</Link></li>
              <li><Link to="/study?subject=Artificial Intelligence" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>AI & Machine Learning</Link></li>
              <li><Link to="/study?subject=Mathematics" style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Discrete Mathematics & Physics</Link></li>
            </ul>
          </div>

          {/* Platform & Trust */}
          <div>
            <h4 style={{ fontSize: '1rem', color: '#f8fafc', marginBottom: '1.2rem' }}>
              Architecture & Trust
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sparkles size={16} color="var(--brand-cyan)" />
                <span>Powered by Google Gemini 2.5 Flash</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Globe size={16} color="#4facfe" />
                <span>Verified Tavily Web Resources</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Shield size={16} color="#10b981" />
                <span>Supabase PostgreSQL + RLS Protected</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom copyright */}
        <div
          style={{
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '1.75rem',
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.82rem',
            color: 'var(--text-muted)'
          }}
        >
          <div>
            © {new Date().getFullYear()} AI STUDY ASSISTANT. Built for student excellence. Real data, zero hallucinations.
          </div>
          <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.5rem' }}>
            <span>Privacy & RLS</span>
            <span>Terms of Study</span>
            <span>Security Status: Active</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
