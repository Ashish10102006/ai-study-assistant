import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

export default function Hero3DScene() {
  const mountRef = useRef(null);
  const [hasWebGL, setHasWebGL] = useState(true);

  useEffect(() => {
    const currentMount = mountRef.current;
    if (!currentMount) return;

    // Check WebGL availability
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) {
        setHasWebGL(false);
        return;
      }
    } catch (e) {
      setHasWebGL(false);
      return;
    }

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    const width = currentMount.clientWidth || window.innerWidth;
    const height = currentMount.clientHeight || 500;

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.z = 18;

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    currentMount.appendChild(renderer.domElement);

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const pointLight1 = new THREE.PointLight(0x00f2fe, 3, 50);
    pointLight1.position.set(10, 10, 10);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x8a2be2, 3, 50);
    pointLight2.position.set(-10, -10, 10);
    scene.add(pointLight2);

    // 4. Central Digital Brain / Knowledge Core
    const coreGroup = new THREE.Group();
    scene.add(coreGroup);

    // Inner Icosahedron
    const coreGeo = new THREE.IcosahedronGeometry(4.5, 2);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x00f2fe,
      wireframe: true,
      emissive: 0x00f2fe,
      emissiveIntensity: 0.4,
      transparent: true,
      opacity: 0.7
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreGroup.add(coreMesh);

    // Glowing Inner Nucleus
    const innerGeo = new THREE.SphereGeometry(2.5, 32, 32);
    const innerMat = new THREE.MeshStandardMaterial({
      color: 0x8a2be2,
      emissive: 0x8a2be2,
      emissiveIntensity: 0.8,
      roughness: 0.2,
      metalness: 0.8
    });
    const innerMesh = new THREE.Mesh(innerGeo, innerMat);
    coreGroup.add(innerMesh);

    // 5. Orbiting Knowledge Nodes & Academic Floating Objects
    const orbitGroup = new THREE.Group();
    scene.add(orbitGroup);

    const isMobile = window.innerWidth < 768;
    const nodeCount = isMobile ? 6 : 12;
    const orbitNodes = [];

    for (let i = 0; i < nodeCount; i++) {
      const radius = 7.5 + (i % 3) * 2;
      const angle = (i / nodeCount) * Math.PI * 2;
      const heightOffset = (Math.sin(i) * 3);

      const nodeGroup = new THREE.Group();

      // Academic Document / Card Shape
      if (i % 3 === 0) {
        const cardGeo = new THREE.BoxGeometry(1.4, 1.8, 0.1);
        const cardMat = new THREE.MeshStandardMaterial({
          color: 0xffffff,
          emissive: 0x00f2fe,
          emissiveIntensity: 0.3,
          metalness: 0.3,
          roughness: 0.2
        });
        const cardMesh = new THREE.Mesh(cardGeo, cardMat);
        cardMesh.rotation.x = 0.4;
        cardMesh.rotation.y = 0.5;
        nodeGroup.add(cardMesh);
      } else {
        // Knowledge Sphere Node
        const sphereGeo = new THREE.SphereGeometry(0.65, 16, 16);
        const sphereMat = new THREE.MeshStandardMaterial({
          color: i % 2 === 0 ? 0x00f2fe : 0xf72585,
          emissive: i % 2 === 0 ? 0x00f2fe : 0xf72585,
          emissiveIntensity: 0.6
        });
        const sphereMesh = new THREE.Mesh(sphereGeo, sphereMat);
        nodeGroup.add(sphereMesh);
      }

      nodeGroup.position.set(
        Math.cos(angle) * radius,
        heightOffset,
        Math.sin(angle) * radius
      );

      orbitGroup.add(nodeGroup);
      orbitNodes.push({ group: nodeGroup, angle, radius, heightOffset, speed: 0.005 + (i % 3) * 0.003 });
    }

    // 6. Particle Field (Knowledge Stars)
    const particleCount = isMobile ? 250 : 600;
    const particleGeo = new THREE.BufferGeometry();
    const particleCoords = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
      particleCoords[i] = (Math.random() - 0.5) * 60;
      particleCoords[i + 1] = (Math.random() - 0.5) * 40;
      particleCoords[i + 2] = (Math.random() - 0.5) * 50;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particleCoords, 3));

    const particleMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.25,
      transparent: true,
      opacity: 0.6
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);

    // 7. Interactive Mouse / Touch Parallax
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const handleMouseMove = (event) => {
      const rect = currentMount.getBoundingClientRect();
      mouseX = ((event.clientX - rect.left) / width) * 2 - 1;
      mouseY = -(((event.clientY - rect.top) / height) * 2 - 1);
    };

    window.addEventListener('mousemove', handleMouseMove);

    // Resize Handler
    const handleResize = () => {
      if (!currentMount) return;
      const newWidth = currentMount.clientWidth || window.innerWidth;
      const newHeight = currentMount.clientHeight || 500;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener('resize', handleResize);

    // 8. Animation Loop
    let animationFrameId;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Smooth mouse lerp
      targetX += (mouseX - targetX) * 0.05;
      targetY += (mouseY - targetY) * 0.05;

      camera.position.x = targetX * 3;
      camera.position.y = targetY * 2;
      camera.lookAt(0, 0, 0);

      // Core rotation
      coreMesh.rotation.y = elapsedTime * 0.25;
      coreMesh.rotation.x = elapsedTime * 0.15;
      innerMesh.rotation.y = -elapsedTime * 0.4;

      // Orbit nodes
      orbitNodes.forEach((node) => {
        node.angle += node.speed;
        node.group.position.x = Math.cos(node.angle) * node.radius;
        node.group.position.z = Math.sin(node.angle) * node.radius;
        node.group.position.y = node.heightOffset + Math.sin(elapsedTime * 2 + node.angle) * 0.5;
        node.group.rotation.y += 0.02;
      });

      // Background particles drift
      particles.rotation.y = elapsedTime * 0.02;

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      if (currentMount && renderer.domElement) {
        currentMount.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  if (!hasWebGL) {
    return (
      <div style={{
        width: '100%',
        height: '480px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'radial-gradient(circle, rgba(0,242,254,0.1) 0%, transparent 70%)',
        borderRadius: '24px',
        border: '1px solid rgba(255,255,255,0.08)'
      }}>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🧠 ✨</div>
          <h3 style={{ color: 'var(--brand-cyan)' }}>AI Academic Knowledge Sphere</h3>
          <p style={{ color: 'var(--text-muted)' }}>WebGL acceleration is enabled in standard desktop browsers.</p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={mountRef}
      className="canvas-container"
      style={{
        width: '100%',
        height: 'clamp(280px, 40vh, 480px)',
        position: 'relative',
        borderRadius: '24px',
        overflow: 'hidden',
        pointerEvents: 'auto',
        touchAction: 'pan-y'
      }}
    />
  );
}
