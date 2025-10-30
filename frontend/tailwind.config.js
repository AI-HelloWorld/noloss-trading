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
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        dark: {
          50: '#18181b',
          100: '#27272a',
          200: '#3f3f46',
          300: '#52525b',
          400: '#71717a',
          500: '#a1a1aa',
          600: '#d4d4d8',
          700: '#e4e4e7',
          800: '#f4f4f5',
          900: '#fafafa',
        },
        primary: '#fbbf24',    // Gold
        secondary: '#0a0a0a',  // Deep Black
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

