import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';
import {
  agentEndpointUrl,
  agentPreviewUrl,
  agentWebSocketUrl,
  fetchAgentJson,
  slugifyProjectName,
} from '../../utils/aiAgent.js';
import { queuedAI } from '../../services/aiCost/queue.service.js';

describe('AI-agent upstream helpers', () => {
  const originalFetch = global.fetch;
  const originalAgentUrl = process.env.AI_AGENT_URL;

  beforeEach(() => {
    process.env.AI_AGENT_URL = 'https://agent.example:8443/agent';
    global.fetch = jest.fn();
  });

  afterEach(() => {
    if (originalAgentUrl === undefined) delete process.env.AI_AGENT_URL;
    else process.env.AI_AGENT_URL = originalAgentUrl;
    global.fetch = originalFetch;
  });

  it('preserves the configured HTTPS origin for API, preview, and socket URLs', () => {
    expect(agentEndpointUrl('/api/runs/123')).toBe('https://agent.example:8443/api/runs/123');
    expect(agentPreviewUrl('my site', 'assets/logo.png')).toBe(
      'https://agent.example:8443/preview/my%20site/assets%2Flogo.png'
    );
    expect(agentWebSocketUrl('run-123')).toBe('wss://agent.example:8443/ws/generate/run-123');
  });

  it('rejects non-HTTP(S) agent URLs instead of proxying to them', () => {
    for (const value of ['file:///etc/passwd', 'gopher://agent.example/', 'not a url']) {
      expect(() => agentEndpointUrl('/api/health', value)).toThrow(/Invalid AI_AGENT_URL/);
    }
  });

  it('slugifies optional input without crashing on missing values', () => {
    expect(slugifyProjectName('My Awesome Store!')).toBe('my-awesome-store');
    expect(slugifyProjectName(undefined)).toBe('generated-website');
    expect(slugifyProjectName('!!!')).toBe('generated-website');
  });

  it('aborts a hung upstream request and reports a timeout', async () => {
    global.fetch.mockImplementation(() => new Promise(() => {}));

    await expect(fetchAgentJson('/api/health', { timeoutMs: 5 })).rejects.toMatchObject({
      code: 'FETCH_TIMEOUT',
    });
  });

  it('retains upstream status codes for retry decisions', async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 429, text: async () => 'slow down' });

    const error = await fetchAgentJson('/api/health').catch((err) => err);

    expect(error).toBeInstanceOf(Error);
    expect(error.status).toBe(429);
    expect(String(error.message)).toContain('429');
  });

  it('releases queue capacity after successful calls', async () => {
    const calls = [];
    const job = async () => {
      calls.push('ok');
      return 'ok';
    };

    for (let i = 0; i < 3; i += 1) {
      await expect(
        queuedAI(job, { queueKind: 'chat', maxRetries: 1, timeoutMs: 1000 })
      ).resolves.toBe('ok');
    }

    expect(calls).toHaveLength(3);
  });
});
