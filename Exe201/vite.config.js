import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: [
      "1e46-2402-800-63b6-ad05-44bf-b158-fd18-342d.ngrok-free.app",
      "0.0.0.0",
    ],
  },
});
