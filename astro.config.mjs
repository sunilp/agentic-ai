// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://agenticlab.sunilprakash.com',
  base: '/',
  trailingSlash: 'always',
  build: {
    format: 'directory',
  },
  markdown: {
    shikiConfig: {
      // Light theme to match editorial off-white brand surface.
      // github-dark fights the warm-paper aesthetic of the rest of the site.
      theme: 'github-light',
    },
  },
  integrations: [
    mdx(),
    svelte(),
    sitemap(),
  ],
  vite: {
    build: {
      rollupOptions: {
        external: ['/pagefind/pagefind.js'],
      },
    },
  },
  redirects: {
    '/proof/baseline-eval-report': '/evidence/baseline-eval-report/',
    '/proof/workflow-vs-agent-comparison': '/evidence/workflow-vs-agent-comparison/',
    '/proof/trace-example': '/evidence/trace-example/',
    '/proof/failure-cases': '/evidence/failure-cases/',
    '/principles/': '/manifesto/',
  },
});
