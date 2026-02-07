/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void: '#08070D',
        surface: '#0F0E17',
        card: '#161525',
        'card-hover': '#1C1A30',
        elevated: '#211F38',
        gold: '#F0C246',
        'gold-dim': '#C49A1A',
        neon: '#00E5A0',
        'neon-dim': '#00B87A',
        accent: {
          red: '#E83F5B',
          blue: '#4E7CFF',
        },
        'text-primary': '#F2F0FF',
        'text-secondary': '#9B97B8',
        'text-muted': '#5E5A7E',
        roulette: {
          red: '#C0392B',
          black: '#1A1A2E',
          green: '#27AE60',
        },
      },
      fontFamily: {
        display: ["'Playfair Display'", "Georgia", "serif"],
        body: ["'DM Sans'", "'Segoe UI'", "sans-serif"],
        mono: ["'JetBrains Mono'", "'Fira Code'", "monospace"],
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'fade-in': 'fadeIn 0.5s ease',
        'slide-in': 'slideIn 0.3s ease',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
}
