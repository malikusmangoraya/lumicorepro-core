/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'rgb(var(--t-primary-rgb, 124 58 237) / <alpha-value>)',
        accent: 'rgb(var(--t-accent-rgb, 236 72 153) / <alpha-value>)',
        heading: 'rgb(var(--t-heading-rgb, 46 16 101) / <alpha-value>)',
        canvas: 'rgb(var(--t-canvas-rgb, 248 250 252) / <alpha-value>)',
        surface: 'rgb(var(--t-surface-rgb, 255 255 255) / <alpha-value>)',
        text: 'rgb(var(--t-text-rgb, 30 41 59) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Roboto', 'sans-serif'],
        display: ['Poppins', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
