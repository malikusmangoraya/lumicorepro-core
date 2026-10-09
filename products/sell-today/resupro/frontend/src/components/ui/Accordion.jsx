import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn, getAnimationClass } from '../../utils';

const Accordion = ({
  items = [],
  allowMultiple = false,
  defaultOpen = [],
  openItems: controlledOpen,
  onChange,
  onToggle,
  animate = 'none',
  className = '',
  itemClassName = '',
}) => {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const openItems = controlledOpen ?? internalOpen;
  const notify = onChange || onToggle;

  const toggleItem = (index) => {
    const next = (() => {
      if (allowMultiple) {
        return openItems.includes(index)
          ? openItems.filter((i) => i !== index)
          : [...openItems, index];
      }
      return openItems.includes(index) ? [] : [index];
    })();

    if (controlledOpen === undefined) setInternalOpen(next);
    notify?.(next, index);
  };

  return (
    <div className={cn('space-y-2', getAnimationClass(animate), className)}>
      {items.map((item, index) => {
        const isOpen = openItems.includes(index);
        return (
          <div
            key={item.id ?? index}
            className={cn(
              'rounded-xl border border-border bg-card overflow-hidden transition-shadow',
              isOpen && 'shadow-sm',
              itemClassName
            )}
          >
            <button
              type="button"
              className="flex w-full items-center justify-between px-4 py-3.5 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              onClick={() => toggleItem(index)}
              aria-expanded={isOpen}
              aria-controls={`accordion-content-${index}`}
              id={`accordion-trigger-${index}`}
            >
              <span className="text-sm font-medium">{item.title}</span>
              <ChevronDown
                className={cn(
                  'h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200',
                  isOpen && 'rotate-180'
                )}
                aria-hidden="true"
              />
            </button>
            <div
              id={`accordion-content-${index}`}
              role="region"
              aria-labelledby={`accordion-trigger-${index}`}
              className={cn(
                'grid transition-all duration-300 ease-out',
                isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
              )}
            >
              <div className="overflow-hidden">
                <div className="px-4 pb-4 text-sm text-muted-foreground">{item.content}</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Accordion;
