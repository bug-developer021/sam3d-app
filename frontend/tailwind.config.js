/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
    "./lib/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#09090b", // zinc-950
        panel: "#18181b", // zinc-900
        edge: "#27272a", // zinc-800
        surface: "#27272a", // zinc-800
        accent: "#8b5cf6", // violet-500
        highlight: "#d8b4fe", // violet-300
        secondary: "#71717a", // zinc-500
      },
      boxShadow: {
        brand: "0 0 50px -12px rgba(139, 92, 246, 0.25)",
        panel: "0 8px 30px -4px rgba(0, 0, 0, 0.5)",
        glow: "0 0 20px rgba(139, 92, 246, 0.5)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "hero-glow": "conic-gradient(from 180deg at 50% 50%, #2a2a2a 0deg, #1a1a1a 180deg, #2a2a2a 360deg)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
    },
  },
  plugins: [],
};
