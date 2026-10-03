import { describe, expect, it } from 'vitest';
import { aiAgentAPI } from '../services/api';

describe('API mock server', () => {
  it('intercepts AI agent health requests', async () => {
    const response = await aiAgentAPI.checkHealth();

    expect(response.data).toEqual({
      success: true,
      agent: { status: 'ok' },
      connected: true,
    });
  });
});
