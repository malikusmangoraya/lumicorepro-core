import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  describeError,
  notify,
  notifyError,
  registerNotificationHandler,
} from '../../services/notificationBus';

afterEach(() => {
  // Drop any handler a test forgot to unregister so tests stay isolated.
  registerNotificationHandler(null)();
});

describe('notificationBus', () => {
  it('drops notifications while no toast surface is mounted', () => {
    const handler = vi.fn();
    notify('nobody listening');
    expect(handler).not.toHaveBeenCalled();
    expect(() => notify('')).not.toThrow();
  });

  it('forwards messages with a default info type and supports unregistering', () => {
    const handler = vi.fn();
    const unregister = registerNotificationHandler(handler);

    notify('Saved');
    notify('Boom', 'error');

    expect(handler).toHaveBeenNthCalledWith(1, 'Saved', 'info');
    expect(handler).toHaveBeenNthCalledWith(2, 'Boom', 'error');

    unregister();
    notify('ignored');
    expect(handler).toHaveBeenCalledTimes(2);
  });

  it('does not let a stale unregister remove a newer handler', () => {
    const first = vi.fn();
    const second = vi.fn();
    const unregisterFirst = registerNotificationHandler(first);
    registerNotificationHandler(second);

    unregisterFirst();
    notify('still delivered');

    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledWith('still delivered', 'info');
  });

  it('prefers the API message, then the API error, then Error.message, then the fallback', () => {
    expect(describeError({ response: { data: { message: 'API said no' } } })).toBe('API said no');
    expect(describeError({ response: { data: { error: 'Bad request' } } })).toBe('Bad request');
    expect(describeError(new Error('network down'))).toBe('network down');
    expect(describeError({}, 'Custom fallback')).toBe('Custom fallback');
  });

  it('reports failures through the toast handler as an error', () => {
    const handler = vi.fn();
    registerNotificationHandler(handler);

    notifyError({ response: { data: { message: 'Payment failed' } } });

    expect(handler).toHaveBeenCalledWith('Payment failed', 'error');
  });
});
