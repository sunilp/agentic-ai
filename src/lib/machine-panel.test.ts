import { describe, it, expect } from 'vitest';
import { panelFor } from './machine-panel';

describe('machine panel', () => {
  it('lists what step 18 rests on, with links only for written steps', () => {
    const p = panelFor(18, new Set(['03-list-every-ai-system']));
    expect(p.restsOn.map((r) => r.n)).toEqual([3, 9, 15]);
    expect(p.restsOn[0].href).toBe('/governance/03-list-every-ai-system/');
    expect(p.restsOn[1].href).toBeNull();
    expect(p.href).toBeNull();
  });

  it('names patterns with their catalogue layer colour', () => {
    const p = panelFor(10, new Set());
    const anti = p.patterns.find((x) => x.slug === 'rubber-stamp-verifier');
    expect(anti?.anti).toBe(true);
    expect(anti?.colour).toBe('#b08d20');
    expect(p.patterns.every((x) => x.href.startsWith('/patterns/'))).toBe(true);
  });

  it('gives step 1 nothing to rest on', () => {
    expect(panelFor(1, new Set()).restsOn).toEqual([]);
  });
});
