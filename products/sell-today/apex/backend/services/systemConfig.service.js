import SystemConfig from '../models/SystemConfig.js';
import { getRedis, isRedisAvailable } from './cache/redis.client.js';
import logger from '../utils/logger.js';

/**
 * SystemConfigService — runtime configuration store.
 *
 * Session-level truth lives in PostgreSQL (SystemConfig table). A warm cache
 * sits in Redis (JSON blob) with an in-memory Map fallback so every request
 * reads credentials from the cache, never hardcoded env.
 *
 * Usage:
 *   import systemConfig from './systemConfig.service.js';
 *   const stripeKeys = await systemConfig.get('payments', {});
 *   const ctx = await systemConfig.getAll();
 *   await systemConfig.set('payments', { stripe: {...}, paypal: {...} });
 */

const CACHE_KEY = 'system_config:full';
const TTL_SECONDS = 300;

const defaults = {
  business: {
    name: '',
    tagline: '',
    logoUrl: '',
    supportEmail: '',
  },
  currency: {
    code: 'USD',
    symbol: '$',
  },
  payments: {
    stripe: {
      enabled: false,
      mode: 'sandbox',
      secretKey: '',
      publishableKey: '',
      webhookSecret: '',
    },
    paypal: {
      enabled: false,
      mode: 'sandbox',
      clientId: '',
      clientSecret: '',
      webhookId: '',
    },
  },
  smtp: {
    enabled: false,
    host: '',
    port: 587,
    secure: false,
    user: '',
    pass: '',
    fromName: '',
    fromEmail: '',
  },
  setup: {
    completed: false,
    completedAt: null,
    superAdminEmail: '',
    businessNiche: '',
  },
};

const deepMerge = (base, override) => {
  const out = Array.isArray(base) ? [...base] : { ...base };
  for (const [k, v] of Object.entries(override || {})) {
    if (
      out[k] &&
      typeof out[k] === 'object' &&
      !Array.isArray(out[k]) &&
      v &&
      typeof v === 'object' &&
      !Array.isArray(v)
    ) {
      out[k] = deepMerge(out[k], v);
    } else {
      out[k] = v;
    }
  }
  return out;
};

class SystemConfigService {
  constructor() {
    this.memory = {};
    this.memoryLoaded = false;
  }

  /**
   * Return an in-memory/redis cached snapshot without hitting the DB for reads.
   */
  _snapshot() {
    return deepMerge(defaults, this.memory);
  }

  /**
   * Whether the DB is actually reachable (fail-open when offline so dev/demo
   * flows keep working and setup redirect does not lock everyone out).
   */
  _dbAvailable() {
    try {
      const db = SystemConfig?.sequelize ?? null;
      return Boolean(db && db.connectionManager && db.connectionManager.pool);
    } catch {
      return false;
    }
  }

  async _loadFromRedis() {
    try {
      const redis = getRedis();
      if (!redis?.isReady && !isRedisAvailable()) return null;
      const raw = await redis.get(CACHE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  async _storeInRedis() {
    try {
      const redis = getRedis();
      if (!redis?.isReady && !isRedisAvailable()) return;
      await redis.set(CACHE_KEY, JSON.stringify(this.memory), 'EX', TTL_SECONDS);
    } catch {
      /* cache is optional */
    }
  }

  async _loadFromDb() {
    try {
      const rows = await SystemConfig.findAll({ raw: true });
      this.memory = {};
      for (const row of rows) {
        this.memory[row.key] = row.value;
      }
      this.memoryLoaded = true;
      return this.memory;
    } catch (err) {
      logger.warn(`SystemConfig DB load failed (using defaults): ${err.message}`);
      this.memoryLoaded = false;
      return {};
    }
  }

  /**
   * Warm the full cache. Called once at server boot and after every mutation.
   */
  async refresh() {
    const fromRedis = await this._loadFromRedis();
    if (fromRedis && Object.keys(fromRedis).length > 0) {
      this.memory = fromRedis;
      this.memoryLoaded = true;
      return this.memory;
    }
    return this._loadFromDb();
  }

  /**
   * Get a merged config snapshot. Local memory → Redis → DB → defaults.
   */
  async getAll() {
    if (!this.memoryLoaded) {
      const fromRedis = await this._loadFromRedis();
      if (fromRedis && Object.keys(fromRedis).length > 0) {
        this.memory = fromRedis;
        this.memoryLoaded = true;
      } else {
        await this._loadFromDb();
      }
    }
    return this._snapshot();
  }

  /**
   * Get one config group (e.g. 'payments') or a dotted path (e.g. 'payments.stripe').
   */
  async get(path = '', fallback = undefined) {
    const full = await this.getAll();
    if (!path) return full;
    const parts = path.split('.');
    let cursor = full;
    for (const part of parts) {
      if (cursor && typeof cursor === 'object' && part in cursor) {
        cursor = cursor[part];
      } else {
        return fallback;
      }
    }
    return cursor === undefined ? fallback : cursor;
  }

  /**
   * Upsert a config group and refresh the caches.
   */
  async set(key, value) {
    const parsed = value && typeof value === 'object' ? value : {};
    await SystemConfig.upsert({ key, value: parsed });
    this.memory[key] = deepMerge(this.memory[key] || {}, parsed);
    this.memoryLoaded = true;
    await this._storeInRedis();
    return this._snapshot();
  }

  /**
   * Bulk save used by the Setup Wizard / Admin Settings panel.
   */
  async bulkSet(entries) {
    for (const [key, value] of Object.entries(entries || {})) {
      if (!key || typeof key !== 'string') continue;
      await this.set(key, value);
    }
    return this.getAll();
  }

  /**
   * True only when a buyer has completed onboarding (business name + support
   * email + currency present). DB offline → true (fail-open).
   */
  async isConfigured() {
    if (!this._dbAvailable()) return true;
    const cfg = await this.getAll();
    const hasBusiness = Boolean(cfg?.business?.name && cfg?.business?.supportEmail);
    const hasCurrency = Boolean(cfg?.currency?.code);
    return Boolean(cfg?.setup?.completed || (hasBusiness && hasCurrency));
  }

  /**
   * Masked public view — never exposes secrets. Returned by /api/settings/public
   * and merged into payment /config.
   */
  async getPublicConfig() {
    const cfg = await this.getAll();
    const stripe = cfg?.payments?.stripe || {};
    const paypal = cfg?.payments?.paypal || {};
    return {
      business: {
        name: cfg?.business?.name || '',
        tagline: cfg?.business?.tagline || '',
        logoUrl: cfg?.business?.logoUrl || '',
        supportEmail: cfg?.business?.supportEmail || '',
      },
      currency: cfg?.currency || defaults.currency,
      payments: {
        stripeEnabled: Boolean(stripe?.enabled && stripe?.publishableKey),
        stripePublishableKey: stripe?.publishableKey || '',
        paypalEnabled: Boolean(paypal?.enabled && paypal?.clientId),
      },
      setupCompleted: Boolean(cfg?.setup?.completed),
    };
  }

  /**
   * Redact a snapshot for admin-only display (drops private keys).
   */
  maskAdminConfig(cfg) {
    const copy = JSON.parse(JSON.stringify(cfg || {}));
    if (copy?.payments?.stripe?.secretKey)
      copy.payments.stripe.secretKey = copy.payments.stripe.secretKey ? '••••••••' : '';
    if (copy?.payments?.stripe?.webhookSecret) copy.payments.stripe.webhookSecret = '••••••••';
    if (copy?.payments?.paypal?.clientSecret)
      copy.payments.paypal.clientSecret = copy.payments.paypal.clientSecret ? '••••••••' : '';
    if (copy?.payments?.paypal?.webhookId)
      copy.payments.paypal.webhookId = copy.payments.paypal.webhookId ? '••••••••' : '';
    if (copy?.smtp?.pass) copy.smtp.pass = copy.smtp.pass ? '••••••••' : '';
    return copy;
  }
}

export default new SystemConfigService();
