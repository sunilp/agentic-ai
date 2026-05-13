import { describe, it, expect } from 'vitest';
import { buildReverseIndex, getReverseLinks } from './cross-links';

describe('cross-links', () => {
  it('builds reverse index from references', () => {
    const entries = [
      { id: 'ch-04', collection: 'chapters', references: ['fn-001', 'r-001'] },
      { id: 'fn-001', collection: 'fieldNotes', references: ['ch-04', 'ch-07'] },
    ];
    const idx = buildReverseIndex(entries);
    expect(idx['fn-001']?.referencedBy).toContainEqual({ id: 'ch-04', collection: 'chapters' });
    expect(idx['ch-04']?.referencedBy).toContainEqual({ id: 'fn-001', collection: 'fieldNotes' });
    expect(idx['ch-07']?.referencedBy).toContainEqual({ id: 'fn-001', collection: 'fieldNotes' });
  });

  it('returns empty arrays for unknown ids', () => {
    const idx = buildReverseIndex([]);
    const links = getReverseLinks(idx, 'unknown');
    expect(links.referencedBy).toEqual([]);
    expect(links.citedBy).toEqual([]);
    expect(links.mentionedIn).toEqual([]);
  });

  it('handles entries without references', () => {
    const entries = [{ id: 'ch-04', collection: 'chapters' }];
    const idx = buildReverseIndex(entries);
    expect(idx['ch-04']).toBeUndefined();
  });

  it('preserves collection origin in reverse lookup for cites and patterns', () => {
    const entries = [
      { id: 'lab-001', collection: 'labs', references: ['ch-04'], cites: ['evidence-eval-baseline'], patterns: ['hub-and-spoke'] },
    ];
    const idx = buildReverseIndex(entries);
    expect(idx['ch-04']?.referencedBy).toEqual([{ id: 'lab-001', collection: 'labs' }]);
    expect(idx['evidence-eval-baseline']?.citedBy).toEqual([{ id: 'lab-001', collection: 'labs' }]);
    expect(idx['hub-and-spoke']?.mentionedIn).toEqual([{ id: 'lab-001', collection: 'labs' }]);
  });
});
