/**
 * Fail-closed JWT secret resolution.
 *
 * Refuses to boot when JWT_SECRET is missing, shorter than MIN_LENGTH, or a
 * well-known placeholder, so a publicly known value can never be used to forge
 * tokens (including admin tokens).
 *
 * Generate a secret with:
 *   node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
 *   # or: openssl rand -hex 32
 */
const DENIED_SECRETS = [
  'secret',
  'changeme',
  'change_me',
  'change-me-in-production',
  'change_this_secret_in_production',
  'change_this_to_a_random_64_char_string',
  'lumi_jwt_secret',
  'replace-me',
  'replace_with_a_random_64_character_secret',
  'replace_with_secure_random_key',
  'secret_jwt_key',
  'secret_jwt_key_2026',
  'super_secret_production_key_2026',
  'your_jwt_secret_key_here',
  'your_super_secret_key_here_change_this',
  'your-super-secret-jwt-key-change-this',
  'your_super_secret_jwt_key_change_this_minimum_32_characters',
];

const MIN_LENGTH = 32;

function fail(reason) {
  console.error(`[fatal] JWT_SECRET ${reason}. Refusing to start.
Generate a strong secret with one of:
  node -e "console.log(require('crypto').randomBytes(48).toString('hex'))"
  # or: openssl rand -hex 32
Then set JWT_SECRET in your .env file.`);
  process.exit(1);
}

function resolveJwtSecret(env) {
  const source = env || process.env;
  const raw = source.JWT_SECRET;
  if (typeof raw !== 'string' || raw.trim() === '') fail('is not set');
  const secret = raw.trim();
  if (secret.length < MIN_LENGTH) {
    fail(`must be at least ${MIN_LENGTH} characters (got ${secret.length})`);
  }
  if (DENIED_SECRETS.indexOf(secret.toLowerCase()) !== -1) {
    fail('is a well-known placeholder value');
  }
  return secret;
}

const jwtSecret = Object.freeze(resolveJwtSecret(process.env));

module.exports = { jwtSecret, MIN_LENGTH };
