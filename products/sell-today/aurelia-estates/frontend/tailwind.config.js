/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        primary: 'rgb(var(--t-primary-rgb, 37 99 235) / <alpha-value>)',
        accent: 'rgb(var(--t-accent-rgb, 124 58 237) / <alpha-value>)',
        heading: 'rgb(var(--t-heading-rgb, 15 23 42) / <alpha-value>)',
        canvas: 'rgb(var(--t-canvas-rgb, 255 255 255) / <alpha-value>)',
        surface: 'rgb(var(--t-surface-rgb, 248 250 252) / <alpha-value>)',
        text: 'rgb(var(--t-text-rgb, 31 41 55) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Geist', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
