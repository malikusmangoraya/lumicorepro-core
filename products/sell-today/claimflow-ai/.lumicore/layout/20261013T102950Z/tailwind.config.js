/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        primary: 'rgb(var(--t-primary-rgb, 55 65 81) / <alpha-value>)',
        accent: 'rgb(var(--t-accent-rgb, 220 38 38) / <alpha-value>)',
        heading: 'rgb(var(--t-heading-rgb, 17 24 39) / <alpha-value>)',
        canvas: 'rgb(var(--t-canvas-rgb, 248 250 252) / <alpha-value>)',
        surface: 'rgb(var(--t-surface-rgb, 255 255 255) / <alpha-value>)',
        text: 'rgb(var(--t-text-rgb, 38 41 47) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Helvetica Neue', 'sans-serif'],
        display: ['Helvetica Neue', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
