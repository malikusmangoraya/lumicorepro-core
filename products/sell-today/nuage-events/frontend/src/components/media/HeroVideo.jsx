import React from 'react';

/**
 * HeroVideo — a cinematic video panel with a poster-first upgrade path.
 *
 * The poster image renders immediately and is preloaded by index.html, so the
 * largest contentful paint never waits on video. The clip itself is attached
 * only after the browser has had a moment to finish the first render, on
 * viewports 768px and wider, and never under prefers-reduced-motion or
 * data-saver mode. If it fails to load, the poster stays in place, so the hero
 * never renders an empty box.
 */
export default function HeroVideo({
  src,
  poster,
  alt = '',
  caption = '',
  className = '',
  aspect = '16 / 10',
}) {
  const base = import.meta.env.BASE_URL || '/';
  const asset = (p) => (p ? `${base.replace(/\/$/, '')}/${String(p).replace(/^\//, '')}` : p);
  const wrapRef = React.useRef(null);
  const videoRef = React.useRef(null);
  const [live, setLive] = React.useState(false);
  const [ready, setReady] = React.useState(false);
  const [failed, setFailed] = React.useState(false);

  React.useEffect(() => {
    if (live || failed || !src) return undefined;
    let cancelled = false;

    const allowed = () => {
      try {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false;
        if (window.matchMedia('(max-width: 767px)').matches) return false;
        if (navigator.connection && navigator.connection.saveData) return false;
        return true;
      } catch (e) {
        return false;
      }
    };
    if (!allowed()) return undefined;

    // Deferred so the clip never competes with the first render.
    const timer = window.setTimeout(() => {
      if (!cancelled) setLive(true);
    }, 700);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [src, live, failed]);

  React.useEffect(() => {
    const video = videoRef.current;
    if (!video || !live || failed) return undefined;
    let observer;
    try {
      if (!('IntersectionObserver' in window)) {
        video.play().catch(() => {});
        return undefined;
      }
      observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            video.play().catch(() => {});
          } else {
            video.pause();
          }
        });
      });
      observer.observe(video);
    } catch (e) {
      return undefined;
    }
    return () => {
      if (observer) observer.disconnect();
    };
  }, [live, failed]);

  return (
    <div
      ref={wrapRef}
      className={`hero-video${ready ? ' is-ready' : ''} ${className}`}
      style={{ aspectRatio: aspect }}
      data-reveal
    >
      <img
        src={asset(poster)}
        alt={alt}
        loading="lazy"
        decoding="async"
        width="1200"
        height="750"
        className="hero-video-poster"
      />
      {live && !failed && (
        <video
          ref={videoRef}
          className="hero-video-el"
          src={asset(src)}
          poster={asset(poster)}
          muted
          loop
          playsInline
          preload="none"
          aria-hidden="true"
          tabIndex={-1}
          onCanPlay={() => setReady(true)}
          onError={() => setFailed(true)}
        />
      )}
      <div className="hero-video-shade" aria-hidden="true" />
      {caption && <p className="hero-video-caption">{caption}</p>}
    </div>
  );
}