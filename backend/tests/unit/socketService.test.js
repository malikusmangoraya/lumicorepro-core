import { describe, it, expect } from '@jest/globals';
import { socketMode, setupSocketScaling } from '../../services/socket.service.js';

describe('Socket.IO scaling', () => {
  it('is standalone when Redis is explicitly disabled', () => {
    expect(socketMode({ REDIS_DISABLED: 'true' })).toBe('standalone');
    expect(socketMode({ REDIS_DISABLED: 'TRUE' })).toBe('standalone');
  });

  it('prefers clustered mode otherwise', () => {
    expect(socketMode({})).toBe('clustered');
    expect(socketMode({ REDIS_DISABLED: 'false' })).toBe('clustered');
  });

  it('returns standalone without attaching when disabled (no Redis touched)', async () => {
    const io = { adapter: () => { throw new Error('must not be called'); } };
    const result = await setupSocketScaling(io, { REDIS_DISABLED: 'true' });
    expect(result).toEqual({ clustered: false, mode: 'standalone' });
  });

  it('fails open to standalone when Redis is unreachable', async () => {
    const attached = [];
    const io = { adapter: (a) => attached.push(a) };
    const result = await setupSocketScaling(io, {
      REDIS_URL: 'redis://127.0.0.1:9',
      REDIS_DISABLED: 'false',
    });
    expect(result.clustered).toBe(false);
    expect(result.mode).toBe('standalone');
    expect(attached).toHaveLength(0);
  }, 15000);
});
