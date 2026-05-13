import { describe, it, expect } from 'vitest';
import { estimateReadingTime } from './reading-time';

describe('reading-time', () => {
  it('returns 1 minute for very short text', () => {
    expect(estimateReadingTime('hello world')).toBe(1);
  });

  it('estimates ~240 words per minute for body text', () => {
    const text = Array(480).fill('word').join(' ');
    expect(estimateReadingTime(text)).toBe(2);
  });

  it('rounds up partial minutes', () => {
    const text = Array(300).fill('word').join(' ');
    expect(estimateReadingTime(text)).toBe(2);
  });

  it('strips MDX/HTML noise before counting', () => {
    const text = '<TraceViewer src="x.json" /> hello world ' + Array(700).fill('word').join(' ');
    // ~700 words / 240 wpm → 3 min
    expect(estimateReadingTime(text)).toBe(3);
  });
});
