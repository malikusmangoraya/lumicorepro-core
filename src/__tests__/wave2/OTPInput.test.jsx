import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import OTPInput from '../../components/auth/OTPInput';

afterEach(() => {
  vi.useRealTimers();
});

describe('OTPInput', () => {
  it('renders six labelled digit inputs inside the passcode group', () => {
    render(<OTPInput />);

    expect(screen.getByRole('heading', { name: 'Verify your email' })).toBeInTheDocument();
    const group = screen.getByRole('group', { name: /one-time passcode/i });
    expect(within(group).getAllByRole('textbox')).toHaveLength(6);
    expect(screen.getByLabelText('Digit 1')).toBeInTheDocument();
    expect(screen.getByLabelText('Digit 6')).toBeInTheDocument();
  });

  it('accepts one digit per box, rejects letters and advances focus', () => {
    render(<OTPInput onSubmit={vi.fn()} />);
    const inputs = screen.getAllByRole('textbox');

    fireEvent.change(inputs[0], { target: { value: '4' } });
    expect(inputs[0]).toHaveValue('4');
    expect(document.activeElement).toBe(inputs[1]);

    fireEvent.change(inputs[1], { target: { value: 'a' } });
    expect(inputs[1]).toHaveValue('');
  });

  it('submits the joined code once all six digits are filled', () => {
    const onSubmit = vi.fn();
    render(<OTPInput onSubmit={onSubmit} />);
    const inputs = screen.getAllByRole('textbox');

    '123456'.split('').forEach((digit, index) => {
      fireEvent.change(inputs[index], { target: { value: digit } });
    });

    expect(onSubmit).toHaveBeenCalledOnce();
    expect(onSubmit).toHaveBeenCalledWith('123456');
    inputs.forEach((input, index) => expect(input).toHaveValue('123456'[index]));
  });

  it('fills every box from a pasted code and submits it', () => {
    const onSubmit = vi.fn();
    render(<OTPInput onSubmit={onSubmit} />);
    const group = screen.getByRole('group', { name: /one-time passcode/i });

    const pasteEvent = new Event('paste', { bubbles: true, cancelable: true });
    pasteEvent.clipboardData = { getData: () => '123-456' };
    fireEvent(group, pasteEvent);

    expect(onSubmit).toHaveBeenCalledWith('123456');
    const values = screen
      .getAllByRole('textbox')
      .map((input) => input.value)
      .join('');
    expect(values).toBe('123456');
  });

  it('moves focus with Backspace on an empty box and the arrow keys', () => {
    render(<OTPInput />);
    const inputs = screen.getAllByRole('textbox');

    inputs[1].focus();
    fireEvent.keyDown(inputs[1], { key: 'Backspace' });
    expect(document.activeElement).toBe(inputs[0]);

    fireEvent.keyDown(inputs[0], { key: 'ArrowRight' });
    expect(document.activeElement).toBe(inputs[1]);

    fireEvent.keyDown(inputs[1], { key: 'ArrowLeft' });
    expect(document.activeElement).toBe(inputs[0]);
  });

  // Finding (bug, fixed): `canResend` was `!onResend || countdown <= 0`, so the
  // button was enabled with no handler and the cooldown never ticked with one.
  it('disables resend when no handler is supplied', () => {
    render(<OTPInput />);
    const inputs = screen.getAllByRole('textbox');
    fireEvent.change(inputs[0], { target: { value: '9' } });

    // Without an onResend handler there is nothing to resend to — the button
    // must not pretend to work.
    expect(screen.getByRole('button', { name: /resend in \d+s/i })).toBeDisabled();
  });

  // Regression: the countdown effect used to skip when `onResend` was supplied,
  // leaving the button permanently disabled.
  it('counts down and enables resend, then calls the handler', () => {
    vi.useFakeTimers();
    try {
      const onResend = vi.fn();
      render(<OTPInput onResend={onResend} />);

      expect(screen.getByRole('button', { name: /resend in \d+s/i })).toBeDisabled();
      // Each tick schedules the next one from an effect, so advance one second
      // at a time (a single big jump would only process the first timer).
      for (let i = 0; i < 31; i += 1) {
        act(() => {
          vi.advanceTimersByTime(1000);
        });
      }

      const button = screen.getByRole('button', { name: 'Resend code' });
      expect(button).toBeEnabled();
      fireEvent.click(button);
      expect(onResend).toHaveBeenCalledTimes(1);
    } finally {
      vi.useRealTimers();
    }
  });

  it('disables entry and shows a spinner while loading, and surfaces errors', () => {
    render(<OTPInput loading error="That code expired" />);

    screen.getAllByRole('textbox').forEach((input) => expect(input).toBeDisabled());
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('That code expired');
  });

  it('supports custom title and subtitle', () => {
    render(<OTPInput title="Check your phone" subtitle="Enter the SMS code" />);

    expect(screen.getByRole('heading', { name: 'Check your phone' })).toBeInTheDocument();
    expect(screen.getByText('Enter the SMS code')).toBeInTheDocument();
  });
});
