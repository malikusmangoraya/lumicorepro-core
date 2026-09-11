import React, { forwardRef } from 'react';
import { AlertCircle } from 'lucide-react';

const Textarea = forwardRef(
  (
    {
      label,
      error,
      helperText,
      required = false,
      disabled = false,
      rows = 4,
      maxLength,
      showCount = false,
      className = '',
      id,
      value,
      ...props
    },
    ref
  ) => {
    const inputId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
    const count = value?.length || 0;

    const baseClasses =
      'w-full rounded-lg border bg-background px-4 py-2.5 text-sm transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed resize-y';
    const stateClasses = error
      ? 'border-destructive focus:ring-destructive'
      : 'border-border hover:border-muted-foreground/30';

    return (
      <div className={`w-full ${className}`}>
        {label && (
          <div className="mb-1.5 flex items-center justify-between">
            <label htmlFor={inputId} className="block text-sm font-medium text-foreground">
              {label}
              {required && (
                <span className="ml-0.5 text-destructive" aria-hidden="true">
                  *
                </span>
              )}
            </label>
            {showCount && maxLength && (
              <span className="text-xs text-muted-foreground">
                {count}/{maxLength}
              </span>
            )}
          </div>
        )}
        <textarea
          ref={ref}
          id={inputId}
          rows={rows}
          maxLength={maxLength}
          disabled={disabled}
          value={value}
          aria-invalid={!!error}
          aria-describedby={
            error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
          }
          className={`${baseClasses} ${stateClasses}`}
          {...props}
        />
        {error ? (
          <p
            id={`${inputId}-error`}
            className="mt-1.5 flex items-center gap-1 text-xs text-destructive"
            role="alert"
          >
            <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
            {error}
          </p>
        ) : helperText ? (
          <p id={`${inputId}-helper`} className="mt-1.5 text-xs text-muted-foreground">
            {helperText}
          </p>
        ) : null}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

export default Textarea;
