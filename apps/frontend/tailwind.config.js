/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101828",
        graphite: "#344054",
        mist: "#f4f7fb",
        line: "#d0d5dd",
        cobalt: "#2454ff",
        teal: "#0f9f8f",
        amber: "#b36b00"
      }
    }
  },
  plugins: []
};