/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        logo: ["Montserrat", "sans-serif"],
        display: ["Cormorant Garamond", "serif"],
        "barlow-condensed": ["var(--font-barlow-condensed)", "sans-serif"],
      },
      colors: {
        gray: {
          50: "#FAFAFA",
          100: "#F5F5F5",
          200: "#E5E5E5",
          300: "#D4D4D4",
          400: "#A3A3A3",
          500: "#737373",
          600: "#525252",
          700: "#404040",
          800: "#262626",
          900: "#171717",
        },
        "vitruvyan-accent": {
          DEFAULT: "#333333",
          dark: "#1a1a1a",
        },
        // 🎨 Vitruvyan Design System - Semitransparent Palette
        vitruvyan: {
          // Success/Positive (Green with alpha)
          success: {
            bg: "rgba(34, 197, 94, 0.08)",      // green-500 @ 8%
            border: "rgba(34, 197, 94, 0.20)",  // green-500 @ 20%
            text: "rgba(22, 163, 74, 1)",       // green-600
            hover: "rgba(34, 197, 94, 0.12)",   // green-500 @ 12%
          },
          // Warning/Neutral (Yellow/Amber with alpha)
          warning: {
            bg: "rgba(245, 158, 11, 0.08)",     // amber-500 @ 8%
            border: "rgba(245, 158, 11, 0.20)", // amber-500 @ 20%
            text: "rgba(217, 119, 6, 1)",       // amber-600
            hover: "rgba(245, 158, 11, 0.12)",  // amber-500 @ 12%
          },
          // Danger/Negative (Red with alpha)
          danger: {
            bg: "rgba(239, 68, 68, 0.08)",      // red-500 @ 8%
            border: "rgba(239, 68, 68, 0.20)",  // red-500 @ 20%
            text: "rgba(220, 38, 38, 1)",       // red-600
            hover: "rgba(239, 68, 68, 0.12)",   // red-500 @ 12%
          },
          // Info/Neutral (Blue with alpha)
          info: {
            bg: "rgba(59, 130, 246, 0.08)",     // blue-500 @ 8%
            border: "rgba(59, 130, 246, 0.20)", // blue-500 @ 20%
            text: "rgba(37, 99, 235, 1)",       // blue-600
            hover: "rgba(59, 130, 246, 0.12)",  // blue-500 @ 12%
          },
          // Premium/Featured (Purple with alpha)
          premium: {
            bg: "rgba(168, 85, 247, 0.08)",     // purple-500 @ 8%
            border: "rgba(168, 85, 247, 0.20)", // purple-500 @ 20%
            text: "rgba(147, 51, 234, 1)",      // purple-600
            hover: "rgba(168, 85, 247, 0.12)",  // purple-500 @ 12%
          },
          // Neutral (Gray with alpha) - for cards
          neutral: {
            bg: "rgba(115, 115, 115, 0.05)",    // gray-500 @ 5%
            border: "rgba(115, 115, 115, 0.15)", // gray-500 @ 15%
            text: "rgba(82, 82, 82, 1)",        // gray-600
            hover: "rgba(115, 115, 115, 0.08)",  // gray-500 @ 8%
          },
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
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      keyframes: {
        "scroll-left": {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "scroll-right": {
          "0%": { transform: "translateX(-50%)" },
          "100%": { transform: "translateX(0)" },
        },
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "slideDown": {
          "0%": { 
            transform: "translateY(-30px)", 
            opacity: "0" 
          },
          "100%": { 
            transform: "translateY(0)", 
            opacity: "1" 
          }
        },
      },
      animation: {
        "scroll-left": "scroll-left 30s linear infinite",
        "scroll-right": "scroll-right 30s linear infinite",
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "slideDown": "slideDown 0.5s ease-out",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
