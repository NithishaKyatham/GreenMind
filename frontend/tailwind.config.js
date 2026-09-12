/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f0f9f0",
          100: "#dcf0dc",
          500: "#2e7d32",
          600: "#256628",
          700: "#1b4f1f",
        },
        earth: {
          100: "#f5f0e6",
          500: "#8d6e46",
        },
      },
    },
  },
  plugins: [],
};
