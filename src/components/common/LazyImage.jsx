import { useState } from 'react';

/**
 * High-performance Lazy Loaded Image Component with Skeleton Placeholder & Error Fallback
 */
const LazyImage = ({
  src,
  alt = '',
  className = '',
  placeholder = '',
  fallback = 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400',
  width,
  height,
  aspectRatio,
  loading = 'lazy',
  decoding = 'async',
  ...props
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const imageSrc = hasError ? fallback : src;
  const ratio = aspectRatio || (width && height ? `${width} / ${height}` : undefined);

  return (
    <div
      className={`relative overflow-hidden bg-muted ${className}`}
      style={{ width, height, aspectRatio: ratio }}
    >
      {/* Skeleton Blur Placeholder */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 animate-pulse bg-muted-foreground/10" />
      )}

      {/* Main Image */}
      <img
        src={imageSrc}
        alt={alt}
        width={width}
        height={height}
        loading={loading}
        decoding={decoding}
        onLoad={() => setIsLoaded(true)}
        onError={() => {
          setHasError(true);
          setIsLoaded(true);
        }}
        className={`w-full h-full object-cover transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        }`}
        {...props}
      />
    </div>
  );
};

export default LazyImage;
