import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { ENTRIES, REFERENCED, RETIRED, bySlug, byLayer, byStage, counts } from './pattern-language';

describe('pattern language data', () => {
  // Deliberately no hard-coded total. Spec section 7 test 6 forbids hard-coded counts,
  // because Task 1 may reclassify or drop an entry and that must not force a test edit.
  // These assert structure instead, which is what actually protects the catalogue.
  it('splits cleanly by kind and by status, with nothing uncounted', () => {
    const c = counts();
    expect(c.patterns + c.antiPatterns).toBe(ENTRIES.length);
    expect(c.documented + c.restated + c.proposed).toBe(ENTRIES.length);
  });

  it('puts every entry in exactly one layer group', () => {
    const seen = (['capability', 'control', 'evidence'] as const).flatMap((l) => byLayer(l).map((e) => e.slug));
    expect(seen).toHaveLength(ENTRIES.length);
    expect(new Set(seen).size).toBe(ENTRIES.length);
  });

  it('has unique slugs across entries and the referenced band', () => {
    // Retired stub slugs are deliberately NOT in this check. Six of them are also
    // catalogue slugs, because /patterns/approval-gate/ now redirects to the
    // approval-gate anchor on the index. That collision is the design, not a bug.
    const all = [...ENTRIES.map((e) => e.slug), ...REFERENCED.map((r) => r.slug)];
    expect(new Set(all).size).toBe(all.length);
  });

  it('points every retired stub at an anchor that exists, or at the index', () => {
    const anchors = new Set([...ENTRIES.map((e) => e.slug), ...REFERENCED.map((r) => r.slug)]);
    for (const target of Object.values(RETIRED)) {
      if (target === '/patterns/') continue;
      const anchor = target.split('#')[1];
      expect(anchor, `no entry or referenced slug for ${target}`).toBeDefined();
      expect(anchors.has(anchor)).toBe(true);
    }
  });

  it('requires attributedTo on every documented entry', () => {
    for (const e of ENTRIES.filter((x) => x.status === 'documented')) {
      expect(e.attributedTo.url).toMatch(/^https:\/\//);
      expect(e.attributedTo.who.length).toBeGreaterThan(0);
    }
  });

  it('requires at least one nearestPrior on every restated entry', () => {
    for (const e of ENTRIES.filter((x) => x.status === 'restated')) {
      expect(e.nearestPrior.length).toBeGreaterThan(0);
      for (const n of e.nearestPrior) expect(n.url).toMatch(/^https:\/\//);
    }
  });

  it('resolves every related slug', () => {
    for (const e of ENTRIES) {
      for (const r of e.related ?? []) expect(bySlug(r)).toBeDefined();
    }
  });

  it('gives every anti-pattern a replacedBy that resolves to a pattern', () => {
    for (const e of ENTRIES.filter((x) => x.kind === 'anti-pattern')) {
      const target = bySlug(e.replacedBy!);
      expect(target).toBeDefined();
      expect(target!.kind).toBe('pattern');
    }
  });

  it('retires exactly the twelve stubs', () => {
    expect(Object.keys(RETIRED)).toHaveLength(12);
  });

  it('well-forms every url without fetching it', () => {
    const urls = [
      ...REFERENCED.map((r) => r.url),
      ...ENTRIES.flatMap((e) => (e.status === 'documented' ? [e.attributedTo.url] : [])),
      ...ENTRIES.flatMap((e) => (e.status === 'restated' ? e.nearestPrior.map((n) => n.url) : [])),
    ];
    for (const u of urls) expect(() => new URL(u)).not.toThrow();
  });

  it('derives counts that agree with the data', () => {
    const c = counts();
    expect(c.total).toBe(ENTRIES.length);
    expect(c.patterns + c.antiPatterns).toBe(c.total);
    expect(c.documented + c.restated + c.proposed).toBe(c.total);
    const stageTotal = Object.values(c.stages).reduce((a, b) => a + b, 0);
    expect(stageTotal).toBe(c.total);
  });

  it('groups without losing entries', () => {
    const layered = (['capability', 'control', 'evidence'] as const).flatMap((l) => byLayer(l));
    expect(layered).toHaveLength(ENTRIES.length);
    const staged = (['design', 'build', 'evaluate', 'operate', 'govern'] as const).flatMap((s) => byStage(s));
    expect(staged.length).toBeGreaterThanOrEqual(ENTRIES.length);
  });

  it('contains no em dash in any prose field', () => {
    const prose = ENTRIES.flatMap((e) => [e.name, e.oneLine, ...(e.alsoKnownAs ?? [])]).join(' ');
    expect(prose).not.toContain('—');
  });

  it('has an astro redirect for every retired stub', () => {
    const config = readFileSync(new URL('../../astro.config.mjs', import.meta.url), 'utf8');
    for (const [slug, target] of Object.entries(RETIRED)) {
      expect(config).toContain(`'/patterns/${slug}/': '${target}'`);
    }
  });
});
