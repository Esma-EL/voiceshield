import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        shield: {
          DEFAULT: "#0ea5e9",
          dark: "#0369a1",
        },
      },
      keyframes: {
        pulseRing: {
          "0%": { boxShadow: "0 0 0 0 rgba(239,68,68,0.45)" },
          "70%": { boxShadow: "0 0 0 14px rgba(239,68,68,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(239,68,68,0)" },
        },
        slideIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        pulseRing: "pulseRing 1.6s ease-out infinite",
        slideIn: "slideIn 0.25s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
