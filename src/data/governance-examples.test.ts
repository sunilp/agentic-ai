import { describe, it, expect } from 'vitest';
import { EXAMPLES } from './governance-examples';
import { computeTier } from '~/lib/governance-tier';
import policy from './governance-policy.json';

describe('governance worked examples', () => {
  it('covers all six framework examples', () => {
    expect(EXAMPLES.map((e) => e.slug).sort()).toEqual([
      'agentic-research-assistant', 'credit-scoring-model', 'customer-service-chatbot',
      'document-summarization', 'fraud-detection', 'internal-knowledge-search',
    ]);
  });

  it.each(EXAMPLES)('$slug: the rule reproduces the tier the framework records', (e) => {
    expect(computeTier(e).tier).toBe(e.recordedTier);
  });

  it('points every example at a risk assessment that exists at the pinned tag', () => {
    const files = new Set(policy.manifest);
    for (const e of EXAMPLES) expect(files.has(`examples/${e.slug}/risk-assessment.md`), e.slug).toBe(true);
  });

  it('records a rationale whenever the approver raised a tier', () => {
    for (const e of EXAMPLES) if (e.approverRaisedTo) expect(e.rationale?.length ?? 0).toBeGreaterThan(20);
  });
});
