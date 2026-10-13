/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        primary: 'rgb(var(--t-primary-rgb, 5 150 105) / <alpha-value>)',
        accent: 'rgb(var(--t-accent-rgb, 99 102 241) / <alpha-value>)',
        heading: 'rgb(var(--t-heading-rgb, 5 46 38) / <alpha-value>)',
        canvas: 'rgb(var(--t-canvas-rgb, 242 250 246) / <alpha-value>)',
        surface: 'rgb(var(--t-surface-rgb, 255 255 255) / <alpha-value>)',
        text: 'rgb(var(--t-text-rgb, 31 41 55) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Space Grotesk', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
