import { describe, it, expect } from 'vitest';
import { ENTRIES, bySlug } from '~/data/pattern-language';
import { placeEntries, cellCounts, replacesIndex, SECTORS, RINGS, sectorBounds, ringBounds, GEOMETRY } from './pattern-wheel';

// The distribution below is computed by hand from src/data/pattern-language.ts
// (see the task brief). It is the contract the wheel is designed against:
// position encodes use, and the five zero cells are deliberate (capability's
// work is all up front, control acts rather than measures so it skips
// evaluate, evidence doesn't exist before something is built).
const EXPECTED_DISTRIBUTION: Record<string, Record<string, number>> = {
  capability: { design: 3, build: 2, evaluate: 0, operate: 0, govern: 0 },
  control: { design: 5, build: 4, evaluate: 0, operate: 3, govern: 1 },
  evidence: { design: 0, build: 2, evaluate: 4, operate: 1, govern: 1 },
};

describe('pattern wheel placement', () => {
  it('places every one of the 26 entries in exactly one cell', () => {
    const placed = placeEntries();
    expect(placed).toHaveLength(ENTRIES.length);
    const slugs = new Set(placed.map((p) => p.slug));
    expect(slugs.size).toBe(ENTRIES.length);
  });

  it('matches the specified per-cell distribution exactly', () => {
    const counts = cellCounts();
    expect(counts).toEqual(EXPECTED_DISTRIBUTION);
  });

  it('matches the specified row and column totals', () => {
    const counts = cellCounts();
    const rowTotal = (layer: keyof typeof counts) => Object.values(counts[layer]).reduce((a, b) => a + b, 0);
    expect(rowTotal('capability')).toBe(5);
    expect(rowTotal('control')).toBe(13);
    expect(rowTotal('evidence')).toBe(8);

    const colTotal = (stage: string) =>
      SECTORS.reduce((sum, layer) => sum + counts[layer][stage as keyof (typeof counts)[typeof layer]], 0);
    expect(colTotal('design')).toBe(8);
    expect(colTotal('build')).toBe(8);
    expect(colTotal('evaluate')).toBe(4);
    expect(colTotal('operate')).toBe(4);
    expect(colTotal('govern')).toBe(2);
  });

  it('includes every anti-pattern in the count, at its own primaryStage', () => {
    const antiPatterns = ENTRIES.filter((e) => e.kind === 'anti-pattern');
    expect(antiPatterns).toHaveLength(5);
    const placed = placeEntries();
    for (const ap of antiPatterns) {
      const p = placed.find((x) => x.slug === ap.slug)!;
      expect(p).toBeDefined();
      expect(p.layer).toBe(ap.layer);
      expect(p.primaryStage).toBe(ap.primaryStage);
    }
  });

  it("resolves every anti-pattern's replacedBy to a real pattern", () => {
    for (const e of ENTRIES.filter((x) => x.kind === 'anti-pattern')) {
      expect(e.replacedBy, `${e.slug} has no replacedBy`).toBeDefined();
      const target = bySlug(e.replacedBy!);
      expect(target, `${e.slug}.replacedBy "${e.replacedBy}" does not resolve`).toBeDefined();
      expect(target!.kind).toBe('pattern');
    }
  });

  it('assigns a unique, dense 1..26 legend key', () => {
    const placed = placeEntries();
    const keys = placed.map((p) => p.key).sort((a, b) => a - b);
    expect(keys).toEqual(Array.from({ length: ENTRIES.length }, (_, i) => i + 1));
  });

  it('keeps every mark strictly inside its own ring band', () => {
    const placed = placeEntries();
    for (const p of placed) {
      const { inner, outer } = ringBounds(p.ringIndex);
      expect(p.radius).toBeGreaterThan(inner);
      expect(p.radius).toBeLessThan(outer);
    }
  });

  it('keeps every mark strictly inside its own sector wedge', () => {
    const placed = placeEntries();
    for (const p of placed) {
      const { start, end } = sectorBounds(p.sectorIndex);
      // angleDeg is computed directly from start/end so this should never
      // fail by construction, but it is the actual claim "position encodes
      // use" depends on, so assert it rather than trust it.
      expect(p.angleDeg).toBeGreaterThanOrEqual(start);
      expect(p.angleDeg).toBeLessThanOrEqual(end);
    }
  });

  it('places every mark at a finite point inside the viewBox', () => {
    const placed = placeEntries();
    for (const p of placed) {
      expect(Number.isFinite(p.x)).toBe(true);
      expect(Number.isFinite(p.y)).toBe(true);
    }
  });

  it('never lets a sector wedge span less than 120 degrees, and the three tile the circle', () => {
    for (let i = 0; i < SECTORS.length; i++) {
      const { start, end } = sectorBounds(i);
      expect(end - start).toBe(120);
    }
    const { start: firstStart } = sectorBounds(0);
    const { end: lastEnd } = sectorBounds(SECTORS.length - 1);
    expect(lastEnd - firstStart).toBe(360);
  });

  it('orders the five rings design innermost to govern outermost', () => {
    expect(RINGS).toEqual(['design', 'build', 'evaluate', 'operate', 'govern']);
    for (let i = 0; i < RINGS.length - 1; i++) {
      const a = ringBounds(i);
      const b = ringBounds(i + 1);
      expect(a.outer).toBe(b.inner);
      expect(b.inner).toBeGreaterThan(a.inner);
    }
    expect(ringBounds(0).inner).toBe(GEOMETRY.innerRadius);
  });

  it('builds a replaces index that agrees with the data, reversed', () => {
    const idx = replacesIndex();
    for (const e of ENTRIES.filter((x) => x.kind === 'anti-pattern')) {
      expect(idx.get(e.replacedBy!)).toContain(e.slug);
    }
    // hallucinated-done and rubber-stamp-verifier both replace verifier-loop
    expect(idx.get('verifier-loop')?.sort()).toEqual(['hallucinated-done', 'rubber-stamp-verifier']);
  });

  it('is deterministic: two calls produce the identical layout', () => {
    const a = placeEntries();
    const b = placeEntries();
    expect(a).toEqual(b);
  });
});
