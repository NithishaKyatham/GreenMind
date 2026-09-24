/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Moss/leaf green — the growing-crop identity. Deliberately not
        // Material Design's green (#2e7d32) or a generic "eco app" green.
        primary: {
          50: "#F2F8EE",
          100: "#E0EFD6",
          200: "#C1DFAF",
          300: "#99C97E",
          400: "#71AE55",
          500: "#4C8F39",
          600: "#3A7129",
          700: "#2C5920",
          800: "#234717",
          900: "#1B3812",
        },
        // Harvest gold/turmeric — the one bold accent, reserved for
        // primary actions and the confidence indicator. Grounded in
        // ripened-grain/turmeric color, not the generic AI-design
        // terracotta (#D97757).
        accent: {
          50: "#FBF3E4",
          100: "#F5E2BC",
          300: "#E7B565",
          500: "#C9862A",
          600: "#A96B1D",
          700: "#895315",
        },
        // Tilled-soil neutral — warm grey-brown for borders, secondary
        // text, and surfaces, instead of cool SaaS-default grey.
        earth: {
          50: "#FAF8F5",
          100: "#F1ECE4",
          200: "#E1D8CB",
          300: "#C7B8A3",
          500: "#8A7660",
          700: "#5A4C3D",
          900: "#332A20",
        },
        // Semantic (used sparingly, never as brand color)
        danger: {
          50: "#FBEEEA",
          500: "#B3432E",
          700: "#8A331F",
        },
        info: {
          50: "#EEF2F8",
          500: "#4A6FA5",
          700: "#385A87",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Noto Sans",
          "sans-serif",
        ],
      },
      borderRadius: {
        sm: "8px",
        md: "12px",
        lg: "18px",
      },
      boxShadow: {
        // Warm-tinted, low-opacity — not the generic rgba(0,0,0,.1) grey
        // shadow under every card.
        soft: "0 1px 2px rgba(43,34,20,0.06), 0 8px 24px rgba(43,34,20,0.06)",
      },
    },
  },
  plugins: [],
};
