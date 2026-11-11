import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import policy from './governance-policy.json';
import { STEPS, FRAMEWORK_TAG } from './governance-path';

describe('governance policy snapshot', () => {
  it('is pinned to the tag the kit links use', () => {
    expect(policy.source).toBe(`ai-governance-framework@${FRAMEWORK_TAG}`);
  });

  it('has the four tiers with every field filled', () => {
    expect(Object.keys(policy.tiers)).toEqual(['T1', 'T2', 'T3', 'T4']);
    for (const tier of Object.values(policy.tiers)) {
      expect(Object.keys(tier).sort()).toEqual(['approver', 'metricsReview', 'name', 'redTeam', 'revalidation', 'reviewCadence', 'validation']);
      for (const v of Object.values(tier)) expect(typeof v === 'string' && v.length > 0).toBe(true);
    }
  });

  it('has no em dash in the tier rule, the worked examples or the policy snapshot', () => {
    const dash = String.fromCharCode(0x2014);
    for (const f of ['src/lib/governance-tier.ts', 'src/data/governance-examples.ts', 'src/data/governance-policy.json']) {
      expect(readFileSync(f, 'utf8').includes(dash), f).toBe(false);
    }
  });

  it('contains every starter-kit path', () => {
    const files = new Set(policy.manifest);
    for (const s of STEPS) for (const p of s.kit) expect(files.has(p), `step ${s.n}: ${p}`).toBe(true);
  });
});
