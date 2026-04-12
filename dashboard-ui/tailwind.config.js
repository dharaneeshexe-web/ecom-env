const { fontFamily } = require('tailwindcss/defaultTheme');

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './app/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', ...fontFamily.sans],
      },
      colors: {
        primary: '#6366f1',
        secondary: '#a78bfa',
        accent: '#f472b6',
      },
      boxShadow: {
        glow: '0 0 10px rgba(99, 102, 241, 0.8)',
      },
    },
  },
  plugins: [],
};