import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('*/api/ai/health', () =>
    HttpResponse.json({
      success: true,
      agent: { status: 'ok' },
      connected: true,
    })
  ),
];
