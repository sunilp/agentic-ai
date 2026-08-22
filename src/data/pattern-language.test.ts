import { describe, it, expect } from 'vitest';
import { readFileSync, readdirSync } from 'node:fs';
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

  it('retires exactly the six stubs', () => {
    expect(Object.keys(RETIRED)).toHaveLength(6);
  });

  // Guards a real production bug: astro.config.mjs's static `redirects` map wins over
  // the page src/pages/patterns/[...slug].astro generates for a real content collection
  // entry. If a slug stays in RETIRED after its essay lands, the build stays green and
  // `dist/patterns/<slug>/index.html` exists on disk, but it's the 425-byte meta-refresh
  // stub, not the essay, so a naive `test -f` check misses it entirely. The fix is to
  // remove the slug from both RETIRED (here) and its redirect line in astro.config.mjs.
  it('never retires a slug that now has an essay', () => {
    const dir = new URL('../content/patterns/', import.meta.url);
    const essaySlugs = new Set(
      readdirSync(dir)
        .filter((f) => f.endsWith('.mdx'))
        .map((f) => f.replace(/\.mdx$/, '')),
    );
    const offenders = Object.keys(RETIRED).filter((slug) => essaySlugs.has(slug));
    expect(
      offenders,
      `these slugs have an essay at src/content/patterns/<slug>.mdx but are still in RETIRED, ` +
        `so the static redirect in astro.config.mjs shadows the real page: ${offenders.join(', ')}. ` +
        `Remove each from RETIRED in src/data/pattern-language.ts and delete its redirect line in astro.config.mjs.`,
    ).toEqual([]);
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

  it('resolves every pattern slug declared in blueprint frontmatter', () => {
    const dir = new URL('../content/architecture/', import.meta.url);
    const valid = new Set([...ENTRIES.map((e) => e.slug), ...REFERENCED.map((r) => r.slug)]);
    for (const file of readdirSync(dir).filter((f) => f.endsWith('.mdx'))) {
      const m = readFileSync(new URL(file, dir), 'utf8').match(/^patterns: \[(.*?)\]/m);
      if (!m) continue;
      for (const slug of m[1].split(',').map((s) => s.trim()).filter(Boolean)) {
        expect(valid.has(slug), `${file} references unknown pattern "${slug}"`).toBe(true);
      }
    }
  });

  it('resolves every blueprints value to a real architecture entry', () => {
    const dir = new URL('../content/architecture/', import.meta.url);
    const archIds = new Set(
      readdirSync(dir)
        .filter((f) => f.endsWith('.mdx'))
        .map((file) => readFileSync(new URL(file, dir), 'utf8').match(/^id: (\S+)$/m))
        .filter((m): m is RegExpMatchArray => m !== null)
        .map((m) => m[1]),
    );
    // Collect the (slug, blueprintId) pairs before asserting anything, so the test cannot
    // pass vacuously: if the catalogue ever stops populating `blueprints` on any entry, this
    // fails loudly instead of the loop below silently asserting nothing.
    const pairs = ENTRIES.flatMap((e) => (e.blueprints ?? []).map((archId) => ({ slug: e.slug, archId })));
    expect(pairs.length, 'no ENTRIES declare a blueprints value; this test would pass vacuously').toBeGreaterThan(0);
    for (const { slug, archId } of pairs) {
      expect(archIds.has(archId), `${slug} names unknown blueprint "${archId}"`).toBe(true);
    }
  });

  // Guards the actual bug, not just the data: PatternLayout.astro once built blueprint
  // hrefs directly from the frontmatter id (`/architecture/${id}/`, e.g. `/architecture/arch-001/`),
  // which 404s because the architecture collection routes on the collection filename
  // (e.g. `/architecture/001-the-control-plane/`), not the frontmatter id. A revert of that
  // fix would keep every blueprint id valid (the data-integrity test above would still pass)
  // while silently reintroducing the 404. This is a source-grep, which is a blunt instrument;
  // it stands in for a rendered-HTML assertion until pattern essays exist to render, which
  // belongs in the final verification task.
  it('builds blueprint hrefs from the collection entry, not the frontmatter id', () => {
    const src = readFileSync(new URL('../layouts/PatternLayout.astro', import.meta.url), 'utf8');
    expect(src).not.toMatch(/\/architecture\/\$\{id\}\//);
    expect(src).not.toMatch(/\/architecture\/\$\{[a-zA-Z]*[Aa]rch[a-zA-Z]*\}\//);
    expect(src).toContain("getCollection('architecture')");
    expect(src).toMatch(/blueprintFor|\.find\(\(b\) => b\.data\.id === /);
  });
});
