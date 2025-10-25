/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ruth-blue': '#0066cc',
        'ruth-navy': '#1e3a8a',
        'ruth-gray': '#64748b',
      }
    },
  },
  plugins: [],
}
