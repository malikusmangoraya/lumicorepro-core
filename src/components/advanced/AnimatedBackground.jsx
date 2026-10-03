/**
 * AnimatedBackground - Dynamic Particle System
 * =============================================
 * Beautiful animated background with particles, gradients, and interactive effects.
 * 
 * Features:
 * - Floating particles
 * - Animated mesh gradient
 * - Mouse-interactive particles
 * - Multiple themes
 * - Performance optimized with Canvas API
 * - Responsive to viewport size
 */

import React, { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';

class Particle {
  constructor(canvas, theme) {
    this.canvas = canvas;
    this.theme = theme;
    this.reset();
  }

  reset() {
    this.x = Math.random() * this.canvas.width;
    this.y = Math.random() * this.canvas.height;
    this.vx = (Math.random() - 0.5) * 0.5;
    this.vy = (Math.random() - 0.5) * 0.5;
    this.radius = Math.random() * 2 + 1;
    this.opacity = Math.random() * 0.5 + 0.3;
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;

    // Wrap around edges
    if (this.x < 0) this.x = this.canvas.width;
    if (this.x > this.canvas.width) this.x = 0;
    if (this.y < 0) this.y = this.canvas.height;
    if (this.y > this.canvas.height) this.y = 0;
  }

  draw(ctx, mouseX, mouseY) {
    // Mouse interaction
    const dx = mouseX - this.x;
    const dy = mouseY - this.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    const maxDistance = 150;

    if (distance < maxDistance) {
      const force = (maxDistance - distance) / maxDistance;
      this.x -= dx * force * 0.02;
      this.y -= dy * force * 0.02;
    }

    // Draw particle
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${this.theme.particleColor}, ${this.opacity})`;
    ctx.fill();

    // Draw connections
    ctx.strokeStyle = `rgba(${this.theme.lineColor}, ${this.opacity * 0.2})`;
    ctx.lineWidth = 0.5;
  }
}

const AnimatedBackground = ({
  theme = 'default',
  particleCount = 50,
  interactive = true,
  showGradient = true,
  blur = 0,
  className = '',
}) => {
  const canvasRef = useRef(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const animationFrameId = useRef(null);
  const particlesRef = useRef([]);

  // Theme configurations
  const themes = {
    default: {
      gradient: ['#667eea', '#764ba2', '#f093fb'],
      particleColor: '255, 255, 255',
      lineColor: '255, 255, 255',
    },
    ocean: {
      gradient: ['#2E3192', '#1BFFFF', '#00C9FF'],
      particleColor: '173, 216, 230',
      lineColor: '135, 206, 250',
    },
    sunset: {
      gradient: ['#FF512F', '#F09819', '#DD2476'],
      particleColor: '255, 215, 0',
      lineColor: '255, 140, 0',
    },
    forest: {
      gradient: ['#134E5E', '#71B280', '#38ef7d'],
      particleColor: '144, 238, 144',
      lineColor: '34, 139, 34',
    },
    nebula: {
      gradient: ['#360033', '#0b8793', '#d74177'],
      particleColor: '230, 230, 250',
      lineColor: '216, 191, 216',
    },
    aurora: {
      gradient: ['#00d2ff', '#3a47d5', '#00f260'],
      particleColor: '127, 255, 212',
      lineColor: '64, 224, 208',
    },
  };

  const currentTheme = themes[theme] || themes.default;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      // Recreate particles on resize
      particlesRef.current = Array.from(
        { length: particleCount },
        () => new Particle(canvas, currentTheme)
      );
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Initialize particles
    particlesRef.current = Array.from(
      { length: particleCount },
      () => new Particle(canvas, currentTheme)
    );

    // Animation loop
    const animate = () => {
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw gradient background
      if (showGradient) {
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
        currentTheme.gradient.forEach((color, index) => {
          gradient.addColorStop(index / (currentTheme.gradient.length - 1), color);
        });
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }

      // Update and draw particles
      particlesRef.current.forEach((particle, i) => {
        particle.update();
        particle.draw(ctx, mousePos.x, mousePos.y);

        // Draw connections between nearby particles
        for (let j = i + 1; j < particlesRef.current.length; j++) {
          const otherParticle = particlesRef.current[j];
          const dx = particle.x - otherParticle.x;
          const dy = particle.y - otherParticle.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 120) {
            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(otherParticle.x, otherParticle.y);
            ctx.strokeStyle = `rgba(${currentTheme.lineColor}, ${
              (1 - distance / 120) * 0.15
            })`;
            ctx.stroke();
          }
        }
      });

      animationFrameId.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationFrameId.current) {
        cancelAnimationFrame(animationFrameId.current);
      }
    };
  }, [theme, particleCount, showGradient, mousePos]);

  const handleMouseMove = (e) => {
    if (interactive) {
      setMousePos({ x: e.clientX, y: e.clientY });
    }
  };

  return (
    <div
      className={`fixed inset-0 -z-10 ${className}`}
      onMouseMove={handleMouseMove}
      style={{ filter: blur > 0 ? `blur(${blur}px)` : 'none' }}
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{
          background: showGradient ? 'transparent' : '#000',
        }}
      />
      
      {/* Overlay gradient for depth */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(circle at 50% 50%, transparent 0%, rgba(0,0,0,0.3) 100%)',
        }}
      />
    </div>
  );
};

AnimatedBackground.propTypes = {
  theme: PropTypes.oneOf(['default', 'ocean', 'sunset', 'forest', 'nebula', 'aurora']),
  particleCount: PropTypes.number,
  interactive: PropTypes.bool,
  showGradient: PropTypes.bool,
  blur: PropTypes.number,
  className: PropTypes.string,
};

export default AnimatedBackground;
