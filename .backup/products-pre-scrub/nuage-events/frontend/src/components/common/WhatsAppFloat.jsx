import React from 'react';
import { MessageCircle } from 'lucide-react';
import { cn } from '../../utils';

const WhatsAppFloat = ({
  phoneNumber = '',
  message = 'Hello! I would like to know more.',
  label = 'Chat with us on WhatsApp',
  position = 'right',
  className = '',
}) => {
  const href = phoneNumber
    ? `https://wa.me/${phoneNumber.replace(/\D/g, '')}?text=${encodeURIComponent(message)}`
    : null;

  if (!href) return null;

  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      title={label}
      className={cn(
        'fixed bottom-5 z-50 inline-flex h-13 w-13 items-center justify-center rounded-full bg-green-500 p-3.5 text-white shadow-lg transition-all duration-200 hover:scale-105 hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500/40',
        position === 'left' ? 'left-5' : 'right-5',
        className
      )}
    >
      <MessageCircle className="h-6 w-6" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </a>
  );
};

export default WhatsAppFloat;
