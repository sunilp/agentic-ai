import { describe, it, expect } from 'vitest';
import { readdirSync } from 'node:fs';
import { STEPS, PARTS, holdsUp, neighbours, stepBySlug, kitUrl, writtenHref } from './governance-path';
import { ENTRIES } from './pattern-language';

describe('governance path', () => {
  it('numbers 22 steps from 1, in order', () => {
    expect(STEPS.map((s) => s.n)).toEqual(Array.from({ length: 22 }, (_, i) => i + 1));
  });

  it('gives every step a unique slug prefixed with its zero-padded number', () => {
    expect(new Set(STEPS.map((s) => s.slug)).size).toBe(22);
    for (const s of STEPS) expect(s.slug.startsWith(`${String(s.n).padStart(2, '0')}-`)).toBe(true);
  });

  it('keeps parts contiguous and in reading order', () => {
    const runs = STEPS.map((s) => s.part).filter((p, i, a) => i === 0 || a[i - 1] !== p);
    expect(runs).toEqual(PARTS);
  });

  it('only rests on earlier steps, so order and dependencies agree', () => {
    for (const s of STEPS) for (const d of s.restsOn) expect(d, `step ${s.n}`).toBeLessThan(s.n);
  });

  it('gives every step except the first something to rest on', () => {
    for (const s of STEPS) expect(s.restsOn.length > 0, `step ${s.n}`).toBe(s.n !== 1);
  });

  it('links only to patterns in the catalogue', () => {
    const slugs = new Set(ENTRIES.map((e) => e.slug));
    for (const s of STEPS) for (const p of s.patterns) expect(slugs.has(p), `step ${s.n}: ${p}`).toBe(true);
  });

  it('relates only to blueprints that exist', () => {
    const ids = new Set(readdirSync('src/content/architecture').map((f) => f.replace(/\.mdx$/, '')));
    for (const s of STEPS) for (const r of s.related) expect(ids.has(r), `step ${s.n}: ${r}`).toBe(true);
  });

  it('writes checklist lines in capitals', () => {
    for (const s of STEPS) {
      expect(s.checklist.item).toBe(s.checklist.item.toUpperCase());
      expect(s.checklist.response).toBe(s.checklist.response.toUpperCase());
    }
  });

  it('has no em dashes and no calendar language', () => {
    const all = JSON.stringify(STEPS);
    expect(all).not.toContain('\u2014');
    expect(all).not.toMatch(/\b\d+ days\b|\bweek \d+\b/i);
  });

  it('makes holdsUp the inverse of restsOn, leaving out the walk-through', () => {
    expect([...holdsUp(9)].sort((a, b) => a - b)).toEqual([10, 11, 17, 18, 20]);
    expect(holdsUp(22)).toEqual([]);
    for (const s of STEPS) expect(holdsUp(s.n)).not.toContain(22);
  });

  it('finds neighbours and steps by slug', () => {
    expect(neighbours(1).prev).toBeUndefined();
    expect(neighbours(1).next?.n).toBe(2);
    expect(neighbours(22).next).toBeUndefined();
    expect(stepBySlug('03-list-every-ai-system')?.n).toBe(3);
  });

  it('pins kit links to the framework tag', () => {
    expect(kitUrl('README.md')).toBe('https://github.com/sunilp/ai-governance-framework/blob/v2.2.0/README.md');
  });

  it('links a step only when its essay is written', () => {
    const href = writtenHref(new Set(['03-list-every-ai-system']));
    expect(href(3)).toBe('/governance/03-list-every-ai-system/');
    expect(href(4)).toBeNull();
  });

  it('never links a forthcoming book', () => {
    for (const s of STEPS) if (s.book && !s.book.url) expect(s.book.note.length).toBeGreaterThan(0);
    expect(STEPS.find((s) => s.book?.title === 'Designing Agentic Systems')?.book?.url).toBeUndefined();
  });
});
