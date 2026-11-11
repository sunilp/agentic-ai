import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { parsePreview, chapterNumber, isFree } from './book';

const STUB = `Intro line.

## What this chapter covers

- **Tools as contracts** -- function calling with validation
- **The agent loop** -- the observe-think-act cycle

## Code companion

The working code for this chapter is in [\`src/ch02/\`](https://github.com/sunilp/agentic-ai/tree/main/src/ch02):

- \`agent.py\` -- First working agent

## Get the full chapter

The complete chapter text is available in the book.
`;

describe('book helpers', () => {
  it('reads the outline and the code link from a preview', () => {
    const p = parsePreview(STUB);
    expect(p.points).toEqual([
      { title: 'Tools as contracts', text: 'function calling with validation' },
      { title: 'The agent loop', text: 'the observe-think-act cycle' },
    ]);
    expect(p.code).toEqual({ label: 'src/ch02/', href: 'https://github.com/sunilp/agentic-ai/tree/main/src/ch02' });
  });

  it('returns nothing for a preview with no outline', () => {
    expect(parsePreview('One line.\n\n## Get the full chapter\n\nIn the book.\n')).toEqual({ points: [], code: undefined });
  });

  it('does not read bullets from another section as the outline', () => {
    const p = parsePreview('## Code companion\n\n- **Not an outline** -- no\n');
    expect(p.points).toEqual([]);
  });

  it('numbers chapters from their file names', () => {
    expect(chapterNumber('02-tools-context-agent-loop')).toBe('02');
    expect(chapterNumber('00a-how-llms-work')).toBe('00a');
  });

  it('treats drafts as book-only', () => {
    expect(isFree({ data: { status: 'draft' } })).toBe(false);
    expect(isFree({ data: { status: 'published' } })).toBe(true);
    expect(isFree({ data: {} })).toBe(true);
  });

  it('parses every real book-only chapter without leaking markup', () => {
    const dir = 'src/content/chapters';
    for (const f of readdirSync(dir).filter((x) => x.endsWith('.mdx'))) {
      const raw = readFileSync(`${dir}/${f}`, 'utf8');
      if (!/^status: draft$/m.test(raw)) continue;
      const p = parsePreview(raw.split(/^---$/m).slice(2).join('---'));
      for (const pt of p.points) {
        expect(pt.title, f).not.toMatch(/[*`]/);
        expect(pt.text, f).not.toMatch(/^--/);
      }
      if (p.code) expect(p.code.href, f).toMatch(/^https:\/\/github\.com\/sunilp\/agentic-ai\//);
    }
  });
});
