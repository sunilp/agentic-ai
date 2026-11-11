import { describe, it, expect } from 'vitest';
import { computeTier, OVERRIDES, type Level } from './governance-tier';

const dims = (...levels: Level[]) => levels.map((level, i) => ({ name: `Dimension ${i + 1}`, level }));

describe('governance tiering rule', () => {
  it('gives T4 when every dimension is Low', () => {
    expect(computeTier({ dimensions: dims('Low', 'Low', 'Low', 'Low', 'Low'), overrides: [] }).tier).toBe('T4');
  });

  it('gives T1 when any dimension is Critical', () => {
    expect(computeTier({ dimensions: dims('Low', 'Critical', 'Low', 'Low', 'Low'), overrides: [] }).tier).toBe('T1');
  });

  it('takes the highest dimension, not the sum', () => {
    expect(computeTier({ dimensions: dims('Medium', 'Medium', 'Medium', 'Medium', 'High'), overrides: [] }).tier).toBe('T2');
  });

  it('lets override 6 raise a T3 agent to T2', () => {
    const r = computeTier({ dimensions: dims('Medium', 'Low'), overrides: [6] });
    expect(r.scored).toBe('T3');
    expect(r.tier).toBe('T2');
  });

  it('never lets an override lower a tier', () => {
    expect(computeTier({ dimensions: dims('Critical'), overrides: [6] }).tier).toBe('T1');
  });

  it('lets the approver raise a tier but never lower it', () => {
    expect(computeTier({ dimensions: dims('High'), overrides: [], approverRaisedTo: 'T1' }).tier).toBe('T1');
    const lowered = computeTier({ dimensions: dims('High'), overrides: [], approverRaisedTo: 'T3' });
    expect(lowered.tier).toBe('T2');
    expect(lowered.reasons.join(' ')).toContain('cannot lower');
  });

  it('rejects a prohibited use instead of tiering it', () => {
    expect(computeTier({ prohibited: true, dimensions: dims('Low'), overrides: [] }).tier).toBe('rejected');
  });

  it('refuses unknown override numbers', () => {
    expect(() => computeTier({ dimensions: dims('Low'), overrides: [10] })).toThrow('unknown override');
  });

  it('numbers the canonical override list 1 to 9, five automatic T1 then four minimum T2', () => {
    expect(OVERRIDES.map((o) => o.item)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9]);
    expect(OVERRIDES.map((o) => o.floor)).toEqual(['T1', 'T1', 'T1', 'T1', 'T1', 'T2', 'T2', 'T2', 'T2']);
  });
});
