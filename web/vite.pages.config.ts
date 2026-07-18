import react from "@vitejs/plugin-react";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const webRoot = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  base: process.env.PAGES_BASE_PATH || "/",
  root: resolve(webRoot, "static-app"),
  publicDir: resolve(webRoot, "public"),
  plugins: [react()],
  build: {
    emptyOutDir: true,
    outDir: resolve(webRoot, "dist-pages"),
  },
});
