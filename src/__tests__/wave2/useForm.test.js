import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import useForm from '../../hooks/useForm';

const initialValues = { email: '', password: '', remember: false };

function setup(overrides = {}) {
  const props = {
    initialValues,
    onSubmit: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  };
  const hook = renderHook((p) => useForm(p), { initialProps: props });
  return { ...hook, props };
}

describe('useForm — field state', () => {
  it('exposes initial values and tracks text input changes', () => {
    const { result } = setup();

    expect(result.current.values).toEqual(initialValues);
    expect(result.current.errors).toEqual({});
    expect(result.current.touched).toEqual({});

    act(() => {
      result.current.handleChange({ target: { name: 'email', value: 'ada@example.com', type: 'email' } });
    });
    act(() => {
      result.current.handleChange({ target: { name: 'password', value: 'secret', type: 'password' } });
    });

    expect(result.current.values).toEqual({
      email: 'ada@example.com',
      password: 'secret',
      remember: false,
    });
  });

  it('stores the checked flag for checkboxes', () => {
    const { result } = setup();

    act(() => {
      result.current.handleChange({ target: { name: 'remember', type: 'checkbox', checked: true } });
    });
    expect(result.current.values.remember).toBe(true);

    act(() => {
      result.current.handleChange({ target: { name: 'remember', type: 'checkbox', checked: false } });
    });
    expect(result.current.values.remember).toBe(false);
  });

  it('marks fields touched on blur only for the blurred field', () => {
    const { result } = setup();

    act(() => {
      result.current.handleBlur({ target: { name: 'email' } });
    });

    expect(result.current.touched).toEqual({ email: true });
  });

  it('supports programmatic field values and errors', () => {
    const { result } = setup();

    act(() => result.current.setFieldValue('email', 'manual@example.com'));
    act(() => result.current.setFieldError('email', 'Already taken'));

    expect(result.current.values.email).toBe('manual@example.com');
    expect(result.current.errors.email).toBe('Already taken');
  });
});

describe('useForm — validation', () => {
  it('blocks submission and records errors when validation fails', async () => {
    const validate = vi.fn(() => ({ email: 'Email is required' }));
    const { result, props } = setup({ validate, initialValues: { email: '', password: '' } });
    const event = { preventDefault: vi.fn() };

    await act(async () => {
      await result.current.handleSubmit(event);
    });

    expect(event.preventDefault).toHaveBeenCalledTimes(1);
    expect(validate).toHaveBeenCalledWith({ email: '', password: '' });
    expect(result.current.errors).toEqual({ email: 'Email is required' });
    expect(result.current.touched).toEqual({ email: true, password: true });
    expect(result.current.submitCount).toBe(0);
    expect(result.current.isSubmitting).toBe(false);
    expect(props.onSubmit).not.toHaveBeenCalled();
  });

  it('submits when validation passes and clears stale errors', async () => {
    const validate = vi.fn(() => ({}));
    const { result, props } = setup({
      validate,
      initialValues: { email: 'ada@example.com', password: 'secret' },
    });

    await act(async () => {
      await result.current.handleSubmit({ preventDefault: vi.fn() });
    });

    expect(props.onSubmit).toHaveBeenCalledWith({
      email: 'ada@example.com',
      password: 'secret',
    });
    expect(result.current.errors).toEqual({});
    expect(result.current.submitCount).toBe(1);
    expect(result.current.isSubmitting).toBe(false);
  });

  it('submits without a validation function or an event', async () => {
    const { result, props } = setup();

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(props.onSubmit).toHaveBeenCalledWith(initialValues);
    expect(result.current.submitCount).toBe(1);
  });

  it('counts each successful submit', async () => {
    const { result } = setup();

    await act(async () => {
      await result.current.handleSubmit();
      await result.current.handleSubmit();
    });

    expect(result.current.submitCount).toBe(2);
  });
});

describe('useForm — submission lifecycle', () => {
  it('flags isSubmitting while onSubmit is pending', async () => {
    let finish;
    const onSubmit = vi.fn(() => new Promise((resolve) => {
      finish = resolve;
    }));
    const { result } = setup({ onSubmit });

    let pending;
    await act(async () => {
      pending = result.current.handleSubmit();
    });
    expect(result.current.isSubmitting).toBe(true);

    await act(async () => {
      finish();
      await pending;
    });

    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.submitCount).toBe(1);
  });

  it('swallows onSubmit rejections and still resets isSubmitting', async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error('server down'));
    const { result } = setup({ onSubmit });

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(result.current.isSubmitting).toBe(false);
    expect(result.current.submitCount).toBe(1);
  });

  it('resetForm restores initial values, errors, touched and submit count', async () => {
    const { result } = setup();

    act(() => {
      result.current.handleChange({ target: { name: 'email', value: 'x@example.com', type: 'text' } });
      result.current.handleBlur({ target: { name: 'email' } });
      result.current.setFieldError('email', 'Bad email');
    });
    await act(async () => {
      await result.current.handleSubmit();
    });

    act(() => result.current.resetForm());

    expect(result.current.values).toEqual(initialValues);
    expect(result.current.errors).toEqual({});
    expect(result.current.touched).toEqual({});
    expect(result.current.submitCount).toBe(0);
    expect(result.current.isSubmitting).toBe(false);
  });
});
