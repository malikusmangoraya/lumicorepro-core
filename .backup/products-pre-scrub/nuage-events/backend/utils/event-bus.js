/**
 * Event Bus — Internal EventEmitter for the application
 * Auto-generated for internal event handling
 *
 * Usage:
 *   import { eventBus } from './event-bus.js';
 *   eventBus.emit('order.created', { orderId: '...' });
 *   eventBus.on('order.created', async (data) => { ... });
 */

import { EventEmitter } from 'events';
import logger from './logger.js';

class LumicoreEventBus extends EventEmitter {
  constructor() {
    super();
    this.setMaxListeners(50); // Increase for many subscribers
    this._stats = {};
  }

  emit(event, ...args) {
    this._stats[event] = (this._stats[event] || 0) + 1;
    logger.debug(`[EventBus] ${event} (total: ${this._stats[event]})`);
    return super.emit(event, ...args);
  }

  on(event, listener) {
    logger.debug(`[EventBus] Registered listener: ${event}`);
    return super.on(event, async (...args) => {
      try {
        await listener(...args);
      } catch (err) {
        logger.error(`[EventBus] Error in listener for ${event}: ${err.message}`);
      }
    });
  }

  getStats() {
    return { ...this._stats };
  }
}

export const eventBus = new LumicoreEventBus();

// ── Register default handlers ────────────────────────────────────────────
// Uncomment and implement the handlers you need:
// eventBus.on('subscription.created', async (data) => { /* handle */ });
// eventBus.on('subscription.upgraded', async (data) => { /* handle */ });
// eventBus.on('subscription.downgraded', async (data) => { /* handle */ });
// eventBus.on('subscription.cancelled', async (data) => { /* handle */ });
// eventBus.on('invoice.paid', async (data) => { /* handle */ });
// eventBus.on('invoice.failed', async (data) => { /* handle */ });

export default eventBus;
