import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn, getAnimationClass } from '../../utils';

const Dropdown = ({
  trigger,
  children,
  label,
  align = 'left',
  open: controlledOpen,
  defaultOpen = false,
  onOpenChange,
  onClose,
  className = '',
  menuClassName = '',
  closeOnSelect = true,
  animate = 'scale',
}) => {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const open = controlledOpen ?? internalOpen;
  const ref = useRef(null);

  const setOpen = useCallback(
    (next) => {
      if (controlledOpen === undefined) setInternalOpen(next);
      onOpenChange?.(next);
      if (!next) onClose?.();
    },
    [controlledOpen, onOpenChange, onClose]
  );

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    const handleEscape = (e) => {
      if (e.key === 'Escape') setOpen(false);
    };

    if (!open) return undefined;

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [open, setOpen]);

  const alignments = {
    left: 'left-0',
    right: 'right-0',
    center: 'left-1/2 -translate-x-1/2',
  };

  return (
    <div ref={ref} className={cn('relative inline-block', className)}>
      {trigger ? (
        React.cloneElement(trigger, {
          onClick: (e) => {
            trigger.props.onClick?.(e);
            setOpen(!open);
          },
          'aria-expanded': open,
          'aria-haspopup': 'menu',
        })
      ) : (
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-haspopup="menu"
        >
          {label}
          <ChevronDown
            className={cn('h-4 w-4 transition-transform duration-200', open && 'rotate-180')}
          />
        </button>
      )}
      {open && (
        <div
          role="menu"
          className={cn(
            'absolute z-50 mt-2 min-w-[10rem] rounded-xl border border-border bg-card shadow-lg p-1.5',
            alignments[align],
            getAnimationClass(animate),
            menuClassName
          )}
        >
          {React.Children.map(children, (child) => {
            if (!React.isValidElement(child)) return child;
            if (closeOnSelect && child.type === DropdownItem) {
              return React.cloneElement(child, {
                onClick: (...args) => {
                  child.props.onClick?.(...args);
                  setOpen(false);
                },
              });
            }
            return child;
          })}
        </div>
      )}
    </div>
  );
};

export const DropdownItem = ({
  children,
  onClick,
  icon: Icon,
  danger = false,
  disabled = false,
  className = '',
  ...props
}) => (
  <button
    type="button"
    onClick={onClick}
    disabled={disabled}
    className={cn(
      'flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors',
      'disabled:opacity-50 disabled:pointer-events-none',
      danger ? 'text-destructive hover:bg-destructive/10' : 'text-foreground hover:bg-muted',
      className
    )}
    role="menuitem"
    {...props}
  >
    {Icon && <Icon className="h-4 w-4" aria-hidden="true" />}
    {children}
  </button>
);

export const DropdownHeader = ({ children, className = '' }) => (
  <div className={cn('px-3 py-2 text-sm font-medium text-muted-foreground', className)}>
    {children}
  </div>
);

export const DropdownDivider = () => (
  <div className="my-1.5 border-t border-border" aria-hidden="true" />
);

export default Dropdown;
