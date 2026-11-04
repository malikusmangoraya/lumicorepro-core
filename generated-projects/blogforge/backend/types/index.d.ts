// Shared domain types for the backend (JS codebase typed via checkJs).
/** @typedef {Object} User
 * @property {string} id UUID primary key
 * @property {string} name non-empty
 * @property {string} email unique, validated
 * @property {string} password bcrypt hash
 * @property {'user'|'admin'} role
 * @property {Date} [createdAt]
 * @property {Date} [updatedAt]
 */
export {};

/** @typedef {Object} Record
 * @property {string} id UUID primary key
 * @property {string} title
 * @property {string} [body] markdown/plain text payload
 * @property {'draft'|'published'|'archived'} status
 * @property {string} userId FK -> users.id
 * @property {Date} [createdAt]
 * @property {Date} [updatedAt]
 */
