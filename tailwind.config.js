/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1e88e5',
        secondary: '#6c757d',
        success: '#4caf50',
        danger: '#f44336',
        warning: '#ff9800',
        info: '#03a9f4',
        light: '#f8f9fa',
        dark: '#343a40',
      },
    },
  },
  plugins: [],
}
