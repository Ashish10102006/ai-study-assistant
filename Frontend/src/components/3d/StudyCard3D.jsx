import React, { useRef, useState } from 'react';

export default function StudyCard3D({ title, subtitle, icon, badge, onClick, actionLabel = "Explore Tool", accentColor = "#00f2fe" }) {
  const cardRef = useRef(null);
  const [rotation, setRotation] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotX = -((y - centerY) / centerY) * 10;
    const rotY = ((x - centerX) / centerX) * 10;

    setRotation({ x: rotX, y: rotY });
  };

  const handleMouseEnter = () => setIsHovered(true);

  const handleMouseLeave = () => {
    setIsHovered(false);
    setRotation({ x: 0, y: 0 });
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      style={{
        perspective: '1000px',
        cursor: 'pointer',
        height: '100%'
      }}
    >
      <div
        style={{
          background: 'linear-gradient(145deg, rgba(20, 27, 43, 0.8) 0%, rgba(10, 14, 23, 0.9) 100%)',
          backdropFilter: 'blur(16px)',
          border: `1px solid ${isHovered ? accentColor : 'rgba(255, 255, 255, 0.08)'}`,
          borderRadius: '20px',
          padding: '2rem 1.75rem',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          transition: 'transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.25s ease, border-color 0.25s ease',
          transform: isHovered
            ? `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg) translateY(-8px) translateZ(20px)`
            : 'rotateX(0deg) rotateY(0deg) translateY(0) translateZ(0)',
          boxShadow: isHovered
            ? `0 20px 40px -10px rgba(0, 0, 0, 0.8), 0 0 30px ${accentColor}25`
            : '0 8px 24px rgba(0, 0, 0, 0.4)',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        {/* Glow ambient spot */}
        <div
          style={{
            position: 'absolute',
            top: '-30%',
            right: '-30%',
            width: '180px',
            height: '180px',
            background: `radial-gradient(circle, ${accentColor}30 0%, transparent 70%)`,
            pointerEvents: 'none',
            opacity: isHovered ? 1 : 0.4,
            transition: 'opacity 0.3s ease'
          }}
        />

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div
              style={{
                width: '52px',
                height: '52px',
                borderRadius: '14px',
                background: `rgba(255, 255, 255, 0.05)`,
                border: `1px solid ${accentColor}40`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.75rem',
                transform: isHovered ? 'scale(1.1) rotate(5deg)' : 'scale(1)',
                transition: 'transform 0.3s ease'
              }}
            >
              {icon}
            </div>
            {badge && (
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: '600',
                  padding: '0.25rem 0.65rem',
                  borderRadius: '999px',
                  background: `${accentColor}15`,
                  color: accentColor,
                  border: `1px solid ${accentColor}35`
                }}
              >
                {badge}
              </span>
            )}
          </div>

          <h3 style={{ fontSize: '1.35rem', marginBottom: '0.6rem', color: '#f8fafc' }}>
            {title}
          </h3>
          <p style={{ fontSize: '0.92rem', color: '#94a3b8', lineHeight: '1.55' }}>
            {subtitle}
          </p>
        </div>

        <div style={{ marginTop: '1.75rem', paddingTop: '1.25rem', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: accentColor,
              fontWeight: '600',
              fontSize: '0.9rem'
            }}
          >
            <span>{actionLabel}</span>
            <span style={{ transform: isHovered ? 'translateX(5px)' : 'none', transition: 'transform 0.2s ease' }}>→</span>
          </div>
        </div>
      </div>
    </div>
  );
}
