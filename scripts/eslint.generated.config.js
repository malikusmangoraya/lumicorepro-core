import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['**/node_modules/**', '**/dist/**', '**/build/**']),
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
      // Local component injection rigidity: generated code must use the
      // pre-built ButtonMotion wrapper, never raw semantic <button> markup.
      'no-restricted-syntax': [
        'error',
        {
          selector: "JSXOpeningElement[name.name='button']",
          message:
            'Raw <button> violates local component injection. Import ButtonMotion from @/components/ui/ButtonMotion instead.',
        },
      ],
    },
  },
  {
    // Library-owned primitives legitimately render a native <button>.
    files: [
      '**/src/components/ui/**',
      '**/src/components/motion/**',
      '**/src/components/forms/**',
      '**/src/components/icons/**',
      '**/src/components/common/**',
      '**/src/components/navigation/**',
      '**/src/components/layout/**',
      '**/src/components/ecommerce/**',
      '**/src/components/**',
      '**/src/components/Navbar.jsx',
      '**/src/components/Footer.jsx',
      '**/src/components/UniqueLogo.jsx',
    ],
    rules: { 'no-restricted-syntax': 'off' },
  },
])