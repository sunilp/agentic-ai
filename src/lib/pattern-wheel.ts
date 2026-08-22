/**
 * Pattern Wheel geometry — placement logic for the periodic-table-style
 * catalogue visualisation at /patterns/. Position encodes use: RINGS are
 * lifecycle stage, design innermost to govern outermost. SECTORS are
 * architectural layer: capability, control, evidence. Every entry sits in
 * its (layer, primaryStage) cell.
 *
 * Kept as plain, renderer-free functions (no Svelte, no DOM) so placement
 * can be asserted by a test without mounting the component. See
 * PatternWheel.svelte for the rendering that consumes this module.
 *
 * Anti-pattern placement decision: each anti-pattern is placed at its OWN
 * (layer, primaryStage) cell, the same cell a plain data-driven placement
 * would give it, NOT at its `replacedBy` target's cell. Three of the five
 * anti-patterns already share a cell with their replacedBy target
 * (workflow-in-an-agent-costume, silent-fail-open, the-uncalibrated-ensemble),
 * so this only makes a visible difference for two: hallucinated-done and
 * rubber-stamp-verifier, both tagged evidence/evaluate, whose replacedBy
 * (verifier-loop) is control/build. Moving those two would relabel their
 * layer away from what the data says and would break the exact distribution
 * the wheel was specified against (evidence/evaluate would read 2 instead of
 * 4, control/build 6 instead of 4). The trap-beside-its-escape relationship
 * is instead surfaced through the click interaction: selecting an
 * anti-pattern draws a chord to its replacedBy target (and selecting a
 * pattern draws chords back to every anti-pattern it replaces), which reads
 * as a genuine "here is the trap, here is the way out" connection rather
 * than a silent relabelling.
 */
import { ENTRIES, type Entry, type Layer, type Stage } from '~/data/pattern-language';

export const SECTORS: readonly Layer[] = ['capability', 'control', 'evidence'];
export const RINGS: readonly Stage[] = ['design', 'build', 'evaluate', 'operate', 'govern'];

export interface WheelGeometry {
  cx: number;
  cy: number;
  innerRadius: number;
  ringWidth: number;
  outerRadius: number;
  sectorPadDeg: number;
}

/** 880-wide viewBox, matching the 26 existing pattern diagrams. */
export const VIEWBOX = { width: 880, height: 860 };

export const GEOMETRY: WheelGeometry = {
  cx: 460,
  cy: 470,
  innerRadius: 72,
  ringWidth: 58,
  outerRadius: 72 + 58 * 5, // 362
  sectorPadDeg: 10,
};

export interface PlacedEntry {
  slug: string;
  name: string;
  kind: Entry['kind'];
  layer: Layer;
  primaryStage: Stage;
  alsoStages: Stage[];
  oneLine: string;
  status: Entry['status'];
  related: string[];
  replacedBy?: string;
  /** Stable 1-based legend key: sector order, then ring order, then alphabetical within the cell. */
  key: number;
  sectorIndex: number;
  ringIndex: number;
  indexInCell: number;
  cellCount: number;
  /** Degrees, 0 = due east, increasing clockwise (SVG y grows downward). */
  angleDeg: number;
  radius: number;
  x: number;
  y: number;
}

/** Sector angular bounds in degrees. Sector 0 starts at due east (0deg) so a
 *  sector boundary lands exactly on the horizontal ruler the ring labels use. */
export function sectorBounds(sectorIndex: number): { start: number; end: number } {
  const start = sectorIndex * 120;
  return { start, end: start + 120 };
}

export function ringBounds(ringIndex: number, geo: WheelGeometry = GEOMETRY): { inner: number; outer: number } {
  return {
    inner: geo.innerRadius + geo.ringWidth * ringIndex,
    outer: geo.innerRadius + geo.ringWidth * (ringIndex + 1),
  };
}

export function ringMidRadius(ringIndex: number, geo: WheelGeometry = GEOMETRY): number {
  const { inner, outer } = ringBounds(ringIndex, geo);
  return (inner + outer) / 2;
}

function polarToXY(cx: number, cy: number, radius: number, angleDeg: number): { x: number; y: number } {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + radius * Math.cos(rad), y: cy + radius * Math.sin(rad) };
}

function cellKey(layer: Layer, stage: Stage): string {
  return `${layer}:${stage}`;
}

/**
 * Places every entry in exactly one (layer, primaryStage) cell and computes
 * its on-wheel coordinates. Deterministic: entries within a cell are ordered
 * alphabetically by name, matching byLayer/byStage elsewhere in the
 * catalogue, so the layout and the numbered legend key are stable.
 */
export function placeEntries(entries: readonly Entry[] = ENTRIES, geo: WheelGeometry = GEOMETRY): PlacedEntry[] {
  const cells = new Map<string, Entry[]>();
  for (const e of entries) {
    const k = cellKey(e.layer, e.primaryStage);
    const list = cells.get(k);
    if (list) list.push(e);
    else cells.set(k, [e]);
  }
  for (const list of cells.values()) list.sort((a, b) => a.name.localeCompare(b.name));

  // Stable legend key: sector order, then ring order, then alpha within the cell.
  const ordered: Entry[] = [];
  for (const sector of SECTORS) {
    for (const stage of RINGS) {
      ordered.push(...(cells.get(cellKey(sector, stage)) ?? []));
    }
  }
  const keyOf = new Map(ordered.map((e, i) => [e.slug, i + 1]));

  const placed: PlacedEntry[] = [];
  SECTORS.forEach((sector, sectorIndex) => {
    const { start } = sectorBounds(sectorIndex);
    const usableStart = start + geo.sectorPadDeg;
    const usableWidth = 120 - geo.sectorPadDeg * 2;

    RINGS.forEach((stage, ringIndex) => {
      const list = cells.get(cellKey(sector, stage)) ?? [];
      const n = list.length;
      const radius = ringMidRadius(ringIndex, geo);

      list.forEach((e, i) => {
        const angleDeg = n === 1 ? start + 60 : usableStart + ((i + 0.5) / n) * usableWidth;
        const { x, y } = polarToXY(geo.cx, geo.cy, radius, angleDeg);
        placed.push({
          slug: e.slug,
          name: e.name,
          kind: e.kind,
          layer: e.layer,
          primaryStage: e.primaryStage,
          alsoStages: e.alsoStages ?? [],
          oneLine: e.oneLine,
          status: e.status,
          related: e.related ?? [],
          replacedBy: e.replacedBy,
          key: keyOf.get(e.slug)!,
          sectorIndex,
          ringIndex,
          indexInCell: i,
          cellCount: n,
          angleDeg,
          radius,
          x,
          y,
        });
      });
    });
  });

  return placed;
}

/** (layer, primaryStage) distribution. Five of fifteen cells are legitimately
 *  empty: capability has nothing past build, control has nothing at evaluate,
 *  evidence has nothing at design. */
export function cellCounts(entries: readonly Entry[] = ENTRIES): Record<Layer, Record<Stage, number>> {
  const out = {} as Record<Layer, Record<Stage, number>>;
  for (const l of SECTORS) out[l] = { design: 0, build: 0, evaluate: 0, operate: 0, govern: 0 };
  for (const e of entries) out[e.layer][e.primaryStage] += 1;
  return out;
}

/** Reverse index: pattern slug -> anti-pattern slugs whose replacedBy names it. */
export function replacesIndex(entries: readonly Entry[] = ENTRIES): Map<string, string[]> {
  const map = new Map<string, string[]>();
  for (const e of entries) {
    if (e.kind !== 'anti-pattern' || !e.replacedBy) continue;
    const list = map.get(e.replacedBy);
    if (list) list.push(e.slug);
    else map.set(e.replacedBy, [e.slug]);
  }
  return map;
}
