/**
 * Base Repository
 * ---------------
 * Thin data-access layer. Controllers → services → repositories → models.
 * Repositories own ALL Sequelize/raw DB access; services own business logic.
 * Includes eager-load helpers to prevent N+1 query patterns.
 */
export class BaseRepository {
  constructor(model) {
    this.model = model || null;
  }

  /** Find one by primary key with optional eager-load include. */
  async findById(id, { include = null } = {}) {
    const opts = include ? { include } : {};
    return this.model.findByPk(id, opts);
  }

  /** Eager-load relations in a single query instead of per-row queries. */
  async findByIdWith(id, relations = []) {
    return this.findById(id, { include: relations });
  }

  async findOne(where = {}, opts = {}) {
    return this.model.findOne({ where, ...opts });
  }

  /**
   * Eager-loading finder: `include` accepts an array of model associations
   * (or `{ association, include }` for nested) → single query, no N+1.
   */
  async findAll(where = {}, { include = [], limit, offset, order, attributes } = {}) {
    return this.model.findAll({ where, include, limit, offset, order, attributes });
  }

  async create(data, opts = {}) {
    return this.model.create(data, opts);
  }

  async update(id, data, opts = {}) {
    const instance = await this.model.findByPk(id);
    if (!instance) return null;
    return instance.update(data, opts);
  }

  async delete(id) {
    const instance = await this.model.findByPk(id);
    if (!instance) return null;
    await instance.destroy();
    return true;
  }

  async count(where = {}) {
    return this.model.count({ where });
  }

  /** Run a block inside a DB transaction (local env) — intended for checkout. */
  async transaction(fn) {
    const { sequelize } = await import('../config/database.js');
    return sequelize.transaction(fn);
  }
}

export default BaseRepository;