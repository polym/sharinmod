import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ["class"],
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'SpotifyMixUI', 'CircularSp-Arab', 'CircularSp-Hebr', 'CircularSp-Cyrl',
          'CircularSp-Grek', 'CircularSp-Deva', 'Helvetica Neue', 'helvetica',
          'arial', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Meiryo',
          'MS Gothic', 'sans-serif',
        ],
        title: [
          'SpotifyMixUITitle', 'SpotifyMixUI', 'Helvetica Neue', 'helvetica',
          'arial', 'sans-serif',
        ],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic':
          'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      colors: {
        /* Spotify Dark Palette */
        spotify: {
          green: '#1ed760',
          'green-border': '#1db954',
          black: '#121212',
          'surface': '#181818',
          'interactive': '#1f1f1f',
          'elevated': '#252525',
          'elevated-alt': '#272727',
          white: '#ffffff',
          silver: '#b3b3b3',
          'near-white': '#cbcbcb',
          'border': '#4d4d4d',
          'light-border': '#7c7c7c',
          negative: '#f3727f',
          warning: '#ffa42b',
          announcement: '#539df5',
        },
        switch: {
          on: '#1ed760',
          off: '#535353',
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
        lg: "8px",
        md: "6px",
        sm: "4px",
        xl: "10px",
        '2xl': "20px",
        pill: "500px",
        full: "9999px",
      },
      boxShadow: {
        'spotify-heavy': 'rgba(0,0,0,0.5) 0px 8px 24px',
        'spotify-medium': 'rgba(0,0,0,0.3) 0px 8px 8px',
        'spotify-inset': 'rgb(18,18,18) 0px 1px 0px, rgb(124,124,124) 0px 0px 0px 1px inset',
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
export default config
