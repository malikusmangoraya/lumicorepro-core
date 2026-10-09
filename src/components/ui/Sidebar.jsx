import React, { useState } from 'react';
import { Link, useLocation, NavLink } from 'react-router-dom';
import { cn } from '../../utils';
import { ChevronRight, ChevronDown, X } from 'lucide-react';
import { motion } from 'framer-motion';
import IconButton from './IconButton';
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from './Collapsible';

const Sidebar = React.forwardRef(
  (
    {
      items = [],
      className = '',
      collapsed = false,
      onToggle,
      variant = 'default',
      showIcons = true,
      ...props
    },
    ref
  ) => {
    const location = useLocation();
    const [openSections, setOpenSections] = useState({});

    const variants = {
      default: 'bg-card border-r border-border',
      inset: 'bg-card border-r border-border shadow-lg',
      overlay: 'bg-card/95 backdrop-blur-xl border-r border-border shadow-xl',
    };

    const handleSectionToggle = (sectionKey) => {
      setOpenSections(prev => ({
        ...prev,
        [sectionKey]: !prev[sectionKey],
      }));
    };

    const isActive = (path) => {
      if (!path) return false;
      return location.pathname === path || location.pathname.startsWith(`${path}/`);
    };

    const isSectionActive = (sectionItems) => {
      return sectionItems.some(item => isActive(item.path));
    };

    const renderItem = (item, depth = 0) => {
      const active = isActive(item.path);
      const hasChildren = item.children && item.children.length > 0;
      const sectionKey = item.path || item.label;

      if (hasChildren) {
        const sectionActive = isSectionActive(item.children);
        const isOpen = openSections[sectionKey];

        return (
          <Collapsible key={sectionKey} open={isOpen} onOpenChange={() => handleSectionToggle(sectionKey)} className="w-full">
            <CollapsibleTrigger className="w-full">
              <NavLink
                to={item.path}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                  'text-sm font-medium',
                  active || sectionActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted/50',
                  collapsed && 'justify-center px-2'
                )}
                aria-current={active ? 'page' : undefined}
                onClick={() => handleSectionToggle(sectionKey)}
              >
                {showIcons && item.icon && (
                  <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" strokeWidth={2} />
                )}
                {!collapsed && <span className="flex-1 text-left">{item.label}</span>}
                {!collapsed && (
                  <ChevronDown
                    className={cn(
                      'h-4 w-4 text-muted-foreground transition-transform duration-200',
                      isOpen && 'rotate-180'
                    )}
                    aria-hidden="true"
                  />
                )}
              </NavLink>
            </CollapsibleTrigger>
            <CollapsibleContent className="overflow-hidden">
              <div className={cn('pl-6 py-1 space-y-1', collapsed && 'pl-2')}>
                {item.children.map(child => renderItem(child, depth + 1))}
              </div>
            </CollapsibleContent>
          </Collapsible>
        );
      }

      return (
        <NavLink
          key={item.path}
          to={item.path}
          className={cn(
            'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
            'text-sm font-medium',
            active
              ? 'bg-primary/10 text-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted/50',
            collapsed && 'justify-center px-2',
            item.disabled && 'opacity-50 pointer-events-none'
          )}
          aria-current={active ? 'page' : undefined}
          onClick={item.onClick}
        >
          {showIcons && item.icon && (
            <item.icon className="h-5 w-5 shrink-0" aria-hidden="true" strokeWidth={2} />
          )}
          {!collapsed && <span className="flex-1 text-left">{item.label}</span>}
          {item.badge && !collapsed && (
            <span className="ml-auto px-2 py-0.5 text-xs font-medium rounded-full bg-primary/10 text-primary">
              {item.badge}
            </span>
          )}
        </NavLink>
      );
    };

    return (
      <motion.aside
        ref={ref}
        className={cn(
          'flex flex-col h-full transition-all duration-300 ease-out',
          variants[variant],
          collapsed ? 'w-16' : 'w-64',
          className
        )}
        animate={{ width: collapsed ? 64 : 256 }}
        {...props}
      >
        {!collapsed && (
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-lg font-bold text-foreground">Navigation</h2>
              <IconButton
                icon={X}
                label="Collapse sidebar"
                size="sm"
                variant="ghost"
                onClick={onToggle}
                className="ml-auto"
              />
            </div>
          </div>
        )}
        <nav
          role="navigation"
          aria-label="Sidebar navigation"
          className="flex-1 p-3 space-y-1 overflow-y-auto"
        >
          {items.map(item => renderItem(item))}
        </nav>
        {collapsed && onToggle && (
          <div className="p-3 border-t border-border">
            <IconButton
              icon={ChevronRight}
              label="Expand sidebar"
              size="sm"
              variant="ghost"
              onClick={onToggle}
              className="w-full"
            />
          </div>
        )}
      </motion.aside>
    );
  }
);

Sidebar.displayName = 'Sidebar';

export default Sidebar;