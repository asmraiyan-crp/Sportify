/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      // ── Colour Palette ──────────────────────────────────────────────────
      colors: {
        base:    "#0b0b0f",
        card:    "#111118",
        card2:   "#16161f",
        hover:   "#1e1e2a",
        border:  "#1f1f2e",
        border2: "#2a2a3d",
        accent: {
          DEFAULT: "#7c3aed",
          light:   "#9d5ff0",
          glow:    "rgba(124,58,237,0.33)",
        },
        live:    "#ef4444",
        soon:    "#eab308",
        win:     "#22c55e",
        t1:      "#f0f0ff",
        t2:      "#9595b0",
        t3:      "#5a5a75",
      },

      // ── Typography ───────────────────────────────────────────────────────
      fontFamily: {
        display: ['"Bebas Neue"', "sans-serif"],
        heading:  ["Rajdhani", "sans-serif"],
        body:     ["Inter", "sans-serif"],
      },
      fontSize: {
        "2xs": ["10px", "14px"],
        "3xl-display": ["52px", "1"],
        "4xl-display": ["72px", "1"],
      },

      // ── Spacing / Sizing ─────────────────────────────────────────────────
      borderRadius: {
        card: "14px",
        btn:  "8px",
      },

      // ── Box Shadows ───────────────────────────────────────────────────────
      boxShadow: {
        "card-hover": "0 8px 32px rgba(0,0,0,0.45)",
        "accent-glow": "0 6px 24px rgba(124,58,237,0.35)",
        "accent-glow-lg": "0 10px 30px rgba(124,58,237,0.25)",
      },

      // ── Background Images / Gradients ─────────────────────────────────────
      backgroundImage: {
        "logo-gradient":  "linear-gradient(90deg,#7c3aed,#c084fc)",
        "accent-bar":     "linear-gradient(180deg,#7c3aed,#9d5ff0)",
        "card-glow":      "linear-gradient(135deg,rgba(124,58,237,0.33) 0%,transparent 60%)",
        "top-glow":       "linear-gradient(90deg,transparent,#7c3aed,#9d5ff0,transparent)",
        "hero-overlay":   "linear-gradient(90deg,rgba(0,0,0,0.85) 0%,rgba(0,0,0,0.4) 60%,transparent 100%)",
        "hero-football":  "linear-gradient(135deg,#1a0a2e 0%,#2d1060 50%,#0f0a1e 100%)",
        "hero-cricket":   "linear-gradient(135deg,#0e1a0a 0%,#1e4d1a 50%,#0a150a 100%)",
        "hero-ucl":       "linear-gradient(135deg,#0a1628 0%,#1e3a5f 50%,#0a0f1e 100%)",
        "hero-wwe":       "linear-gradient(135deg,#1e0a0a 0%,#4d1010 50%,#150505 100%)",
        "player-avatar":  "linear-gradient(135deg,#7c3aed,#1e1030)",
      },

      // ── Animations ────────────────────────────────────────────────────────
      keyframes: {
        pulse2: {
          "0%,100%": { opacity: "1", transform: "scale(1)" },
          "50%":     { opacity: "0.5", transform: "scale(0.8)" },
        },
        modalIn: {
          from: { opacity: "0", transform: "scale(0.96) translateY(10px)" },
          to:   { opacity: "1", transform: "scale(1) translateY(0)" },
        },
        slideHero: {
          from: { opacity: "0", transform: "translateY(12px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "pulse2":   "pulse2 1.2s ease-in-out infinite",
        "modal-in": "modalIn 0.22s cubic-bezier(0.4,0,0.2,1) forwards",
        "slide-up": "slideHero 0.4s ease forwards",
      },
    },
  },
  plugins: [],
};
