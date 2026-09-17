import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Brain,
  BookOpen,
  LayoutDashboard,
  FileText,
  Bookmark,
  Search,
  User,
  LogOut,
  Menu,
  X,
  Sparkles
} from 'lucide-react';

export default function Navbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
  };

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'AI Study', path: '/study', icon: <Sparkles size={16} /> },
    { name: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={16} /> },
    { name: 'Materials', path: '/materials', icon: <FileText size={16} /> },
    { name: 'Resources', path: '/resources', icon: <Search size={16} /> },
  ];

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        background: 'rgba(7, 9, 14, 0.82)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        height: 'var(--navbar-height)'
      }}
    >
      <div
        className="container"
        style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        {/* Brand Logo */}
        <Link
          to="/"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem',
            textDecoration: 'none',
            minWidth: 0
          }}
        >
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#030712',
              boxShadow: '0 0 14px rgba(0, 242, 254, 0.4)',
              flexShrink: 0
            }}
          >
            <Brain size={22} />
          </div>
          <div style={{ minWidth: 0, overflow: 'hidden' }}>
            <div
              style={{
                fontFamily: 'Outfit',
                fontWeight: '800',
                fontSize: 'clamp(1rem, 4.2vw, 1.25rem)',
                color: '#fff',
                letterSpacing: '-0.02em',
                lineHeight: 1.1,
                whiteSpace: 'nowrap'
              }}
            >
              AI STUDY <span style={{ color: 'var(--brand-cyan)' }}>ASSISTANT</span>
            </div>
            <div
              style={{
                fontSize: '0.68rem',
                color: 'var(--text-muted)',
                letterSpacing: '0.04em',
                display: 'block'
              }}
            >
              ACADEMIC AI
            </div>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="nav-desktop">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.5rem 0.9rem',
                borderRadius: '10px',
                fontSize: '0.9rem',
                fontWeight: isActive(link.path) ? '600' : '500',
                color: isActive(link.path) ? 'var(--brand-cyan)' : 'var(--text-secondary)',
                background: isActive(link.path) ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                border: isActive(link.path) ? '1px solid rgba(0, 242, 254, 0.2)' : '1px solid transparent',
                transition: 'all var(--transition-fast)'
              }}
            >
              {link.icon}
              <span>{link.name}</span>
            </Link>
          ))}
        </nav>

        {/* Auth CTA & Profile Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Link
                to="/profile"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  padding: '0.35rem 0.65rem',
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid var(--border-medium)',
                  minHeight: '38px'
                }}
              >
                {user.user_metadata?.avatar_url || user.user_metadata?.picture ? (
                  <img
                    src={user.user_metadata.avatar_url || user.user_metadata.picture}
                    alt="Student Avatar"
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      objectFit: 'cover',
                      border: '1px solid var(--brand-cyan)',
                      flexShrink: 0
                    }}
                  />
                ) : (
                  <div
                    style={{
                      width: '28px',
                      height: '28px',
                      borderRadius: '50%',
                      background: 'var(--grad-primary)',
                      color: '#000',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: '700',
                      fontSize: '0.8rem',
                      flexShrink: 0
                    }}
                  >
                    {user.email ? user.email[0].toUpperCase() : 'S'}
                  </div>
                )}
                <span
                  className="nav-desktop"
                  style={{ fontSize: '0.82rem', color: '#f8fafc', maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                >
                  {user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || 'Student'}
                </span>
              </Link>
              <button
                onClick={handleLogout}
                title="Sign Out"
                className="nav-desktop"
                style={{
                  padding: '0.5rem',
                  borderRadius: '10px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  color: '#ef4444',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <div className="nav-desktop" style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Link to="/login" className="btn btn-secondary" style={{ padding: '0.45rem 0.85rem', fontSize: '0.82rem' }}>
                Sign In
              </Link>
              <Link to="/register" className="btn btn-primary" style={{ padding: '0.45rem 0.95rem', fontSize: '0.82rem' }}>
                Get Started
              </Link>
            </div>
          )}

          {/* Mobile Hamburger Toggle */}
          <button
            className="nav-mobile-btn"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle navigation menu"
            style={{
              display: 'none',
              alignItems: 'center',
              justifyContent: 'center',
              width: '42px',
              height: '42px',
              borderRadius: '10px',
              background: mobileOpen ? 'rgba(0, 242, 254, 0.15)' : 'rgba(255, 255, 255, 0.06)',
              border: `1px solid ${mobileOpen ? 'var(--brand-cyan)' : 'var(--border-medium)'}`,
              color: mobileOpen ? 'var(--brand-cyan)' : '#fff'
            }}
          >
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Overlay & Menu */}
      {mobileOpen && (
        <>
          <div
            onClick={() => setMobileOpen(false)}
            style={{
              position: 'fixed',
              top: 'var(--navbar-height)',
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(3, 7, 18, 0.7)',
              backdropFilter: 'blur(6px)',
              zIndex: 98
            }}
          />
          <div
            className="nav-mobile-drawer"
            style={{
              position: 'relative',
              zIndex: 99,
              background: 'rgba(10, 14, 23, 0.98)',
              borderBottom: '1px solid rgba(0, 242, 254, 0.25)',
              padding: '1.25rem 1rem 1.5rem 1rem',
              maxHeight: 'calc(100vh - var(--navbar-height))',
              overflowY: 'auto'
            }}
          >
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileOpen(false)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.85rem',
                  padding: '0.85rem 1rem',
                  borderRadius: '12px',
                  color: isActive(link.path) ? 'var(--brand-cyan)' : 'var(--text-primary)',
                  background: isActive(link.path) ? 'rgba(0, 242, 254, 0.12)' : 'rgba(255, 255, 255, 0.03)',
                  border: `1px solid ${isActive(link.path) ? 'rgba(0, 242, 254, 0.3)' : 'rgba(255, 255, 255, 0.05)'}`,
                  fontWeight: '600',
                  fontSize: '0.98rem',
                  minHeight: '48px'
                }}
              >
                {link.icon}
                <span>{link.name}</span>
              </Link>
            ))}

            {/* Mobile Auth Actions */}
            <div style={{ marginTop: '0.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255, 255, 255, 0.08)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {user ? (
                <>
                  <Link
                    to="/profile"
                    onClick={() => setMobileOpen(false)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      padding: '0.85rem 1rem',
                      borderRadius: '12px',
                      background: 'rgba(255, 255, 255, 0.04)',
                      border: '1px solid var(--border-medium)',
                      minHeight: '48px',
                      color: '#fff'
                    }}
                  >
                    {user.user_metadata?.avatar_url || user.user_metadata?.picture ? (
                      <img
                        src={user.user_metadata.avatar_url || user.user_metadata.picture}
                        alt="Avatar"
                        style={{ width: '24px', height: '24px', borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }}
                      />
                    ) : (
                      <User size={18} color="var(--brand-cyan)" />
                    )}
                    <span>My Profile ({user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0] || 'Student'})</span>
                  </Link>
                  <button
                    onClick={() => { setMobileOpen(false); handleLogout(); }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '0.5rem',
                      padding: '0.85rem 1rem',
                      borderRadius: '12px',
                      background: 'rgba(239, 68, 68, 0.12)',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      color: '#f87171',
                      fontWeight: '600',
                      minHeight: '48px'
                    }}
                  >
                    <LogOut size={18} />
                    <span>Sign Out</span>
                  </button>
                </>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  <Link
                    to="/login"
                    onClick={() => setMobileOpen(false)}
                    className="btn btn-secondary"
                    style={{ width: '100%', minHeight: '48px' }}
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setMobileOpen(false)}
                    className="btn btn-primary"
                    style={{ width: '100%', minHeight: '48px' }}
                  >
                    Get Started
                  </Link>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </header>
  );
}
