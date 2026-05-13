/**
 * D3 helpers — small utilities used by chart Svelte islands.
 * Keep the bundle small by importing only what we need.
 */
import { scaleLinear, scaleBand, max, min, extent } from 'd3';

export { scaleLinear, scaleBand, max, min, extent };

/** Map a numeric value to brick or ink based on whether it's the "winning" datum. */
export function colorForValue(value: number, isAccent: boolean): string {
  return isAccent ? '#9b4a3f' : '#1a1a1a';
}

/** Format a numeric tick: 87 → "87%", 1.4 → "1.4×", -3.4 → "-3.4pp". */
export function formatTick(value: number, unit: '%' | '×' | 'pp' | ''): string {
  return `${value.toFixed(unit === '×' ? 1 : 1)}${unit}`;
}
