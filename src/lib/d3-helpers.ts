/**
 * D3 helpers — small utilities used by chart Svelte islands.
 * Keep the bundle small by importing only what we need.
 */
import { scaleLinear, scaleBand, max, min, extent } from 'd3';

export { scaleLinear, scaleBand, max, min, extent };

/** Brick or ink based on whether this is the "winning" datum. */
export function colorForAccent(isAccent: boolean): string {
  return isAccent ? '#9b4a3f' : '#1a1a1a';
}

/** Format a numeric tick: 87 → "87.0%", 1.4 → "1.4×", -3.4 → "-3.4pp". */
export function formatTick(value: number, unit: '%' | '×' | 'pp' | ''): string {
  return `${value.toFixed(1)}${unit}`;
}
