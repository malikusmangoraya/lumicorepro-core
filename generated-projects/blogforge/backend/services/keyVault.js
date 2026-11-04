/** keyVault — encrypted API-key manager for AI providers.
 * Keys live in the DB (or file) as AES-256-GCM ciphertext; ENCRYPTION_KEY is a
 * 32-byte hex secret from .env — never a key itself. get()/set() are the only
 * surface; raw plaintext never crosses a log or response.
 */
const crypto = require('crypto');

const ALGO = 'aes-256-gcm';

function _key() {
  const hex = process.env.ENCRYPTION_KEY;
  if (!hex || hex.length !== 64) {
    throw new Error('ENCRYPTION_KEY must be a 64-char hex string (32 bytes)');
  }
  return Buffer.from(hex, 'hex');
}

const _store = new Map(); // name -> {iv, tag, data} hex — swap for a DB table in prod

function setKey(name, plaintext) {
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv(ALGO, _key(), iv);
  const data = Buffer.concat([cipher.update(String(plaintext), 'utf8'), cipher.final()]);
  _store.set(name, { iv: iv.toString('hex'), tag: cipher.getAuthTag().toString('hex'), data: data.toString('hex') });
  return name;
}

function getKey(name) {
  const rec = _store.get(name);
  if (!rec) return process.env[name] || null; // .env fallback
  try {
    const decipher = crypto.createDecipheriv(ALGO, _key(), Buffer.from(rec.iv, 'hex'));
    decipher.setAuthTag(Buffer.from(rec.tag, 'hex'));
    return Buffer.concat([decipher.update(Buffer.from(rec.data, 'hex')), decipher.final()]).toString('utf8');
  } catch (_e) {
    return null; // wrong key / tampered — never throw raw crypto errors outward
  }
}

function hasKey(name) {
  return _store.has(name) || Boolean(process.env[name]);
}

module.exports = { setKey, getKey, hasKey };
