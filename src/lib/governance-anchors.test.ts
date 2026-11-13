import { describe, it, expect } from 'vitest';
import { stepAnchors } from './governance-anchors';

describe('stepAnchors', () => {
  const headings = [
    { depth: 2, slug: 'one-name-on-every-decision', text: 'One name on every decision' },
    { depth: 3, slug: 'three-lines', text: 'Three lines' },
    { depth: 2, slug: 'who-signs-in-a-team-of-five', text: 'Who signs in a team of five' },
  ];

  it('lists the h2 headings in order and skips deeper ones', () => {
    expect(stepAnchors(headings).map((a) => a.anchor)).toEqual(['one-name-on-every-decision', 'who-signs-in-a-team-of-five']);
  });

  it('adds the Deep dive when the essay has one', () => {
    const anchors = stepAnchors(headings, 'text\n<DeepDive>\n### Three lines\n</DeepDive>');
    expect(anchors[anchors.length - 1]).toEqual({ label: 'Deep dive', anchor: 'deep-dive' });
  });
});
