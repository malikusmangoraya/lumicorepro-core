import { describe, it, expect } from '@jest/globals';
import http from 'http';
import express from 'express';
import {
  tracingMiddleware,
  downstreamTraceHeaders,
  parseTraceparent,
  formatTraceparent,
} from '../../middleware/tracing.js';

function makeApp() {
  const app = express();
  app.use(tracingMiddleware);
  app.get('/x', (req, res) => {
    res.json({ traceId: req.traceId, downstream: downstreamTraceHeaders() });
  });
  return app;
}

function request(app) {
  const server = http.createServer(app);
  return new Promise((resolve, reject) => {
    server.listen(0, () => {
      const { port } = server.address();
      import('node:http').then(({ default: httpMod }) => {
        const req = httpMod.get({ port, path: '/x' }, (res) => {
          let body = '';
          res.on('data', (c) => { body += c; });
          res.on('end', () => {
            server.close();
            resolve({ res, body: JSON.parse(body) });
          });
        });
        req.on('error', reject);
      });
    });
  });
}

describe('W3C trace context', () => {
  it('round-trips parse/format', () => {
    const tp = '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01';
    const parsed = parseTraceparent(tp);
    expect(parsed).toEqual({ traceId: '4bf92f3577b34da6a3ce929d0e0e4736', spanId: '00f067aa0ba902b7', flags: '01' });
    expect(parseTraceparent('garbage')).toBeNull();
    expect(formatTraceparent(parsed.traceId, parsed.spanId)).toBe(tp);
  });

  it('starts a trace when none is provided and echoes it', async () => {
    const { res, body } = await request(makeApp());
    expect(res.headers['x-trace-id']).toMatch(/^[0-9a-f]{32}$/);
    expect(body.traceId).toBe(res.headers['x-trace-id']);
    expect(res.headers.traceparent).toContain(body.traceId);
  });

  it('continues an incoming trace across the request', async () => {
    const incoming = '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01';
    const server = http.createServer(makeApp());
    const port = await new Promise((resolve) => {
      server.listen(0, () => resolve(server.address().port));
    });
    const { default: httpMod } = await import('node:http');
    const result = await new Promise((resolve, reject) => {
      const req = httpMod.get({ port, path: '/x', headers: { traceparent: incoming } }, (res) => {
        let raw = '';
        res.on('data', (c) => { raw += c; });
        res.on('end', () => { resolve({ res, body: JSON.parse(raw) }); });
      });
      req.on('error', reject);
    });
    server.close();
    expect(result.body.traceId).toBe('4bf92f3577b34da6a3ce929d0e0e4736');
    expect(result.body.downstream.traceparent).toContain('4bf92f3577b34da6a3ce929d0e0e4736');
    expect(result.body.downstream['x-trace-id']).toBe('4bf92f3577b34da6a3ce929d0e0e4736');
    // Each hop is a new span — the outgoing span id differs from the incoming.
    expect(result.body.downstream.traceparent).not.toBe(incoming);
  });
});
