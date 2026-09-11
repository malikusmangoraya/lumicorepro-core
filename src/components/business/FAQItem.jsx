import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn, getAnimationClass } from '../../utils';

const FAQItem = ({
  question,
  answer,
  open: controlledOpen,
  defaultOpen = false,
  onToggle,
  onChange,
  animate = 'none',
  animationDelay = 0,
  className = '',
  ...props
}) => {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const isOpen = controlledOpen ?? internalOpen;

  const toggle = () => {
    const next = !isOpen;
    if (controlledOpen === undefined) setInternalOpen(next);
    onToggle?.(next);
    onChange?.(next);
  };

  return (
    <div
      className={cn(
        'border-b border-border py-4',
        getAnimationClass(animate, animationDelay),
        className
      )}
      {...props}
    >
      <button
        type="button"
        className="flex w-full items-center justify-between gap-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-md"
        onClick={toggle}
        aria-expanded={isOpen}
      >
        <span className="text-base font-medium text-foreground">{question}</span>
        <ChevronDown
          className={cn(
            'h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200',
            isOpen && 'rotate-180'
          )}
          aria-hidden="true"
        />
      </button>
      <div
        className={cn(
          'grid transition-all duration-300 ease-out',
          isOpen ? 'grid-rows-[1fr] opacity-100 mt-3' : 'grid-rows-[0fr] opacity-0'
        )}
      >
        <div className="overflow-hidden">
          <p className="text-sm text-muted-foreground leading-relaxed">{answer}</p>
        </div>
      </div>
    </div>
  );
};

export default FAQItem;
