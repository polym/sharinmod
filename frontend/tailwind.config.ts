import type { Config } from 'tailwindcss'

const config: Config = {
  // Dark mode disabled in CSS, kept for future class-based dark mode support
  darkMode: ["class"],
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        heading: ['Fredoka', 'sans-serif'],
        body: ['Nunito', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      colors: {
        /* Claymorphism Vibrant Colors */
        clay: {
          primary: '#4F46E5',
          secondary: '#818CF8',
          accent: '#F97316',
          background: '#EEF2FF',
          text: '#1E1B4B',
          'border-light': '#E0E7FF',
          'border-dark': '#4338CA',
        },
        /* Original brand colors kept for compatibility */
        brand: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          800: '#3730A3',
          900: '#312E81',
        },
        switch: {
          on: '#AEF0C2',
          off: '#F8F9FC',
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xl: "1.25rem",
        '2xl': "1.5rem",
      },
      boxShadow: {
        'clay': '8px 8px 16px rgba(79, 70, 229, 0.1), -4px -4px 12px rgba(255, 255, 255, 0.9), inset 2px 2px 4px rgba(79, 70, 229, 0.05)',
        'clay-hover': '12px 12px 20px rgba(79, 70, 229, 0.15), -6px -6px 16px rgba(255, 255, 255, 0.95), inset 2px 2px 4px rgba(79, 70, 229, 0.05)',
        'clay-button': '6px 6px 12px rgba(79, 70, 229, 0.3), inset -2px -2px 6px rgba(0, 0, 0, 0.1), inset 2px 2px 6px rgba(255, 255, 255, 0.2)',
        'clay-button-active': '2px 2px 6px rgba(79, 70, 229, 0.4), inset 2px 2px 6px rgba(0, 0, 0, 0.15)',
        'clay-inset': 'inset 4px 4px 8px rgba(79, 70, 229, 0.08), inset -2px -2px 6px rgba(255, 255, 255, 0.9)',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
export default config
