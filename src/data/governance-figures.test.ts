import { describe, it, expect } from 'vitest';
import { HOURGLASS, DIAMOND, refSteps } from './governance-figures';

describe('governance figures', () => {
  it('puts the register, tier, gates, evidence and platform at the narrow waist', () => {
    expect(refSteps(HOURGLASS.waist.refs)).toEqual([3, 4, 9, 10, 20]);
  });

  it('refers only to real steps', () => {
    const all = [HOURGLASS.upper, HOURGLASS.waist, HOURGLASS.lower, HOURGLASS.below, ...DIAMOND.bands].flatMap((b) => refSteps(b.refs));
    for (const n of all) expect(n >= 1 && n <= 22, String(n)).toBe(true);
  });

  it('has no em dashes', () => {
    expect(JSON.stringify([HOURGLASS, DIAMOND])).not.toContain(String.fromCharCode(0x2014));
  });
});
