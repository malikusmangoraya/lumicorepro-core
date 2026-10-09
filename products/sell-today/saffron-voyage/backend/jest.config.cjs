module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/__tests__/**/*.test.js'],
  collectCoverageFrom: ['routes/**/*.js', 'controllers/**/*.js', 'services/**/*.js'],
  coverageProvider: 'v8',
  verbose: true,
  testTimeout: 20000,
};
