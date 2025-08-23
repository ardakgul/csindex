/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        inter: ['Inter', 'ui-sans-serif', 'system-ui']
      },
      colors: {
        brand: {
          DEFAULT: '#6B8AFF',
          accent: '#4C6EDB'
        }
      }
    },
  },
  plugins: [],
};