/**
 * User Repository
 * ---------------
 * DB access for users + eager-loading helpers (e.g. orders, wishlist).
 * Services call these; controllers never touch Sequelize directly.
 */
import { BaseRepository } from './base.repository.js';
import User from '../models/User.js';

export class UserRepository extends BaseRepository {
  constructor() {
    super(User);
  }

  async findByEmail(email, scope = null) {
    const where = { email: (email || '').toLowerCase().trim() };
    if (scope === 'withPassword') {
      return User.scope('withPassword').findOne({ where });
    }
    return this.findOne(where);
  }

  /** User + their recent orders in ONE query (prevents N+1). */
  async findByIdWithRelations(id) {
    return this.findByIdWith(id, [
      { association: 'orders', limit: 10, order: [['createdAt', 'DESC']] },
      'wishlist',
      'cart',
    ]);
  }
}

export default new UserRepository();