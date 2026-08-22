import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
import { bySlug } from './pattern-language';

// The two fixed body-structure shapes, per the pattern-language design spec section 5.
// Every pattern essay uses exactly the first set of headings, in order; every
// anti-pattern essay uses exactly the second, inverted set. These are deliberately
// hard-coded, not derived, because the whole point of the test is to catch an essay
// that drifts from the fixed shape.
const PATTERN_HEADINGS = ['The problem', 'Forces', 'The pattern', 'Worked example', 'When not to use it', 'Related patterns'];

const ANTI_PATTERN_HEADINGS = [
  'What it looks like in the wild',
  'Why it happens',
  'What it costs',
  'Worked example',
  'The pattern that replaces it',
  'Related patterns',
];

// Astro's actual heading-id generation (github-slugger, via the MDX pipeline) is not
// reachable from a plain vitest run. Every heading this catalogue uses is plain
// lower-and-upper-case words separated by spaces, so a plain lowercase-and-hyphenate
// slugifier produces the same id Astro does for this content. The build-time check in
// the verification task (grepping id="..." out of the rendered dist HTML) is what
// actually proves the two agree; this is the fast, offline half of that guarantee.
function slugify(heading: string): string {
  return heading
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-');
}

function splitFrontmatter(raw: string): { frontmatter: string; body: string } {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!match) throw new Error('no frontmatter block found');
  return { frontmatter: match[1], body: raw.slice(match[0].length) };
}

function extractAnchors(frontmatter: string): { label: string; anchor: string }[] {
  const block = frontmatter.match(/^anchors:\n((?:  - .*\n?)+)/m);
  if (!block) throw new Error('no anchors block found in frontmatter');
  return block[1]
    .trim()
    .split('\n')
    .map((line) => {
      const m = line.match(/label:\s*(.+?),\s*anchor:\s*([a-z0-9-]+)\s*}/);
      if (!m) throw new Error(`could not parse anchor line: ${line}`);
      return { label: m[1].trim(), anchor: m[2].trim() };
    });
}

function extractH2Headings(body: string): string[] {
  return [...body.matchAll(/^##\s+(.+)$/gm)].map((m) => m[1].trim());
}

const dir = new URL('../content/patterns/', import.meta.url);
const files = readdirSync(dir).filter((f) => f.endsWith('.mdx'));

describe('pattern essay body structure', () => {
  it('has at least one essay to check', () => {
    // Guards against this whole suite passing vacuously once every file below is deleted.
    expect(files.length).toBeGreaterThan(0);
  });

  for (const file of files) {
    const slug = file.replace(/\.mdx$/, '');
    const raw = readFileSync(new URL(file, dir), 'utf8');
    const { frontmatter, body } = splitFrontmatter(raw);
    const headings = extractH2Headings(body);
    const anchors = extractAnchors(frontmatter);

    describe(slug, () => {
      it('resolves via bySlug', () => {
        expect(bySlug(slug)).toBeDefined();
      });

      it('declares the required h2 sections, in order, for its kind', () => {
        const entry = bySlug(slug);
        if (!entry) throw new Error(`no pattern-language entry for ${slug}`);
        const expected = entry.kind === 'pattern' ? PATTERN_HEADINGS : ANTI_PATTERN_HEADINGS;
        expect(headings).toEqual(expected);
      });

      it('declares anchors matching the slugified headings', () => {
        expect(anchors.map((a) => a.anchor)).toEqual(headings.map(slugify));
      });

      it('contains no em dash', () => {
        expect(raw).not.toContain('—');
      });
    });
  }
});
