import { describe, it, expect, beforeEach, jest } from '@jest/globals';

/**
 * The ioredis mock is installed before the service module loads so the
 * clustered path can be exercised without a live Redis.
 */
const mockRedisInstance = {
  duplicate: jest.fn(),
  connect: jest.fn(async () => {}),
  ping: jest.fn(async () => 'PONG'),
  quit: jest.fn(async () => 'OK'),
};
const MockRedis = jest.fn(() => mockRedisInstance);

jest.unstable_mockModule('ioredis', () => ({ default: MockRedis }));

const { socketMode, setupSocketScaling } = await import('../../services/socket.service.js');

// jest.config.js sets `resetMocks: true`, which strips implementations from
// module-scope mocks before every test — rebind them here or the service would
// construct an undefined client.
beforeEach(() => {
  MockRedis.mockImplementation(() => mockRedisInstance);
  mockRedisInstance.duplicate.mockImplementation(() => mockRedisInstance);
  mockRedisInstance.connect.mockImplementation(async () => {});
  mockRedisInstance.ping.mockImplementation(async () => 'PONG');
  mockRedisInstance.quit.mockImplementation(async () => 'OK');
});

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
    mockRedisInstance.ping.mockImplementationOnce(async () => {
      throw new Error('ECONNREFUSED');
    });
    const result = await setupSocketScaling(io, {
      REDIS_URL: 'redis://127.0.0.1:9',
      REDIS_DISABLED: 'false',
    });
    expect(result.clustered).toBe(false);
    expect(result.mode).toBe('standalone');
    expect(attached).toHaveLength(0);
  }, 15000);

  it('attaches the Redis adapter and reports clustered when Redis answers', async () => {
    const attached = [];
    const io = { adapter: (a) => attached.push(a) };
    const result = await setupSocketScaling(io, { REDIS_URL: 'redis://127.0.0.1:6379' });
    expect(result).toEqual({ clustered: true, mode: 'clustered' });
    expect(attached).toHaveLength(1);
  }, 15000);
});
