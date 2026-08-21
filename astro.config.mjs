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
    '/patterns/agent-loop/': '/patterns/',
    '/patterns/approval-gate/': '/patterns/#approval-gate',
    '/patterns/cold-start-mitigation/': '/patterns/',
    '/patterns/earn-the-complexity/': '/patterns/#earn-the-complexity',
    '/patterns/escalation-path/': '/patterns/#escalation-path',
    '/patterns/eval-loop/': '/patterns/#failure-buckets',
    '/patterns/failure-buckets/': '/patterns/#failure-buckets',
    '/patterns/hub-and-spoke/': '/patterns/#orchestrator-workers',
    '/patterns/tool-registry/': '/patterns/#tool-agent-registry',
    '/patterns/trace-the-truth/': '/patterns/#split-the-log',
    '/patterns/verifier-loop/': '/patterns/#verifier-loop',
    '/patterns/workflow-first/': '/patterns/#workflow-first',
  },
});
