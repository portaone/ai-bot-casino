export const tokens = {
  bg: {
    void: "#08070D",
    surface: "#0F0E17",
    card: "#161525",
    cardHover: "#1C1A30",
    elevated: "#211F38",
  },
  accent: {
    gold: "#F0C246",
    goldDim: "#C49A1A",
    neon: "#00E5A0",
    neonDim: "#00B87A",
    red: "#E83F5B",
    redGlow: "rgba(232,63,91,0.3)",
    blue: "#4E7CFF",
  },
  text: {
    primary: "#F2F0FF",
    secondary: "#9B97B8",
    muted: "#5E5A7E",
    inverse: "#08070D",
  },
  roulette: {
    red: "#C0392B",
    black: "#1A1A2E",
    green: "#27AE60",
  },
};

export const font = {
  display: "'Playfair Display', Georgia, serif",
  mono: "'JetBrains Mono', 'Fira Code', monospace",
  body: "'DM Sans', 'Segoe UI', sans-serif",
};

export const WHEEL_NUMBERS = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26];
export const RED_NUMBERS = new Set([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]);

export function getColor(n: number): string {
  if (n === 0) return tokens.roulette.green;
  return RED_NUMBERS.has(n) ? tokens.roulette.red : tokens.roulette.black;
}
