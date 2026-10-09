/**
 * Privacy service — GDPR data subject rights (DSR).
 *
 * exportUserData(userId)  → every row the platform holds about the user.
 * eraseUserData(userId)   → anonymizes the account in place and deletes
 *   non-essential rows. Financial records (orders/payments) are RETAINED but
 *   detached from the identity: the user row itself is anonymized, so the
 *   ledger keeps integrity without keeping personal data. The full report of
 *   what was kept vs deleted is returned — erasure is never silent.
 */
import crypto from 'crypto';
import User from '../models/User.js';
import Order from '../models/Order.js';
import Payment from '../models/Payment.js';
import Review from '../models/Review.js';
import Cart from '../models/Cart.js';
import Wishlist from '../models/Wishlist.js';
import Subscription from '../models/Subscription.js';
import Address from '../models/Address.js';
import Notification from '../models/Notification.js';
import Membership from '../models/Membership.js';
import AuditLog from '../models/AuditLog.js';
import { sequelize } from '../config/database.js';

const ANON_NAME = 'Deleted User';

export async function exportUserData(userId) {
  const [user, orders, payments, reviews, cart, wishlist, subscriptions, addresses, memberships, auditLogs] =
    await Promise.all([
      User.findByPk(userId, { raw: true }),
      Order.findAll({ where: { user_id: userId }, raw: true }),
      Payment.findAll({ where: { user_id: userId }, raw: true }),
      Review.findAll({ where: { user_id: userId }, raw: true }),
      Cart.findOne({ where: { user_id: userId }, raw: true }),
      Wishlist.findAll({ where: { user_id: userId }, raw: true }),
      Subscription.findAll({ where: { user_id: userId }, raw: true }),
      Address.findAll({ where: { user_id: userId }, raw: true }),
      Membership.findAll({ where: { user_id: userId }, raw: true }),
      AuditLog.findAll({ where: { user_id: userId }, raw: true }),
    ]);
  if (user) delete user.password;
  return {
    user,
    orders,
    payments,
    reviews,
    cart,
    wishlist,
    subscriptions,
    addresses,
    memberships,
    auditLogs,
    exportedAt: new Date().toISOString(),
  };
}

export async function eraseUserData(userId) {
  const anonEmail = `deleted-${userId}-${crypto.randomBytes(4).toString('hex')}@deleted.local`;
  const report = { anonymized: [], deleted: [], retained: [] };

  await sequelize.transaction(async (t) => {
    const user = await User.findByPk(userId, { transaction: t });
    if (!user) {
      const err = new Error('Account not found');
      err.statusCode = 404;
      throw err;
    }

    await user.update(
      {
        name: ANON_NAME,
        email: anonEmail,
        password: crypto.randomBytes(32).toString('hex'),
        avatar: '',
        phone: '',
        oauthId: null,
        oauthProvider: null,
        verificationToken: null,
        verificationExpires: null,
        resetPasswordToken: null,
        resetPasswordExpires: null,
        twoFactorEnabled: false,
        twoFactorSecret: null,
        isActive: false,
        preferences: {},
      },
      { transaction: t }
    );
    report.anonymized.push('users');

    await Review.update(
      { userName: ANON_NAME, userAvatar: '' },
      { where: { user_id: userId }, transaction: t }
    );
    report.anonymized.push('reviews');

    const deleted = await Promise.all([
      Cart.destroy({ where: { user_id: userId }, transaction: t }),
      Wishlist.destroy({ where: { user_id: userId }, transaction: t }),
      Address.destroy({ where: { user_id: userId }, transaction: t }),
      Notification.destroy({ where: { recipient: userId }, transaction: t }),
      Membership.destroy({ where: { user_id: userId }, transaction: t }),
    ]);
    report.deleted.push(
      { table: 'carts', rows: deleted[0] },
      { table: 'wishlists', rows: deleted[1] },
      { table: 'addresses', rows: deleted[2] },
      { table: 'notifications', rows: deleted[3] },
      { table: 'memberships', rows: deleted[4] }
    );

    // Financial + audit history stays for tax/fraud/legal retention, but the
    // identity it pointed at no longer exists as personal data.
    report.retained.push(
      { table: 'orders', reason: 'financial/legal retention (identity anonymized)' },
      { table: 'payments', reason: 'financial/legal retention (identity anonymized)' },
      { table: 'subscriptions', reason: 'billing history (identity anonymized)' },
      { table: 'audit_logs', reason: 'security trail (identity anonymized)' }
    );
  });

  return { userId, ...report, erasedAt: new Date().toISOString() };
}
