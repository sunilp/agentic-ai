/**
 * Estimate reading time in minutes. ~240 words per minute for English non-fiction.
 * Strips HTML/MDX tags before counting.
 */
export function estimateReadingTime(text: string): number {
  const stripped = text.replace(/<[^>]+>/g, ' ');
  const words = stripped.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.ceil(words / 240));
}
