import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { homedir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { createRunsApiPlugin } from "./scripts/runs-api.mjs";

export function configuredExternalMediaSources({ repoRoot, homeRoot }) {
  return [
    { id: "artifacts", label: "AI-VIDEO Artifacts", kind: "development_artifact", root: path.join(repoRoot, "artifacts") },
    { id: "ai-video-experiments", label: "AI-VIDEO Experiments", kind: "development_artifact", root: path.join(homeRoot, "ai-video-experiments") },
    { id: "comfyui-output", label: "ComfyUI Output", kind: "raw_provider_output", root: path.join(homeRoot, "ComfyUI", "output") },
    { id: "qingyan-project", label: "青颜项目目录", kind: "external_project_asset", root: path.join(homeRoot, "电商图片", "青颜") },
  ];
}

const providerConsoleRoot = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(providerConsoleRoot, "..");
const externalMediaSources = configuredExternalMediaSources({ repoRoot, homeRoot: homedir() });

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
  plugins: [react(), createRunsApiPlugin({ repoRoot, externalSources: externalMediaSources })],
});
