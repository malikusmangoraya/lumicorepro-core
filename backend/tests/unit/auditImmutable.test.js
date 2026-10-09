import { describe, it, expect, jest } from '@jest/globals';
import AuditLog, { purgeAuditLogs } from '../../models/AuditLog.js';

describe('AuditLog immutability', () => {
  it('refuses instance updates without touching the database', async () => {
    const row = AuditLog.build({ id: 1, action: 'test', created_at: new Date() }, { isNewRecord: false });
    await expect(row.update({ action: 'forged' })).rejects.toThrow(/immutable/);
  });

  it('refuses instance deletes without touching the database', async () => {
    const row = AuditLog.build({ action: 'test', created_at: new Date() });
    await expect(row.destroy()).rejects.toThrow(/immutable/);
  });

  it('purge path deletes only rows older than the cutoff', async () => {
    const query = jest.fn(async () => [undefined, { rowCount: 41 }]);
    const deleted = await purgeAuditLogs(new Date('2020-01-01'), { query });

    expect(deleted).toBe(41);
    expect(query).toHaveBeenCalledTimes(1);
    const [sql, opts] = query.mock.calls[0];
    expect(sql).toMatch(/DELETE FROM audit_logs/);
    expect(sql).toMatch(/created_at < :before/);
    expect(opts.replacements.before).toEqual(new Date('2020-01-01'));
  });
});
