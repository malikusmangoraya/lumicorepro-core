import { createRef } from 'react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Mail } from 'lucide-react';
import Input from '../../components/forms/Input';
import Textarea from '../../components/forms/Textarea';
import Select from '../../components/forms/Select';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('Input', () => {
  it('associates its label and helper text with the field', () => {
    render(<Input label="Email address" helperText="We never share it." />);

    const input = screen.getByLabelText('Email address');
    expect(input).toHaveAccessibleDescription('We never share it.');
    expect(input).toHaveAttribute('aria-invalid', 'false');
  });

  it('links an error message to the field and marks it invalid', () => {
    render(<Input label="Email" error="Enter a valid email" />);

    const input = screen.getByLabelText('Email');
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Enter a valid email');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(input).toHaveAttribute('aria-describedby', alert.id);
    expect(input.className).toContain('border-destructive');
  });

  it('shows a required marker that is hidden from screen readers', () => {
    render(<Input label="Company" required />);
    const marker = screen.getByText('*');
    expect(marker).toHaveAttribute('aria-hidden', 'true');
  });

  it('accepts typed input, forwards the ref and honours disabled', () => {
    const onChange = vi.fn();
    const ref = createRef();
    const { rerender } = render(<Input ref={ref} label="Name" onChange={onChange} />);

    const input = screen.getByLabelText('Name');
    expect(ref.current).toBe(input);
    fireEvent.change(input, { target: { value: 'Ada' } });
    expect(onChange).toHaveBeenCalledTimes(1);

    rerender(<Input ref={ref} label="Name" onChange={onChange} disabled />);
    expect(screen.getByLabelText('Name')).toBeDisabled();
  });

  it('toggles password visibility with a labelled control', () => {
    render(<Input label="Password" type="password" />);

    const input = screen.getByLabelText('Password');
    expect(input).toHaveAttribute('type', 'password');

    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    expect(input).toHaveAttribute('type', 'text');

    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    expect(input).toHaveAttribute('type', 'password');
  });

  it('renders lucide forwardRef left/right icons without crashing', () => {
    const { container } = render(
      <Input label="Contact" leftIcon={Mail} rightIcon={Mail} />
    );
    expect(screen.getByLabelText('Contact')).toBeTruthy();
    expect(container.querySelectorAll('svg')).toHaveLength(2);
    expect(screen.getByLabelText('Contact').className).toContain('pl-10');
  });
});

describe('Textarea', () => {
  it('associates its label and error message', () => {
    render(<Textarea label="Bio" error="Too short" />);

    const field = screen.getByLabelText('Bio');
    const alert = screen.getByRole('alert');
    expect(field).toHaveAttribute('aria-invalid', 'true');
    expect(field).toHaveAttribute('aria-describedby', alert.id);
    expect(alert).toHaveTextContent('Too short');
  });

  it('shows a character count for a controlled value', () => {
    render(
      <Textarea label="Bio" value="Hello" maxLength={20} showCount readOnly />
    );

    expect(screen.getByText('5/20')).toBeTruthy();
    expect(screen.getByLabelText('Bio')).toHaveAttribute('maxlength', '20');
  });

  it('forwards its ref, rows and disabled state', () => {
    const ref = createRef();
    render(<Textarea ref={ref} label="Notes" rows={6} disabled />);

    const field = screen.getByLabelText('Notes');
    expect(ref.current).toBe(field);
    expect(field).toHaveAttribute('rows', '6');
    expect(field).toBeDisabled();
  });

  it('falls back to a helper description when there is no error', () => {
    render(<Textarea label="Notes" helperText="Markdown supported" />);
    expect(screen.getByLabelText('Notes')).toHaveAccessibleDescription('Markdown supported');
  });
});

describe('Select', () => {
  it('associates its label and renders the supplied options', () => {
    render(
      <Select label="Plan" defaultValue="free">
        <option value="free">Free</option>
        <option value="pro">Pro</option>
      </Select>
    );

    const select = screen.getByLabelText('Plan');
    expect(select).toHaveValue('free');
    expect(screen.getByRole('option', { name: 'Pro' })).toBeTruthy();
  });

  it('reports errors through role=alert and aria-invalid', () => {
    render(
      <Select label="Country" error="Choose a country" defaultValue="">
        <option value="">Select...</option>
      </Select>
    );

    const select = screen.getByLabelText('Country');
    expect(select).toHaveAttribute('aria-invalid', 'true');
    expect(select.className).toContain('border-destructive');
    expect(screen.getByRole('alert')).toHaveTextContent('Choose a country');
  });

  it('fires onChange and forwards the ref and disabled state', () => {
    const onChange = vi.fn();
    const ref = createRef();
    const { rerender } = render(
      <Select ref={ref} label="Plan" defaultValue="free" onChange={onChange}>
        <option value="free">Free</option>
        <option value="pro">Pro</option>
      </Select>
    );

    const select = screen.getByLabelText('Plan');
    expect(ref.current).toBe(select);
    fireEvent.change(select, { target: { value: 'pro' } });
    expect(onChange).toHaveBeenCalledTimes(1);

    rerender(
      <Select ref={ref} label="Plan" defaultValue="free" onChange={onChange} disabled>
        <option value="free">Free</option>
      </Select>
    );
    expect(screen.getByLabelText('Plan')).toBeDisabled();
  });
});
