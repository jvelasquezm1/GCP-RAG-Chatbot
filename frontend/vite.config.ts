import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [tailwindcss(), react()],
    server: {
      port: 5173,
      host: true,
    },
    build: {
      outDir: "dist",
      sourcemap: true,
    },
    // Define global constants to replace in the code
    define: {
      __API_URL__: JSON.stringify(env.VITE_API_URL || "http://127.0.0.1:8000/"),
    },
  };
});
