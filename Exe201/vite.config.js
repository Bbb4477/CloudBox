import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ["0.0.0.0"],
  },
  define: {
    // Đảm bảo các biến môi trường có thể được truy cập trong mã nguồn
    VITE_API_BASE_URL: JSON.stringify(process.env.VITE_API_BASE_URL),
    VITE_API_KEY: JSON.stringify(process.env.VITE_API_KEY),
    VITE_API_LOG: JSON.stringify(process.env.VITE_API_LOG),
    VITE_API_LOG_END: JSON.stringify(process.env.VITE_API_LOG_END),
  },
});
