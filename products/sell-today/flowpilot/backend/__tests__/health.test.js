const request = require('supertest');
const { app } = require('../server');

describe('operational endpoints', () => {
  test('GET /health reports status and service name', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('OK');
    expect(res.body.service).toBeDefined();
    expect(res.body.timestamp).toBeDefined();
  });

  test('GET /ready reports ready', async () => {
    const res = await request(app).get('/ready');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ready');
  });

  test('an unknown path returns a structured response, never a crash', async () => {
    const res = await request(app).get('/api/definitely-not-a-route');
    expect([404, 400]).toContain(res.status);
  });
});
