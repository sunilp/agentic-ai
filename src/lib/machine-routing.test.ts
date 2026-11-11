import { describe, it, expect } from 'vitest';
import { PARTS, FRAME, labelBoxes, type Rect } from '~/data/governance-machine';
import { STEPS } from '~/data/governance-path';
import { routeLinks, roundedPath, type Pt } from './machine-routing';

const inflate = (r: Rect, m: number): Rect => ({ x: r.x - m, y: r.y - m, w: r.w + 2 * m, h: r.h + 2 * m });

function hits(a: Pt, b: Pt, r: Rect): boolean {
  if (a[1] === b[1]) {
    const y = a[1], x0 = Math.min(a[0], b[0]), x1 = Math.max(a[0], b[0]);
    return y > r.y && y < r.y + r.h && x1 > r.x && x0 < r.x + r.w;
  }
  if (a[0] === b[0]) {
    const x = a[0], y0 = Math.min(a[1], b[1]), y1 = Math.max(a[1], b[1]);
    return x > r.x && x < r.x + r.w && y1 > r.y && y0 < r.y + r.h;
  }
  throw new Error(`segment ${a} to ${b} is not axis-aligned`);
}

describe('machine routing', () => {
  it('has exactly one part for every step from 1 to 21', () => {
    expect(PARTS.map((p) => p.n).sort((a, b) => a - b)).toEqual(Array.from({ length: 21 }, (_, i) => i + 1));
  });

  for (const step of STEPS.filter((s) => s.n <= 21)) {
    it(`step ${step.n}: one link per dependency, clear of every other part and every label`, () => {
      const links = routeLinks(step.n);
      expect(links).toHaveLength(step.restsOn.length);
      for (const l of links) {
        const obstacles = [
          ...PARTS.filter((p) => p.n !== l.from && p.n !== l.to),
          ...labelBoxes().map((b) => inflate(b, 2)),
        ];
        for (let i = 1; i < l.points.length; i++) {
          for (const r of obstacles) {
            expect(hits(l.points[i - 1], l.points[i], r), `${l.from} to ${l.to}, segment ${i}, hits ${JSON.stringify(r)}`).toBe(false);
          }
        }
        for (const [x, y] of l.points) {
          expect(x >= 0 && x <= FRAME.width && y >= 0 && y <= FRAME.height, `${l.from} to ${l.to} leaves the frame`).toBe(true);
        }
      }
      const starts = links.map((l) => l.points[0].join(','));
      expect(new Set(starts).size).toBe(starts.length);
    });
  }

  it('draws nothing for the walk-through', () => {
    expect(routeLinks(22)).toEqual([]);
  });

  it('rounds the corners', () => {
    expect(roundedPath([[0, 0], [20, 0], [20, 20]])).toMatch(/Q20 0 20 7/);
  });
});
