import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" keeps the build relocatable (works from any subpath or file://)
export default defineConfig({
  base: "./",
  plugins: [react()],
});
