import { describe, it, expect } from 'vitest';
import { density } from '../../scripts/lib/prose-density.mjs';

describe('prose density', () => {
  it('counts you and hedges per 1,000 words of prose only', () => {
    const mdx = `---\ntitle: x\n---\nimport A from 'a';\n\nYou set the tier now. It may change. <Track for="small">Your call.</Track>\n\n\`\`\`\nyou you you\n\`\`\`\n`;
    const d = density(mdx);
    expect(d.words).toBe(10);
    expect(d.youPer1k).toBe(200);
    expect(d.hedgesPer1k).toBe(100);
  });
});
