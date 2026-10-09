import React, { useEffect, useState } from 'react';
import { Link2, Linkedin, Facebook, Twitter, Share2 } from 'lucide-react';
import { cn } from '../../utils';

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) {
    return false;
  }
};

const encode = (u) =>
  encodeURIComponent(u || (typeof window !== 'undefined' ? window.location.href : ''));

const SocialShare = ({
  url,
  title = '',
  networks = ['linkedin', 'facebook', 'twitter', 'copy'],
  variant = 'icon',
  className = '',
  onShared,
}) => {
  const [copied, setCopied] = useState(false);
  const target = url || (typeof window !== 'undefined' ? window.location.href : '');
  const text = encodeURIComponent(title || document.title || '');

  const links = {
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encode(target)}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encode(target)}`,
    twitter: `https://twitter.com/intent/tweet?url=${encode(target)}&text=${text}`,
  };

  const handleShare = (n) => {
    if (n === 'copy') {
      copyToClipboard(target).then((ok) => {
        setCopied(ok);
        setTimeout(() => setCopied(false), 2000);
      });
      return;
    }
    if (typeof onShared === 'function') onShared(n);
    window.open(links[n], '_blank', 'noopener,noreferrer,width=600,height=500');
  };

  const icons = {
    linkedin: Linkedin,
    facebook: Facebook,
    twitter: Twitter,
    copy: Link2,
  };

  const labels = {
    linkedin: 'Share on LinkedIn',
    facebook: 'Share on Facebook',
    twitter: 'Share on X',
  };

  return (
    <div
      className={cn('flex items-center gap-2', className)}
      role="group"
      aria-label="Share this page"
    >
      {variant === 'button' && (
        <span className="inline-flex items-center gap-1.5 text-sm text-muted-foreground">
          <Share2 className="h-4 w-4" aria-hidden="true" />
          Share
        </span>
      )}
      {networks.map((n) => {
        const Icon = icons[n] || Share2;
        const active = copied && n === 'copy';
        return (
          <button
            key={n}
            type="button"
            onClick={() => handleShare(n)}
            aria-label={
              active ? 'Link copied' : n === 'copy' ? 'Copy link' : labels[n] || `Share via ${n}`
            }
            className={cn(
              'inline-flex items-center justify-center rounded-full border bg-background text-muted-foreground transition-all duration-200 hover:border-primary hover:text-primary focus:outline-none focus:ring-2 focus:ring-primary/40',
              variant === 'icon' ? 'h-9 w-9' : 'h-9 gap-1.5 px-3 text-sm',
              active && 'border-green-600 text-green-600'
            )}
          >
            {active ? <CheckIcon /> : <Icon className="h-4 w-4" aria-hidden="true" />}
          </button>
        );
      })}
    </div>
  );
};

const CheckIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-4 w-4"
    aria-hidden="true"
  >
    <path d="M20 6 9 17l-5-5" />
  </svg>
);

export default SocialShare;
