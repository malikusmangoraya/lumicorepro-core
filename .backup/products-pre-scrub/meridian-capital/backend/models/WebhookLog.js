/**
 * WebhookLog — Mongoose Model for webhook delivery audit trail
 */

import mongoose from 'mongoose';

const webhookLogSchema = new mongoose.Schema({
  source: { type: String, required: true, index: true },
  event: { type: String, required: true, index: true },
  payload: { type: String },
  status: {
    type: String,
    enum: ['received', 'emitted', 'delivered', 'failed', 'dead_letter'],
    default: 'received',
  },
  attempts: { type: Number, default: 0 },
  error: { type: String },
  createdAt: { type: Date, default: Date.now, index: true, expires: 2592000 }, // TTL 30 days
});

webhookLogSchema.index({ source: 1, event: 1, createdAt: -1 });

export default mongoose.model('WebhookLog', webhookLogSchema);
