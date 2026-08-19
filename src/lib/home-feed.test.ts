import { describe, it, expect } from 'vitest';
import { buildHomeFeed, formatFeedDate, type FeedItem } from './home-feed';

const d = (s: string) => new Date(s);

const streams = {
  fieldNotes: [
    { id: 'fn-004', title: 'FN four', dek: 'dek 4', banner: '/b/fn-004.png', spot: '/s/fn-004.png', date: d('2026-06-25'), readingTime: 9 },
    { id: 'fn-003', title: 'FN three', dek: 'dek 3', banner: '/b/fn-003.png', spot: '/s/fn-003.png', date: d('2026-05-23'), readingTime: 7 },
  ],
  signal: [
    { id: 'sg-004', title: 'Signal four', dek: 'dek s4', banner: '/b/sg-004.png', date: d('2026-08-14'), readingTime: 11 },
    { id: 'sg-003', title: 'Signal three', dek: 'dek s3', banner: '/b/sg-003.png', date: d('2026-06-07'), readingTime: 8 },
  ],
  recipes: [
    { id: 'r-001', title: 'Recipe one', description: 'desc r1', spot: '/s/r-001.png', verifiedOn: d('2026-05-13'), estimatedMinutes: 45 },
  ],
  labs: [
    { id: 'lab-002', title: 'Lab two', description: 'desc l2', spot: '/s/lab-002.png', date: d('2026-07-03'), readingTime: 12 },
  ],
  architecture: [
    { id: 'arch-002', title: 'Arch two', dek: 'dek a2', order: 2, updated: d('2026-08-18'), readingTime: 14, status: 'published' as const },
    { id: 'arch-001', title: 'Arch one', dek: 'dek a1', order: 1, updated: d('2026-08-18'), readingTime: 13, status: 'published' as const },
    { id: 'arch-009', title: 'Arch draft', dek: 'draft', order: 9, updated: d('2026-08-19'), readingTime: 1, status: 'draft' as const },
  ],
};

describe('buildHomeFeed', () => {
  it('features the newest editorial piece; a newer blueprint is never featured', () => {
    const { featured } = buildHomeFeed(streams);
    expect(featured!.id).toBe('sg-004');
    expect(featured!.stream).toBe('Signal');
    expect(featured!.href).toBe('/signal/sg-004/');
    expect(featured!.banner).toBe('/b/sg-004.png');
  });

  it('orders the rest by date descending and respects the limit', () => {
    const { rest } = buildHomeFeed(streams, { limit: 3 });
    expect(rest.map((i) => i.id)).toEqual(['arch-001', 'lab-002', 'fn-004']);
  });

  it('caps blueprints to one entry, picking lowest order on equal dates, and drops drafts', () => {
    const { featured, rest } = buildHomeFeed(streams, { limit: 10 });
    const all = [featured!, ...rest];
    const arch = all.filter((i) => i.stream === 'Blueprint');
    expect(arch.map((i) => i.id)).toEqual(['arch-001']);
    expect(all.find((i) => i.id === 'arch-009')).toBeUndefined();
  });

  it('labels dates by stream semantics', () => {
    const { featured, rest } = buildHomeFeed(streams, { limit: 10 });
    const all = [featured!, ...rest];
    const byId = (id: string) => all.find((i) => i.id === id) as FeedItem;
    expect(byId('sg-004').dateLabel).toBe('');
    expect(byId('arch-001').dateLabel).toBe('Updated');
    expect(byId('r-001').dateLabel).toBe('Verified');
  });

  it('builds hrefs and rubrics per stream', () => {
    const { featured, rest } = buildHomeFeed(streams, { limit: 10 });
    const all = [featured!, ...rest];
    const byId = (id: string) => all.find((i) => i.id === id) as FeedItem;
    expect(byId('fn-004').href).toBe('/field-notes/fn-004/');
    expect(byId('fn-004').rubric).toBe('FN-004 · Field Note');
    expect(byId('r-001').href).toBe('/recipes/r-001/');
    expect(byId('r-001').dek).toBe('desc r1');
    expect(byId('lab-002').href).toBe('/labs/lab-002/');
    expect(byId('arch-001').href).toBe('/architecture/arch-001/');
    expect(byId('arch-001').rubric).toBe('ARCH-001 · Blueprint');
  });

  it('uses the entry slug for hrefs when it differs from the frontmatter id', () => {
    const s = { ...streams, labs: [{ ...streams.labs[0], slug: 'incident-triage-durable-agent' }] };
    const { rest } = buildHomeFeed(s, { limit: 10 });
    expect(rest.find((i) => i.id === 'lab-002')?.href).toBe('/labs/incident-triage-durable-agent/');
  });

  it('returns no featured item when only blueprints exist', () => {
    const { featured, rest } = buildHomeFeed({ fieldNotes: [], signal: [], recipes: [], labs: [], architecture: streams.architecture });
    expect(featured).toBeUndefined();
    expect(rest.map((i) => i.id)).toEqual(['arch-001']);
  });

  it('handles empty streams', () => {
    const { featured, rest } = buildHomeFeed({ fieldNotes: [], signal: [], recipes: [], labs: [], architecture: [] });
    expect(featured).toBeUndefined();
    expect(rest).toEqual([]);
  });
});

describe('formatFeedDate', () => {
  it('omits the year when it matches the reference year', () => {
    expect(formatFeedDate(d('2026-08-14'), d('2026-08-19'))).toBe('Aug 14');
  });
  it('includes the year otherwise', () => {
    expect(formatFeedDate(d('2025-12-02'), d('2026-08-19'))).toBe('Dec 2, 2025');
  });
});
