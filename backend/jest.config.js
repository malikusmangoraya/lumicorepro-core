export default {
  testEnvironment: 'node',
  transform: {},
  testMatch: ['**/__tests__/**/*.test.js', '**/tests/**/*.test.js'],
  verbose: true,
  forceExit: true,
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,
  collectCoverageFrom: [
    'services/**/*.js',
    'utils/**/*.js',
    'middleware/**/*.js',
    'config/**/*.js',
    // Routes and models were excluded from the denominator, which made the
    // reported percentage describe a subset of the backend rather than the
    // backend. They are measured now.
    'routes/**/*.js',
    'models/**/*.js',
    'workers/**/*.js',
    '!**/node_modules/**',
    '!**/coverage/**',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['json', 'lcov', 'text-summary'],
  // Ratchet gate: floors sit ~1 point under the 2026-10-24 measurement
  // (74.79% stmts, 67.11% branches, 69.29% funcs, 75.48% lines; 1903 tests / 82
  // suites). CI fails below this, so coverage can only go UP. Raise the floor
  // whenever a PR adds coverage; target is 80% per AGENTS.md §6.
  coverageThreshold: {
    global: {
      statements: 73,
      branches: 66,
      functions: 68,
      lines: 74,
    },
  },
};