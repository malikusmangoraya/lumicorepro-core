import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores([
    'dist',
    'coverage',
    '.history',
    'ai-agent',
    'backend',
    'backend-library',
    'database',
    'generated-projects',
    'registry',
    'scripts',
    'src/templates',
    'templates',
    'docs',
    'k8s',
    'nginx',
    'public',
    // Packaged buyer deliveries: 69 full project trees (8.2k files). Linting them
    // inflated `eslint .` from ~215 real source files to 8.4k and made the lint
    // step hang past 15 minutes. They are release artefacts, not source.
    'delivery',
    'delivery-new',
    'archive',
    'vendors',
    'test-results',
    'playwright-report',
    'add-kimi-openmuse-lumicor-model',
    'ecommerce-website-generator-engine',
    'full-project-upgrade-and-perfection',
    'free-tier-api-implementation',
    'critical-bundle-optimization-and-cleanup',
    'lumicorepro-core-integration-query',
    'new rebuilt',
    // Local data / env dirs that are not code.
    'pgdata',
    'venv',
    'logs',
    '.cursor',
    '.kiro',
    '.opencode',
    '.qodo',
    '.xgrok',
  ]),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: { ...globals.browser, ...globals.jest, ...globals.node },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      'no-unused-vars': 'off',
      'no-undef': 'off',
      'no-useless-escape': 'off',
      'react-refresh/only-export-components': 'off',
      'react-hooks/static-components': 'off',
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/exhaustive-deps': 'off',
      'react-hooks/purity': 'off',
      'react-hooks/immutability': 'off',
    },
  },
])
