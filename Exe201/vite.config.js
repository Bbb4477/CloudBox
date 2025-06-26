import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      "dd32-2402-800-63b6-ad05-a842-942a-1ed1-bb4e.ngrok-free.app",
      "0.0.0.0",
    ],
  },
});
