/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
          950: '#022c22',
        },
        accent: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
        },
        base: {
          a: '#34d399',
          c: '#60a5fa',
          g: '#fbbf24',
          t: '#f87171',
          u: '#f472b6',
          n: '#94a3b8',
        },
      },
      fontFamily: {
        sans: ['Inter var', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      borderRadius: { xl: '0.875rem', '2xl': '1.125rem', '3xl': '1.5rem' },
      boxShadow: {
        soft: '0 1px 2px 0 rgb(2 6 23 / 0.4)',
        card: '0 1px 3px rgb(2 6 23 / 0.5), 0 8px 24px -12px rgb(2 6 23 / 0.6)',
        glow: '0 0 0 1px rgb(16 185 129 / 0.2), 0 12px 32px -8px rgb(16 185 129 / 0.35)',
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #059669 0%, #10b981 55%, #34d399 100%)',
        'mesh-dark':
          'radial-gradient(at 0% 0%, rgb(16 185 129 / 0.14) 0px, transparent 55%), radial-gradient(at 100% 0%, rgb(139 92 246 / 0.12) 0px, transparent 50%), radial-gradient(at 80% 100%, rgb(52 211 153 / 0.1) 0px, transparent 45%)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-8px)' } },
        helix: { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } },
      },
      animation: {
        'fade-up': 'fade-up 0.5s cubic-bezier(0.22, 1, 0.36, 1) both',
        float: 'float 5s ease-in-out infinite',
        'helix-slow': 'helix 24s linear infinite',
      },
    },
  },
  plugins: [],
};
