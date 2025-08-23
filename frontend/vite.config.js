import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// If deploying to GitHub Pages under a repo (e.g. username.github.io/repo),
// set BASE_PATH env before build or rely on CI injecting process.env.GHP_BASE
const base = process.env.GHP_BASE || process.env.BASE_PATH || '/';

export default defineConfig({
  base,
  plugins: [react()],
  server: { port: 5173 }
});