// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://sunilprakash.com',
  base: '/agentic-ai',
  trailingSlash: 'always',
  build: {
    format: 'directory',
  },
  integrations: [
    mdx(),
    svelte(),
    sitemap(),
  ],
  vite: {
    build: {
      rollupOptions: {
        external: ['/agentic-ai/pagefind/pagefind.js'],
      },
    },
  },
  redirects: {
    '/proof/baseline-eval-report': '/agentic-ai/evidence/baseline-eval-report/',
    '/proof/workflow-vs-agent-comparison': '/agentic-ai/evidence/workflow-vs-agent-comparison/',
    '/proof/trace-example': '/agentic-ai/evidence/trace-example/',
    '/proof/failure-cases': '/agentic-ai/evidence/failure-cases/',
    '/principles/': '/agentic-ai/manifesto/',
  },
});
