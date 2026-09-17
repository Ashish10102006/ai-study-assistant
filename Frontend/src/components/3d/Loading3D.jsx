import React from 'react';

export default function Loading3D({ message = "Consulting Gemini AI & Academic Knowledge..." }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '4rem 2rem',
        width: '100%',
        minHeight: '280px'
      }}
    >
      {/* 3D Animated Rotating Crystal/Brain Rig */}
      <div
        style={{
          position: 'relative',
          width: '80px',
          height: '80px',
          marginBottom: '1.75rem'
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: '50%',
            border: '2px solid transparent',
            borderTopColor: '#00f2fe',
            borderBottomColor: '#8a2be2',
            animation: 'spin 1.2s linear infinite'
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: '8px',
            borderRadius: '50%',
            border: '2px solid transparent',
            borderRightColor: '#f72585',
            borderLeftColor: '#38bdf8',
            animation: 'spin 1.8s linear infinite reverse'
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: '16px',
            background: 'radial-gradient(circle, #00f2fe 0%, #8a2be2 100%)',
            borderRadius: '50%',
            filter: 'blur(6px)',
            opacity: 0.8,
            animation: 'pulse 1.5s ease-in-out infinite alternate'
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.6rem'
          }}
        >
          🧠
        </div>
      </div>

      <div style={{ textAlign: 'center' }}>
        <h4 style={{ fontSize: '1.2rem', color: '#f8fafc', marginBottom: '0.4rem', letterSpacing: '-0.01em' }}>
          AI STUDY ASSISTANT
        </h4>
        <p style={{ color: 'var(--brand-cyan)', fontSize: '0.9rem', fontWeight: '500' }}>
          {message}
        </p>
      </div>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0% { transform: scale(0.85); opacity: 0.5; }
          100% { transform: scale(1.15); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
