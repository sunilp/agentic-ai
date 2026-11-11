#!/usr/bin/env node
// Usage: node scripts/prose-density.mjs src/content/governance/*.mdx
import { readFileSync } from 'node:fs';
import { density } from './lib/prose-density.mjs';

for (const file of process.argv.slice(2)) {
  const d = density(readFileSync(file, 'utf8'));
  const flag = d.youPer1k < 8 || d.hedgesPer1k > 2 ? '  <- check' : '';
  console.log(`${file}: ${d.words} words, you ${d.youPer1k}/1k (target 8+), hedges ${d.hedgesPer1k}/1k (target 2 or fewer)${flag}`);
}
