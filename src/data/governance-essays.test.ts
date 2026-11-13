import { describe, it, expect } from 'vitest';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { stepBySlug } from './governance-path';

const DIR = 'src/content/governance';
const files = existsSync(DIR) ? readdirSync(DIR).filter((f) => f.endsWith('.mdx')) : [];

describe('governance essays', () => {
  it('scans the essay folder', () => {
    expect(Array.isArray(files)).toBe(true);
  });

  for (const file of files) {
    const raw = readFileSync(`${DIR}/${file}`, 'utf8');
    const step = stepBySlug(file.replace(/\.mdx$/, ''));

    it(`${file}: joins to a step`, () => {
      expect(step).toBeDefined();
    });

    const h2 = [...raw.matchAll(/^## (.+)$/gm)];

    it(`${file}: follows the step anatomy, in order`, () => {
      const markers = ['<Track for="small">', '<Track for="enterprise">', '<Shortcut quote=', `<StarterKit n={${step!.n}} />`, '<DeepDive>'];
      for (const m of markers) expect(raw.includes(m), m).toBe(true);
      const at = (m: string) => raw.indexOf(m);
      // Three sections come before the shortcut: the instruction, how it works, how it changes with size.
      const sections = h2.filter((h) => h.index! < at('<Shortcut quote='));
      expect(sections.length).toBeGreaterThanOrEqual(3);
      expect(sections[sections.length - 1].index!).toBeLessThan(at('<Track for="small">'));
      expect(at('<Track for="small">')).toBeLessThan(at('<Track for="enterprise">'));
      expect(at('<Track for="enterprise">')).toBeLessThan(at('<Shortcut quote='));
      expect(at('<Shortcut quote=')).toBeLessThan(at('<StarterKit'));
      expect(at('<StarterKit')).toBeLessThan(at('<DeepDive>'));
    });

    it(`${file}: headings name the subject, not the slot`, () => {
      for (const [, text] of h2) {
        expect(text).not.toMatch(/^(The move|How it works|How it scales|Deep dive)$/i);
        expect(text.split(/\s+/).length, text).toBeLessThanOrEqual(8);
        expect(text, text).not.toMatch(/[:?]/);
      }
      // The contents list is built from these headings, so the frontmatter carries none.
      expect(raw).not.toMatch(/^anchors:/m);
    });

    it(`${file}: no em dashes, no leftover markers, no calendar`, () => {
      expect(raw).not.toContain(String.fromCharCode(0x2014));
      expect(raw).not.toContain(String.fromCharCode(0x2013));
      expect(raw).not.toMatch(/\b(TODO|TBD|FIXME)\b/);
      expect(raw).not.toMatch(/\bfirst \d+ days\b|\b\d+-day plan\b|\bweek \d+\b/i);
    });

    it(`${file}: cites sources`, () => {
      expect(raw).toMatch(/^sources:\s*$/m);
    });
  }

  it('no two steps share a section heading', () => {
    const seen = new Map<string, string>();
    for (const file of files) {
      const raw = readFileSync(`${DIR}/${file}`, 'utf8');
      for (const [, text] of raw.matchAll(/^## (.+)$/gm)) {
        expect(seen.get(text), `"${text}" is in ${seen.get(text)} and ${file}`).toBeUndefined();
        seen.set(text, file);
      }
    }
  });
});
