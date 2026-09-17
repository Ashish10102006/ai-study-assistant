import React, { useState } from 'react';
import { HelpCircle, Brain, Globe, FileSearch, Sparkles, Award } from 'lucide-react';

const STEPS = [
  {
    step: 1,
    key: 'ASK',
    title: 'Ask Question',
    desc: 'Enter any academic question, select your subject, or type a custom topic.',
    icon: <HelpCircle size={24} color="#00f2fe" />,
    color: '#00f2fe'
  },
  {
    step: 2,
    key: 'UNDERSTAND',
    title: 'Cognitive Parsing',
    desc: 'Gemini evaluates semantic intent, academic depth, and prerequisite concepts.',
    icon: <Brain size={24} color="#38bdf8" />,
    color: '#38bdf8'
  },
  {
    step: 3,
    key: 'SEARCH',
    title: 'Tavily Discovery',
    desc: 'Intelligently retrieves verified papers, official docs, and academic portals when needed.',
    icon: <Globe size={24} color="#818cf8" />,
    color: '#818cf8'
  },
  {
    step: 4,
    key: 'ANALYZE',
    title: 'Document Synthesis',
    desc: 'Integrates uploaded PDF notes, lecture slides, or textbook chapters.',
    icon: <FileSearch size={24} color="#c084fc" />,
    color: '#c084fc'
  },
  {
    step: 5,
    key: 'EXPLAIN',
    title: 'Tailored Explanation',
    desc: 'Delivers clear explanations formatted for your preferred style (Simple, Step-by-Step, Exam).',
    icon: <Sparkles size={24} color="#f472b6" />,
    color: '#f472b6'
  },
  {
    step: 6,
    key: 'LEARN',
    title: 'Master & Practice',
    desc: 'Reinforce with interactive AI quizzes, practice problem sets, and cheat-sheets.',
    icon: <Award size={24} color="#10b981" />,
    color: '#10b981'
  }
];

export default function HowItWorks3D() {
  const [activeStep, setActiveStep] = useState(1);

  return (
    <div style={{ width: '100%', margin: '4rem 0' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <span className="badge badge-cyan" style={{ marginBottom: '0.75rem' }}>
          Intelligent Learning Pipeline
        </span>
        <h2 style={{ fontSize: '2.2rem', marginBottom: '0.5rem' }}>
          How AI Study Assistant Works
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '600px', margin: '0 auto' }}>
          From initial question to deep mastery in 6 transparent, grounded steps.
        </p>
      </div>

      {/* Interactive Process Pipeline */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
          gap: '1.25rem',
          position: 'relative'
        }}
      >
        {STEPS.map((s) => {
          const isActive = activeStep === s.step;
          return (
            <div
              key={s.step}
              onClick={() => setActiveStep(s.step)}
              style={{
                background: isActive
                  ? 'linear-gradient(145deg, rgba(25, 34, 54, 0.95) 0%, rgba(13, 18, 29, 0.95) 100%)'
                  : 'rgba(15, 22, 36, 0.5)',
                border: `1px solid ${isActive ? s.color : 'rgba(255, 255, 255, 0.08)'}`,
                borderRadius: '18px',
                padding: '1.5rem 1.25rem',
                cursor: 'pointer',
                transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
                transform: isActive ? 'translateY(-6px) scale(1.02)' : 'translateY(0)',
                boxShadow: isActive ? `0 12px 30px -5px ${s.color}35` : 'none',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center',
                position: 'relative'
              }}
            >
              {/* Step number badge */}
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  background: `${s.color}20`,
                  border: `1px solid ${s.color}50`,
                  color: s.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '700',
                  fontSize: '0.85rem',
                  marginBottom: '1rem'
                }}
              >
                {s.step}
              </div>

              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '16px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '1rem'
                }}
              >
                {s.icon}
              </div>

              <h4 style={{ fontSize: '1.05rem', color: '#f8fafc', marginBottom: '0.5rem' }}>
                {s.key}
              </h4>
              <div style={{ fontSize: '0.82rem', fontWeight: '600', color: s.color, marginBottom: '0.5rem' }}>
                {s.title}
              </div>
              <p style={{ fontSize: '0.78rem', color: '#94a3b8', lineHeight: '1.4' }}>
                {s.desc}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
