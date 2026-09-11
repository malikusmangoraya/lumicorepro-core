import React, { forwardRef } from 'react';

const Switch = forwardRef(
  (
    {
      label,
      checked,
      onChange,
      error,
      helperText,
      disabled = false,
      size = 'md',
      className = '',
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || `switch-${Math.random().toString(36).substr(2, 9)}`;

    const sizes = {
      sm: { track: 'h-5 w-9', thumb: 'h-4 w-4', translate: 'translate-x-4' },
      md: { track: 'h-6 w-11', thumb: 'h-5 w-5', translate: 'translate-x-5' },
      lg: { track: 'h-7 w-14', thumb: 'h-6 w-6', translate: 'translate-x-7' },
    };

    const sizeConfig = sizes[size];

    return (
      <div className={`w-full ${className}`}>
        <label
          htmlFor={inputId}
          className={`flex items-center gap-3 cursor-pointer select-none ${
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          <span className="relative inline-flex">
            <input
              ref={ref}
              id={inputId}
              type="checkbox"
              role="switch"
              checked={checked}
              onChange={onChange}
              disabled={disabled}
              aria-checked={checked}
              aria-invalid={!!error}
              className="peer sr-only"
              {...props}
            />
            <span
              className={`${sizeConfig.track} rounded-full transition-colors ${
                checked ? 'bg-primary' : 'bg-muted-foreground/30'
              } peer-focus-visible:ring-2 peer-focus-visible:ring-primary peer-focus-visible:ring-offset-2`}
              aria-hidden="true"
            >
              <span
                className={`${sizeConfig.thumb} absolute top-0.5 left-0.5 rounded-full bg-white shadow transition-transform ${
                  checked ? sizeConfig.translate : ''
                }`}
              />
            </span>
          </span>
          {label && <span className="text-sm font-medium text-foreground">{label}</span>}
        </label>
        {error ? (
          <p className="mt-1.5 text-xs text-destructive" role="alert">
            {error}
          </p>
        ) : helperText ? (
          <p className="mt-1.5 text-xs text-muted-foreground">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Switch.displayName = 'Switch';

export default Switch;
