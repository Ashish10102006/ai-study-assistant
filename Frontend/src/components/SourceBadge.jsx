import React, { useState } from 'react';
import { ExternalLink, Bookmark, Check } from 'lucide-react';
import { api } from '../services/api';

export default function SourceBadge({ source, onSaveSuccess }) {
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSave = async (e) => {
    e.stopPropagation();
    if (saved || saving) return;
    setSaving(true);
    try {
      await api.post('/api/resources/save', {
        title: source.title,
        url: source.url,
        source: source.domain,
        description: source.description
      });
      setSaved(true);
      if (onSaveSuccess) onSaveSuccess(source);
    } catch (err) {
      console.error('Failed to save resource:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      style={{
        background: 'rgba(15, 23, 42, 0.75)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '12px',
        padding: '0.85rem 1rem',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: '0.5rem',
        transition: 'all var(--transition-fast)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'rgba(0, 242, 254, 0.35)';
        e.currentTarget.style.transform = 'translateY(-2px)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
        e.currentTarget.style.transform = 'translateY(0)';
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: 'var(--brand-cyan)',
              background: 'rgba(0, 242, 254, 0.1)',
              padding: '0.15rem 0.5rem',
              borderRadius: '6px'
            }}
          >
            {source.domain}
          </span>
          <button
            onClick={handleSave}
            title={saved ? "Saved to Bookmarks" : "Save Resource"}
            style={{
              color: saved ? '#10b981' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
              fontSize: '0.75rem',
              padding: '0.2rem 0.4rem',
              borderRadius: '6px',
              background: saved ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255, 255, 255, 0.05)',
              border: `1px solid ${saved ? 'rgba(16, 185, 129, 0.3)' : 'transparent'}`
            }}
          >
            {saved ? <Check size={13} /> : <Bookmark size={13} />}
            <span>{saved ? 'Saved' : 'Bookmark'}</span>
          </button>
        </div>

        <a
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            fontSize: '0.92rem',
            fontWeight: '600',
            color: '#f8fafc',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            lineHeight: '1.3',
            wordBreak: 'break-word',
            overflowWrap: 'anywhere'
          }}
        >
          <span>{source.title}</span>
          <ExternalLink size={13} style={{ flexShrink: 0, color: 'var(--text-muted)' }} />
        </a>
      </div>

      {source.description && (
        <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
          {source.description}
        </p>
      )}
    </div>
  );
}
