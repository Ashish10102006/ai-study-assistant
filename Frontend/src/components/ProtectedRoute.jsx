import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Brain } from 'lucide-react';

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div
        style={{
          minHeight: 'calc(100vh - var(--navbar-height))',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.25rem',
          color: 'var(--text-secondary)'
        }}
      >
        <div
          style={{
            width: '54px',
            height: '54px',
            borderRadius: '16px',
            background: 'var(--grad-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#030712',
            boxShadow: '0 0 24px rgba(0, 242, 254, 0.4)',
            animation: 'pulse 1.8s infinite ease-in-out'
          }}
        >
          <Brain size={28} />
        </div>
        <p style={{ fontSize: '0.92rem', letterSpacing: '0.02em', color: 'var(--text-muted)' }}>
          Authenticating student session...
        </p>
      </div>
    );
  }

  if (!user) {
    // Redirect to login preserving the attempted route for seamless post-login return
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
