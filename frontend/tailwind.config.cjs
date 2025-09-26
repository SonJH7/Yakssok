/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ivory: '#F7F8F2',
        ink: '#2B2B2B',
        border: '#E5E7EB',
        positive: '#9FD6AF',
        warning: '#F3B39D',
        neutral: '#D4D4D8',
      },
    },
  },
  plugins: [],
};
