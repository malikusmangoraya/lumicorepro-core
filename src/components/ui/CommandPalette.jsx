import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  LayoutGrid,
  Sparkles,
  Zap,
  ShoppingBag,
  BarChart3,
  Settings,
  CreditCard,
  Layers,
  ArrowRight,
  Command,
  X,
} from 'lucide-react';
import { cn } from '@/utils';

const DEFAULT_COMMANDS = [
  { id: 'templates', title: 'Browse All Templates', category: 'Navigation', icon: LayoutGrid, href: '/templates' },
  { id: 'generate', title: 'AI Website Generator', category: 'AI Tools', icon: Sparkles, href: '/generate', badge: 'New' },
  { id: 'chat', title: 'AI Assistant Chat', category: 'AI Tools', icon: Zap, href: '/chat' },
  { id: 'dashboard', title: 'Analytics Dashboard', category: 'Apps', icon: BarChart3, href: '/templates/dashboard/DashboardOverview' },
  { id: 'store', title: 'E-Commerce Storefront', category: 'Apps', icon: ShoppingBag, href: '/templates/ecommerce/ProductListing' },
  { id: 'pricing', title: 'Pricing & Plans', category: 'Billing', icon: CreditCard, href: '/pricing' },
  { id: 'settings', title: 'System Settings', category: 'Admin', icon: Settings, href: '/admin/settings' },
  { id: 'business', title: 'Corporate Business Portal', category: 'Templates', icon: Layers, href: '/templates/business/LandingPage' },
];

export function CommandPalette({
  isOpen,
  onClose,
  items = DEFAULT_COMMANDS,
}) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();

  // Keyboard shortcut listener (Cmd+K / Ctrl+K / Escape)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose?.();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose?.();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const filtered = useMemo(() => {
    if (!query.trim()) return items;
    return items.filter((item) =>
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.category.toLowerCase().includes(query.toLowerCase())
    );
  }, [items, query]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleSelect = useCallback(
    (item) => {
      onClose?.();
      if (item.href) {
        navigate(item.href);
      } else if (item.action) {
        item.action();
      }
    },
    [navigate, onClose]
  );

  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % (filtered.length || 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % (filtered.length || 1));
    } else if (e.key === 'Enter' && filtered[selectedIndex]) {
      e.preventDefault();
      handleSelect(filtered[selectedIndex]);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 sm:pt-28 px-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-background/80 backdrop-blur-md"
            aria-hidden="true"
          />

          {/* Dialog Container */}
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: -20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-xl overflow-hidden rounded-2xl border border-border/80 bg-card shadow-2xl z-10"
            role="dialog"
            aria-modal="true"
            aria-label="Command Palette"
          >
            {/* Search Input Bar */}
            <div className="flex items-center border-b border-border/60 px-4 py-3.5">
              <Search className="h-5 w-5 text-muted-foreground mr-3 shrink-0" />
              <input
                type="text"
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a command or search pages..."
                className="w-full bg-transparent text-foreground placeholder:text-muted-foreground text-sm focus:outline-none"
              />
              <div className="flex items-center gap-1.5 ml-2">
                <kbd className="hidden sm:inline-flex items-center gap-0.5 rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                  <Command className="h-3 w-3" /> K
                </kbd>
                <button
                  onClick={onClose}
                  className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                  aria-label="Close"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            {/* Results List */}
            <div className="max-h-80 overflow-y-auto p-2">
              {filtered.length === 0 ? (
                <div className="py-12 text-center text-sm text-muted-foreground">
                  No matching commands found.
                </div>
              ) : (
                filtered.map((item, idx) => {
                  const Icon = item.icon || Layers;
                  const isSelected = idx === selectedIndex;
                  return (
                    <div
                      key={item.id || item.title}
                      onClick={() => handleSelect(item)}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={cn(
                        'flex cursor-pointer items-center justify-between rounded-xl px-3 py-2.5 text-sm transition-colors select-none',
                        isSelected ? 'bg-primary text-primary-foreground' : 'text-foreground hover:bg-accent/50'
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={cn(
                            'flex h-8 w-8 items-center justify-center rounded-lg',
                            isSelected ? 'bg-primary-foreground/20 text-primary-foreground' : 'bg-muted text-muted-foreground'
                          )}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="flex flex-col">
                          <span className="font-medium leading-none">{item.title}</span>
                          <span
                            className={cn(
                              'text-xs mt-1',
                              isSelected ? 'text-primary-foreground/75' : 'text-muted-foreground'
                            )}
                          >
                            {item.category}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {item.badge && (
                          <span
                            className={cn(
                              'rounded-full px-2 py-0.5 text-[10px] font-semibold',
                              isSelected
                                ? 'bg-primary-foreground/20 text-primary-foreground'
                                : 'bg-primary/10 text-primary'
                            )}
                          >
                            {item.badge}
                          </span>
                        )}
                        <ArrowRight
                          className={cn(
                            'h-4 w-4 transition-transform',
                            isSelected ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-1'
                          )}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Footer hints */}
            <div className="flex items-center justify-between border-t border-border/60 bg-muted/40 px-4 py-2 text-[11px] text-muted-foreground">
              <span>Navigate with <kbd className="font-mono">↑</kbd> <kbd className="font-mono">↓</kbd></span>
              <span>Select with <kbd className="font-mono">Enter</kbd></span>
              <span>Exit with <kbd className="font-mono">Esc</kbd></span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export default CommandPalette;
