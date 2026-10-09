import React, { useState } from 'react';
import { cn, getAnimationClass } from '../../utils';

const Tabs = ({
  tabs = [],
  activeTab,
  defaultTab = 0,
  onChange,
  onTabChange,
  variant = 'underline',
  animate = 'fade',
  className = '',
  tabClassName = '',
  contentClassName = '',
}) => {
  const [internalTab, setInternalTab] = useState(defaultTab);
  const currentTab = activeTab ?? internalTab;
  const notify = onChange || onTabChange;

  const handleChange = (index) => {
    if (notify) notify(index, tabs[index]);
    else setInternalTab(index);
  };

  const listStyles = {
    underline: 'border-b border-border gap-1',
    pill: 'bg-muted rounded-lg p-1 gap-1',
    enclosed: 'border-b border-border gap-0',
  };

  const getTabClass = (isActive) => {
    if (variant === 'pill') {
      return cn(
        'px-4 py-2 rounded-md',
        isActive
          ? 'bg-background shadow-sm text-primary'
          : 'text-muted-foreground hover:text-foreground'
      );
    }
    return cn(
      'px-4 pb-3 border-b-2',
      isActive
        ? 'border-primary text-primary'
        : 'border-transparent text-muted-foreground hover:border-muted-foreground/30 hover:text-foreground'
    );
  };

  return (
    <div className={cn(className)}>
      <div
        role="tablist"
        className={cn('flex items-center', listStyles[variant])}
        aria-label="Tabs"
      >
        {tabs.map((tab, index) => {
          const isActive = currentTab === index;
          const Icon = tab.icon;
          return (
            <button
              key={tab.id ?? index}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`tabpanel-${index}`}
              id={`tab-${index}`}
              disabled={tab.disabled}
              className={cn(
                'text-sm font-medium transition-all duration-200',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-md',
                'disabled:opacity-50 disabled:pointer-events-none',
                getTabClass(isActive),
                tabClassName
              )}
              onClick={() => handleChange(index)}
            >
              {Icon && <Icon className="h-4 w-4 mr-2 inline-block" aria-hidden="true" />}
              {tab.label}
              {tab.badge != null && (
                <span className="ml-2 inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
      <div
        role="tabpanel"
        id={`tabpanel-${currentTab}`}
        aria-labelledby={`tab-${currentTab}`}
        className={cn('pt-4', getAnimationClass(animate), contentClassName)}
        key={currentTab}
      >
        {tabs[currentTab]?.content}
      </div>
    </div>
  );
};

export default Tabs;
