/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'bg-base': '#0d0d14',
        'bg-surface': '#13131f',
        'bg-elevated': '#1a1a2e',
        border: '#1e1e30',
        'border-active': '#2d2d4a',
        'text-primary': '#e8e8f0',
        'text-secondary': '#6b6b8a',
        'text-muted': '#3d3d5c',
        accent: '#6366f1',
        'accent-hover': '#4f52d4',
        green: '#10b981',
        red: '#ef4444',
        orange: '#f59e0b',
        blue: '#3b82f6',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-subtle': 'pulseSubtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.6' },
        }
      },
      boxShadow: {
        none: 'none',
      }
    }
  },
  plugins: [],
}
