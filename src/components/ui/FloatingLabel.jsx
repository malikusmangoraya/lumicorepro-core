import React, { forwardRef, useId, useState } from 'react';
import { cn } from '../../utils';

const FloatingLabel = forwardRef(
  (
    {
      label,
      type = 'text',
      error,
      helperText,
      required = false,
      disabled = false,
      leftIcon: LeftIcon,
      rightIcon: RightIcon,
      animate = 'none',
      animationDelay = 0,
      className = '',
      inputClassName = '',
      id,
      onChange,
      onFocus,
      onBlur,
      onKeyDown,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const [hasValue, setHasValue] = useState(false);
    const generatedId = useId();
    const inputId = id || generatedId;
    const isPassword = type === 'password';
    const [showPassword, setShowPassword] = useState(false);
    const actualType = isPassword && showPassword ? 'text' : type;

    const handleChange = (e) => {
      setHasValue(!!e.target.value);
      onChange?.(e);
    };

    const handleFocus = (e) => {
      setIsFocused(true);
      onFocus?.(e);
    };

    const handleBlur = (e) => {
      setIsFocused(false);
      onBlur?.(e);
    };

    const isFloating = isFocused || hasValue;

    return (
      <div className={cn('w-full relative', className)}>
        <div className="relative">
          {LeftIcon && (
            <LeftIcon
              className={cn(
                'absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground transition-colors duration-200',
                isFocused && 'text-primary',
                isFloating && '-translate-y-2 scale-75'
              )}
              aria-hidden="true"
            />
          )}
          <input
            ref={ref}
            id={inputId}
            type={actualType}
            disabled={disabled}
            aria-invalid={!!error}
            aria-describedby={
              error ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
            }
            className={cn(
              'w-full rounded-lg border bg-background px-4 py-3.5 text-sm transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'placeholder-transparent',
              error
                ? 'border-destructive focus:ring-destructive'
                : 'border-border hover:border-muted-foreground/30 focus:border-primary',
              LeftIcon && 'pl-10',
              (RightIcon || isPassword) && 'pr-10',
              isFloating && 'pt-5 pb-2',
              inputClassName
            )}
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            onKeyDown={onKeyDown}
            placeholder=" "
            {...props}
          />
          <label
            htmlFor={inputId}
            className={cn(
              'absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground pointer-events-none transition-all duration-200',
              'origin-left',
              isFloating && '-translate-y-3.5 scale-75 text-primary',
              LeftIcon && 'pl-7',
              error && 'text-destructive'
            )}
          >
            {label}
            {required && (
              <span className="ml-0.5 text-destructive" aria-hidden="true">
                *
              </span>
            )}
          </label>
          {isPassword ? (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? (
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              )}
            </button>
          ) : (
            RightIcon && (
              <RightIcon
                className={cn(
                  'absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground transition-colors duration-200',
                  isFocused && 'text-primary'
                )}
                aria-hidden="true"
              />
            )
          )}
        </div>
        {error ? (
          <p
            id={`${inputId}-error`}
            className="mt-1.5 flex items-center gap-1 text-xs text-destructive animate-fade-in"
            role="alert"
          >
            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
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

FloatingLabel.displayName = 'FloatingLabel';

export default FloatingLabel;