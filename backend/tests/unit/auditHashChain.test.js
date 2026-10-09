import { describe, it, expect } from '@jest/globals';
import { canonicalAuditRow, computeAuditHash, verifyAuditChain } from '../../models/AuditLog.js';

describe('audit hash chain', () => {
  it('canonicalizes rows deterministically', () => {
    const a = canonicalAuditRow({ user_id: 1, action: 'x', meta: { b: 1, a: 2 }, created_at: new Date('2026-01-01T00:00:00Z') });
    const b = canonicalAuditRow({ user_id: 1, action: 'x', meta: { b: 1, a: 2 }, created_at: new Date('2026-01-01T00:00:00Z') });
    expect(a).toBe(b);
    expect(a).toContain('|x|');
  });

  it('hash changes when any covered field changes', () => {
    const base = { prev_hash: 'aa', user_id: 1, action: 'login', ip: '1.1.1.1', created_at: new Date('2026-01-01T00:00:00Z') };
    const h1 = computeAuditHash(base);
    const h2 = computeAuditHash({ ...base, action: 'logout' });
    const h3 = computeAuditHash({ ...base, prev_hash: 'bb' });
    expect(h1).not.toBe(h2);
    expect(h1).not.toBe(h3);
  });

  it('verify passes a well-formed chain', async () => {
    const rows = [];
    let prev = '';
    for (const action of ['a', 'b', 'c']) {
      const row = { id: rows.length + 1, prev_hash: prev, action, created_at: new Date(2026, 0, rows.length + 1) };
      row.hash = computeAuditHash(row);
      prev = row.hash;
      rows.push(row);
    }
    const model = { findAll: async () => rows };
    const result = await verifyAuditChain(model);
    expect(result.valid).toBe(true);
    expect(result.checked).toBe(3);
    expect(result.headHash).toBe(prev);
  });

  it('verify detects a modified row', async () => {
    const rows = [];
    let prev = '';
    for (const action of ['a', 'b']) {
      const row = { id: rows.length + 1, prev_hash: prev, action, created_at: new Date(2026, 0, rows.length + 1) };
      row.hash = computeAuditHash(row);
      prev = row.hash;
      rows.push(row);
    }
    rows[1].action = 'forged'; // tampered after hashing
    const model = { findAll: async () => rows };
    const result = await verifyAuditChain(model);
    expect(result.valid).toBe(false);
    expect(result.brokenAtId).toBe(2);
  });

  it('verify detects a deleted middle row', async () => {
    const mk = (id, prev, action, created) => {
      const row = { id, prev_hash: prev, action, created_at: created };
      row.hash = computeAuditHash(row);
      return row;
    };
    const r1 = mk(1, '', 'a', new Date(2026, 0, 1));
    const r2 = mk(2, r1.hash, 'b', new Date(2026, 0, 2));
    mk(3, r2.hash, 'c', new Date(2026, 0, 3));
    // r2 was deleted — r3 still points its prev_hash at r2.hash, so the chain
    // reported to verify() is r1 → r3 and breaks at r3.
    const r3 = mk(3, r2.hash, 'c', new Date(2026, 0, 3));
    const model = { findAll: async () => [r1, r3] };
    const result = await verifyAuditChain(model);
    expect(result.valid).toBe(false);
  });
});
