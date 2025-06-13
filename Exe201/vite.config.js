import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      "5c03-2402-800-63b6-8069-6cbd-8337-efdb-8bf5.ngrok-free.app",
      "0.0.0.0",
    ],
  },
});
