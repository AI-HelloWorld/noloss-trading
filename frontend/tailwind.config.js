/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Black & Gold Theme - Professional Trading Platform
        gold: {
          50: '#fffef5',
          100: '#fffde8',
          200: '#fef9c3',
          300: '#fdf088',
          400: '#fcd535',  // Binance primary gold
          500: '#f0b90b',  // Binance secondary gold
          600: '#d4a017',
          700: '#b8870f',
          800: '#9a720c',
          900: '#7d5d09',
        },
        dark: {
          50: '#1e2329',  // Binance dark background
          100: '#2b3139', // Binance card background
          200: '#474d57',
          300: '#5e6673',
          400: '#848e9c',
          500: '#a1aab8',
          600: '#b7bdc8',
          700: '#eaecef', // Binance text
          800: '#f0f1f2',
          900: '#ffffff',
        },
        primary: '#fcd535',    // Binance Gold
        secondary: '#1e2329',  // Binance Dark
        success: '#10b981',    // Green
        danger: '#ef4444',     // Red
        warning: '#f59e0b',    // Amber
        background: {
          primary: '#0a0a0a',   // Main background
          secondary: '#18181b', // Card background
          tertiary: '#27272a',  // Hover background
        }
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'display': ['Orbitron', 'sans-serif'],
        'mono': ['Monaco', 'Courier New', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-gold': 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
        'gradient-dark': 'linear-gradient(135deg, #0a0a0a 0%, #18181b 100%)',
      }
    },
  },
  plugins: [],
}

