import { describe, it, expect, jest, beforeEach } from '@jest/globals';

function mockModel() {
  return {
    findByPk: jest.fn(),
    findAll: jest.fn(async () => []),
    findOne: jest.fn(async () => null),
    update: jest.fn(async () => [1]),
    destroy: jest.fn(async () => 0),
  };
}

const models = {
  User: mockModel(),
  Order: mockModel(),
  Payment: mockModel(),
  Review: mockModel(),
  Cart: mockModel(),
  Wishlist: mockModel(),
  Subscription: mockModel(),
  Address: mockModel(),
  Notification: mockModel(),
  Membership: mockModel(),
  AuditLog: mockModel(),
};

jest.unstable_mockModule('../../models/User.js', () => ({ __esModule: true, default: models.User }));
jest.unstable_mockModule('../../models/Order.js', () => ({ __esModule: true, default: models.Order }));
jest.unstable_mockModule('../../models/Payment.js', () => ({ __esModule: true, default: models.Payment }));
jest.unstable_mockModule('../../models/Review.js', () => ({ __esModule: true, default: models.Review }));
jest.unstable_mockModule('../../models/Cart.js', () => ({ __esModule: true, default: models.Cart }));
jest.unstable_mockModule('../../models/Wishlist.js', () => ({ __esModule: true, default: models.Wishlist }));
jest.unstable_mockModule('../../models/Subscription.js', () => ({ __esModule: true, default: models.Subscription }));
jest.unstable_mockModule('../../models/Address.js', () => ({ __esModule: true, default: models.Address }));
jest.unstable_mockModule('../../models/Notification.js', () => ({ __esModule: true, default: models.Notification }));
jest.unstable_mockModule('../../models/Membership.js', () => ({ __esModule: true, default: models.Membership }));
jest.unstable_mockModule('../../models/AuditLog.js', () => ({ __esModule: true, default: models.AuditLog }));
jest.unstable_mockModule('../../config/database.js', () => ({
  __esModule: true,
  sequelize: { transaction: (cb) => Promise.resolve(cb('tx')) },
}));

const { exportUserData, eraseUserData } = await import('../../services/privacy.service.js');

describe('Privacy service (DSR)', () => {
  beforeEach(() => {
    for (const m of Object.values(models)) {
      m.findByPk.mockReset();
      m.findAll.mockReset().mockResolvedValue([]);
      m.findOne.mockReset().mockResolvedValue(null);
      m.update.mockReset().mockResolvedValue([1]);
      m.destroy.mockReset().mockResolvedValue(0);
    }
  });

  it('export strips the password hash and covers every table', async () => {
    models.User.findByPk.mockResolvedValue({ id: 9, email: 'a@b.c', password: 'hash' });
    models.Order.findAll.mockResolvedValue([{ id: 1 }]);

    const data = await exportUserData(9);

    expect(data.user.password).toBeUndefined();
    expect(data.orders).toHaveLength(1);
    for (const key of ['payments', 'reviews', 'wishlist', 'subscriptions', 'addresses', 'memberships', 'auditLogs']) {
      expect(data[key]).toBeDefined();
    }
    expect(data.exportedAt).toBeTruthy();
  });

  it('erase anonymizes identity, deletes non-essentials, retains ledger', async () => {
    const update = jest.fn(async () => [1]);
    models.User.findByPk.mockResolvedValue({ id: 9, update });

    const report = await eraseUserData(9);

    expect(update).toHaveBeenCalledTimes(1);
    const anon = update.mock.calls[0][0];
    expect(anon.name).toBe('Deleted User');
    expect(anon.email).toContain('@deleted.local');
    expect(anon.password).not.toBe('hash');
    expect(anon.isActive).toBe(false);
    expect(models.Review.update).toHaveBeenCalledTimes(1);
    for (const m of [models.Cart, models.Wishlist, models.Address, models.Notification, models.Membership]) {
      expect(m.destroy).toHaveBeenCalledTimes(1);
    }
    expect(report.anonymized).toEqual(['users', 'reviews']);
    expect(report.retained.map((r) => r.table)).toEqual(
      expect.arrayContaining(['orders', 'payments', 'subscriptions', 'audit_logs'])
    );
  });

  it('erase of a missing account is a 404, not a silent no-op', async () => {
    models.User.findByPk.mockResolvedValue(null);
    const err = await eraseUserData(9).catch((e) => e);
    expect(err.statusCode).toBe(404);
  });
});
