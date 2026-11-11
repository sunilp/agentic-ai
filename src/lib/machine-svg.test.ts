import { describe, it, expect } from 'vitest';
import { renderMachineSvg, partState, machineLabel } from './machine-svg';
import { PARTS } from '~/data/governance-machine';

const count = (s: string, needle: string) => s.split(needle).length - 1;

describe('machine svg', () => {
  it('draws 21 parts and one link per dependency of the selected step', () => {
    const svg = renderMachineSvg({ selected: 9, mode: 'explore' });
    expect(count(svg, 'data-step="')).toBe(21);
    expect(count(svg, 'class="machine__link"')).toBe(3);
    expect(svg).not.toContain('NaN');
  });

  it('marks what the selected step rests on and holds up', () => {
    expect(partState(9, 9, 'explore')).toBe('selected');
    for (const n of [4, 6, 8]) expect(partState(n, 9, 'explore')).toBe('restsOn');
    for (const n of [10, 11, 17, 18, 20]) expect(partState(n, 9, 'explore')).toBe('holdsUp');
    expect(partState(1, 9, 'explore')).toBe('faded');
  });

  it('shows built and future parts in progress mode', () => {
    expect(partState(1, 3, 'progress')).toBe('built');
    expect(partState(2, 3, 'progress')).toBe('restsOn');
    expect(partState(4, 3, 'progress')).toBe('holdsUp');
    expect(partState(5, 3, 'progress')).toBe('future');
  });

  it('links only written steps, and uses buttons when interactive', () => {
    const href = (n: number) => (n === 3 ? '/governance/03-list-every-ai-system/' : null);
    const linked = renderMachineSvg({ selected: 3, mode: 'progress', href });
    expect(count(linked, '<a ')).toBe(1);
    const buttons = renderMachineSvg({ selected: 3, mode: 'explore', href, interactive: true });
    expect(count(buttons, 'role="button"')).toBe(21);
    expect(count(buttons, '<a ')).toBe(0);
  });

  it('fits every label inside its part', () => {
    for (const p of PARTS) {
      const width = machineLabel(p.n).length * 6.66;
      if (p.n === 20) expect(width, 'rail').toBeLessThanOrEqual(p.h - 28);
      else expect(width + 10, `step ${p.n}`).toBeLessThanOrEqual(p.w - 6);
    }
  });

  it('has no em dashes', () => {
    expect(renderMachineSvg({ selected: 18, mode: 'explore' })).not.toContain(String.fromCharCode(0x2014));
  });
});
