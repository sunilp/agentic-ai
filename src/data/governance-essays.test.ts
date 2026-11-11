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

    it(`${file}: follows the step anatomy, in order`, () => {
      const markers = ['## The move', '## How it works', '## How it scales', '<Track for="small">', '<Track for="enterprise">', '<Shortcut quote=', `<StarterKit n={${step!.n}} />`, '<DeepDive>'];
      for (const m of markers) expect(raw.includes(m), m).toBe(true);
      const at = (m: string) => raw.indexOf(m);
      expect(at('## The move')).toBeLessThan(at('## How it works'));
      expect(at('## How it works')).toBeLessThan(at('## How it scales'));
      expect(at('## How it scales')).toBeLessThan(at('<Shortcut quote='));
      expect(at('<Shortcut quote=')).toBeLessThan(at('<StarterKit'));
      expect(at('<StarterKit')).toBeLessThan(at('<DeepDive>'));
    });

    it(`${file}: no em dashes, no leftover markers, no calendar`, () => {
      expect(raw).not.toContain(String.fromCharCode(0x2014));
      expect(raw).not.toMatch(/\b(TODO|TBD|FIXME)\b/);
      expect(raw).not.toMatch(/\bfirst \d+ days\b|\b\d+-day plan\b|\bweek \d+\b/i);
    });

    it(`${file}: cites sources`, () => {
      expect(raw).toMatch(/^sources:\s*$/m);
    });
  }
});
