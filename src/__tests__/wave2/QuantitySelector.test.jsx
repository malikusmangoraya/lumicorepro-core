import { useState } from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import QuantitySelector from '../../components/ecommerce/QuantitySelector';

function Controlled({ initialValue = 1, onChange, ...props }) {
  const [value, setValue] = useState(initialValue);
  return (
    <QuantitySelector
      value={value}
      onChange={(next) => {
        setValue(next);
        onChange?.(next);
      }}
      {...props}
    />
  );
}

describe('QuantitySelector', () => {
  it('renders a labelled numeric input with decrement disabled at the minimum', () => {
    render(<Controlled />);
    const input = screen.getByLabelText('Quantity');

    expect(input).toHaveValue(1);
    expect(input).toHaveAttribute('type', 'number');
    expect(input).toHaveAttribute('min', '1');
    expect(input).toHaveAttribute('max', '99');
    expect(screen.getByRole('button', { name: 'Decrease quantity' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Increase quantity' })).toBeEnabled();
  });

  it('steps the value up and down through onChange', () => {
    const onChange = vi.fn();
    render(<Controlled onChange={onChange} />);
    const input = screen.getByLabelText('Quantity');

    fireEvent.click(screen.getByRole('button', { name: 'Increase quantity' }));
    expect(onChange).toHaveBeenLastCalledWith(2);
    expect(input).toHaveValue(2);

    fireEvent.click(screen.getByRole('button', { name: 'Increase quantity' }));
    expect(onChange).toHaveBeenLastCalledWith(3);

    fireEvent.click(screen.getByRole('button', { name: 'Decrease quantity' }));
    expect(onChange).toHaveBeenLastCalledWith(2);
  });

  it('parses typed input and clamps it to the min/max range', () => {
    const onChange = vi.fn();
    render(<Controlled onChange={onChange} max={10} />);
    const input = screen.getByLabelText('Quantity');

    fireEvent.change(input, { target: { value: '0' } });
    expect(onChange).toHaveBeenLastCalledWith(1);
    expect(input).toHaveValue(1);

    fireEvent.change(input, { target: { value: '99' } });
    expect(onChange).toHaveBeenLastCalledWith(10);
    expect(input).toHaveValue(10);
    expect(screen.getByRole('button', { name: 'Increase quantity' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Decrease quantity' })).toBeEnabled();
  });

  it('ignores non-numeric input', () => {
    const onChange = vi.fn();
    render(<Controlled onChange={onChange} />);
    const input = screen.getByLabelText('Quantity');

    fireEvent.change(input, { target: { value: 'abc' } });

    expect(onChange).not.toHaveBeenCalled();
    expect(input).toHaveValue(1);
  });

  it('disables both buttons when min and max meet', () => {
    render(<Controlled initialValue={5} min={5} max={5} />);

    expect(screen.getByRole('button', { name: 'Decrease quantity' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Increase quantity' })).toBeDisabled();
  });

  it('supports a custom accessible label and survives a missing onChange', () => {
    const { rerender } = render(<QuantitySelector value={2} label="Seats" />);
    const input = screen.getByLabelText('Seats');
    expect(input).toHaveValue(2);

    fireEvent.click(screen.getByRole('button', { name: 'Increase quantity' }));
    fireEvent.click(screen.getByRole('button', { name: 'Decrease quantity' }));
    expect(input).toHaveValue(2);

    rerender(<QuantitySelector value={2} label="Seats" size="lg" />);
    expect(screen.getByLabelText('Seats')).toHaveValue(2);
  });
});
