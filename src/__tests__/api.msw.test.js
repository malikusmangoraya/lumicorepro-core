import { describe, expect, it } from 'vitest';
import { http, HttpResponse } from 'msw';
import { aiAgentAPI } from '../services/api';
import { server } from '../test/mocks/server';

describe('API mock server', () => {
  it('intercepts AI agent health requests', async () => {
    const response = await aiAgentAPI.checkHealth();

    expect(response.data).toEqual({
      success: true,
      agent: { status: 'ok' },
      connected: true,
    });
  });

  it('loads the backend technology catalog through the Express API', async () => {
    const catalog = { version: '1.0', languages: { python: { label: 'Python' } } };
    server.use(
      http.get('*/api/ai/technology-catalog', () =>
        HttpResponse.json({ success: true, data: { catalog } })
      )
    );

    const response = await aiAgentAPI.getTechnologyCatalog();

    expect(response.data).toEqual({ success: true, data: { catalog } });
  });
});
