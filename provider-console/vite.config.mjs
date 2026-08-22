import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { createRunsApiPlugin } from "./scripts/runs-api.mjs";

const providerConsoleRoot = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(providerConsoleRoot, "..");

export default defineConfig({
  build: {
    outDir: "dist/client",
  },
  optimizeDeps: {
    include: ["react", "react-dom/client"],
  },
  server: {
    host: "127.0.0.1",
    allowedHosts: ["terminal.local"],
    warmup: {
      clientFiles: ["./src/main.jsx"],
    },
  },
  plugins: [react(), createRunsApiPlugin({ repoRoot })],
});
