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
            gap: '0.75rem',
            textDecoration: 'none'
          }}
        >
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#030712',
              boxShadow: '0 0 16px rgba(0, 242, 254, 0.4)'
            }}
          >
            <Brain size={24} />
          </div>
          <div>
            <div
              style={{
                fontFamily: 'Outfit',
                fontWeight: '800',
                fontSize: '1.25rem',
                color: '#fff',
                letterSpacing: '-0.02em',
                lineHeight: 1.1
              }}
            >
              AI STUDY <span style={{ color: 'var(--brand-cyan)' }}>ASSISTANT</span>
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', letterSpacing: '0.04em' }}>
              ACADEMIC AI PLATFORM
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

        {/* Auth CTA & Profile */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Link
                to="/profile"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.4rem 0.8rem',
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid var(--border-medium)'
                }}
              >
                <div
                  style={{
                    width: '30px',
                    height: '30px',
                    borderRadius: '50%',
                    background: 'var(--grad-primary)',
                    color: '#000',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '700',
                    fontSize: '0.85rem'
                  }}
                >
                  {user.email ? user.email[0].toUpperCase() : 'S'}
                </div>
                <span style={{ fontSize: '0.85rem', color: '#f8fafc', maxWidth: '110px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {user.user_metadata?.full_name || user.email?.split('@')[0] || 'Student'}
                </span>
              </Link>
              <button
                onClick={handleLogout}
                title="Sign Out"
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <Link to="/login" className="btn btn-secondary" style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                Sign In
              </Link>
              <Link to="/register" className="btn btn-primary" style={{ padding: '0.5rem 1.1rem', fontSize: '0.85rem' }}>
                Get Started
              </Link>
            </div>
          )}

          {/* Mobile Menu Button */}
          <button
            className="nav-mobile-btn"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle navigation menu"
            style={{
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0.5rem',
              borderRadius: '8px',
              background: 'rgba(255, 255, 255, 0.05)',
              color: '#fff'
            }}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div
          style={{
            background: 'rgba(7, 9, 14, 0.98)',
            borderBottom: '1px solid var(--border-subtle)',
            padding: '1.25rem 1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem'
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
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                borderRadius: '12px',
                color: isActive(link.path) ? 'var(--brand-cyan)' : 'var(--text-secondary)',
                background: isActive(link.path) ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
                fontWeight: '600'
              }}
            >
              {link.icon}
              <span>{link.name}</span>
            </Link>
          ))}
        </div>
      )}
    </header>
  );
}
