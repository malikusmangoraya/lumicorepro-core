/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'rgb(var(--t-primary-rgb, 8 145 178) / <alpha-value>)',
        accent: 'rgb(var(--t-accent-rgb, 124 77 255) / <alpha-value>)',
        heading: 'rgb(var(--t-heading-rgb, 11 27 51) / <alpha-value>)',
        canvas: 'rgb(var(--t-canvas-rgb, 244 248 255) / <alpha-value>)',
        surface: 'rgb(var(--t-surface-rgb, 255 255 255) / <alpha-value>)',
        text: 'rgb(var(--t-text-rgb, 31 41 55) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Orbitron', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
