/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#8b5cf6",
          accent: "#c084fc",
          surface: "#1e1b4b",
          background: "#0f0e17",
        },
      },
    },
  },
  plugins: [],
};
