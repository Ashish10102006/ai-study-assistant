import React, { useState } from 'react';
import { Search, Sparkles, PlusCircle } from 'lucide-react';

const STANDARD_TOPICS = [
  { id: 'cs', name: 'Computer Science', category: 'Core' },
  { id: 'prog', name: 'Programming', category: 'Core' },
  { id: 'dsa', name: 'Data Structures', category: 'Algorithms' },
  { id: 'algo', name: 'Algorithms', category: 'Algorithms' },
  { id: 'dbms', name: 'DBMS', category: 'Systems' },
  { id: 'os', name: 'Operating Systems', category: 'Systems' },
  { id: 'cn', name: 'Computer Networks', category: 'Systems' },
  { id: 'sec', name: 'Cybersecurity', category: 'Security' },
  { id: 'ai', name: 'Artificial Intelligence', category: 'AI/ML' },
  { id: 'ml', name: 'Machine Learning', category: 'AI/ML' },
  { id: 'math', name: 'Mathematics', category: 'Science' },
  { id: 'phys', name: 'Physics', category: 'Science' },
  { id: 'chem', name: 'Chemistry', category: 'Science' },
  { id: 'other', name: 'Other Subject', category: 'General' },
];

export default function TopicCloud3D({ selectedTopic, onSelectTopic, onCustomTopicSubmit }) {
  const [customInput, setCustomInput] = useState('');
  const [showCustomModal, setShowCustomModal] = useState(false);

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (!customInput.trim()) return;
    if (onCustomTopicSubmit) {
      onCustomTopicSubmit(customInput.trim());
    }
    setCustomInput('');
    setShowCustomModal(false);
  };

  return (
    <div style={{ position: 'relative', width: '100%', margin: '2rem 0' }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <span className="badge badge-purple" style={{ marginBottom: '0.75rem' }}>
          Interactive Academic Cloud
        </span>
        <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
          Explore Academic Subjects & Custom Topics
        </h2>
        <p style={{ color: 'var(--text-secondary)', maxWidth: '650px', margin: '0 auto' }}>
          Select any standard foundational field or type your specific syllabus topic, exam question, or research paper subject.
        </p>
      </div>

      {/* Grid of 3D Topic Pills */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.85rem',
          justifyContent: 'center',
          alignItems: 'center',
          maxWidth: '1000px',
          margin: '0 auto'
        }}
      >
        {STANDARD_TOPICS.map((topic) => {
          const isSelected = selectedTopic === topic.name;
          return (
            <button
              key={topic.id}
              onClick={() => onSelectTopic(topic.name)}
              style={{
                background: isSelected
                  ? 'var(--grad-primary)'
                  : 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%)',
                color: isSelected ? '#030712' : '#e2e8f0',
                border: `1px solid ${isSelected ? '#00f2fe' : 'rgba(255, 255, 255, 0.1)'}`,
                borderRadius: '999px',
                padding: '0.65rem 1.35rem',
                fontSize: '0.92rem',
                fontWeight: isSelected ? '700' : '500',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                cursor: 'pointer',
                transition: 'all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)',
                transform: isSelected ? 'scale(1.05) translateY(-3px)' : 'scale(1)',
                boxShadow: isSelected
                  ? '0 10px 25px rgba(0, 242, 254, 0.4)'
                  : '0 4px 12px rgba(0,0,0,0.2)'
              }}
              onMouseEnter={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.transform = 'translateY(-3px) scale(1.03)';
                  e.currentTarget.style.borderColor = 'rgba(0, 242, 254, 0.4)';
                  e.currentTarget.style.boxShadow = '0 8px 20px rgba(0, 242, 254, 0.15)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isSelected) {
                  e.currentTarget.style.transform = 'scale(1)';
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
                }
              }}
            >
              <span>{topic.name}</span>
            </button>
          );
        })}

        {/* Highlighted "Enter Your Own Topic" Action */}
        <button
          onClick={() => setShowCustomModal(true)}
          style={{
            background: 'linear-gradient(135deg, rgba(138, 43, 226, 0.25) 0%, rgba(247, 37, 133, 0.25) 100%)',
            color: '#f8fafc',
            border: '1px solid rgba(247, 37, 133, 0.5)',
            borderRadius: '999px',
            padding: '0.65rem 1.45rem',
            fontSize: '0.92rem',
            fontWeight: '600',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            cursor: 'pointer',
            transition: 'all 0.25s ease',
            boxShadow: '0 0 20px rgba(247, 37, 133, 0.2)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.05) translateY(-3px)';
            e.currentTarget.style.boxShadow = '0 10px 25px rgba(247, 37, 133, 0.4)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = '0 0 20px rgba(247, 37, 133, 0.2)';
          }}
        >
          <Sparkles size={16} color="#f72585" />
          <span>Enter Your Own Topic</span>
          <PlusCircle size={16} />
        </button>
      </div>

      {/* Custom Topic Quick Input Bar */}
      <div style={{ maxWidth: '680px', margin: '2rem auto 0 auto' }}>
        <form onSubmit={handleCustomSubmit} style={{ display: 'flex', gap: '0.75rem' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <input
              type="text"
              value={customInput}
              onChange={(e) => setCustomInput(e.target.value)}
              placeholder="e.g. TCP three-way handshake, Normalization in DBMS, Newton's second law..."
              style={{
                paddingLeft: '2.75rem',
                height: '52px',
                borderRadius: '16px',
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                color: '#fff',
                width: '100%',
                fontSize: '0.95rem'
              }}
            />
            <Search
              size={18}
              style={{
                position: 'absolute',
                left: '1rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)'
              }}
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ height: '52px', padding: '0 1.5rem', borderRadius: '16px', whiteSpace: 'nowrap' }}
          >
            Study Topic
          </button>
        </form>
      </div>
    </div>
  );
}
