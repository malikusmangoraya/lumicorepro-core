import js from '@eslint/js';
import globals from 'globals';

/**
 * Backend lint config. This file did not exist before: the root config lists
 * `backend` in globalIgnores, so `npm run lint` in backend/ reported success
 * while checking zero files. Keep this config so backend findings are real.
 */
export default [
  {
    ignores: [
      'node_modules/**',
      'coverage/**',
      'uploads/**',
      'generated-projects/**',
      'scripts/**',
      'legacy/**',
    ],
  },
  js.configs.recommended,
  {
    files: ['**/*.js'],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        ...globals.node,
        ...globals.es2024,
        jest: 'readonly',
        describe: 'readonly',
        it: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        beforeAll: 'readonly',
        afterAll: 'readonly',
      },
    },
    rules: {
      'no-unused-vars': [
        'warn',
        { args: 'after-used', argsIgnorePattern: '^_', caughtErrors: 'none' },
      ],
      'no-empty': ['warn', { allowEmptyCatch: true }],
      'no-console': 'off',
      'no-control-regex': 'off',
    },
  },
];
