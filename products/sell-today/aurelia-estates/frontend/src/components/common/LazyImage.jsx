import React, { useState } from 'react';

/**
 * LazyImage
 * ---------
 * An <img> that behaves the way a content image actually needs to:
 *
 *  - native lazy loading (eager when the image is above the fold),
 *  - async decoding so it never blocks the main thread,
 *  - reserved space from `ratio` or `width`/`height`, so the page does not
 *    jump while the image arrives (no layout shift),
 *  - a short fade-in on load, and a neutral placeholder if the file is broken,
 *  - `sizes` / `srcSet` / `loading` passthrough for responsive delivery.
 */
export default function LazyImage({
  src,
  alt = '',
  width,
  height,
  ratio = '4 / 3',
  className = '',
  priority = false,
  fallback = null,
  wrapperClassName = '',
  ...rest
}) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);

  if (!src) return null;

  return (
    <div
      className={`relative overflow-hidden bg-surface/60 ${wrapperClassName}`}
      style={ratio ? { aspectRatio: ratio } : undefined}
    >
      {failed ? (
        fallback || (
          <div
            role="img"
            aria-label={alt}
            className="flex h-full w-full items-center justify-center bg-gradient-to-br from-muted/40 to-muted/10 text-[10px] uppercase tracking-widest text-muted-foreground"
          >
            Image unavailable
          </div>
        )
      ) : (
        <img
          src={src}
          alt={alt}
          width={width}
          height={height}
          loading={priority ? 'eager' : 'lazy'}
          decoding="async"
          onLoad={() => setLoaded(true)}
          onError={() => setFailed(true)}
          className={`h-full w-full object-cover transition-opacity duration-500 ${
            loaded ? 'opacity-100' : 'opacity-0'
          } ${className}`}
          {...rest}
        />
      )}
    </div>
  );
}
