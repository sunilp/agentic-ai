/**
 * Layout of the governance machine: layers bottom to top I (Foundations) to V (GenAI and agents),
 * the roof bar (step 21), the business-unit box (step 19) and the platform rail (step 20).
 * Meaning lives in governance-path.ts; this file is coordinates only.
 */
export const FRAME = { width: 880, height: 500 };
export const PART_H = 40;
export const GUTTER = 32; // vertical gap between layers
export const LABEL_CHAR_W = 7.1; // 11px mono label at 0.5px letter-spacing, measured width per character

export interface Rect { x: number; y: number; w: number; h: number }
export interface MachinePart extends Rect { n: number; row: number }

// Row 0 is the top layer (V). Row 4 is the bottom layer (I).
export const LAYERS: { y: number; name: string }[] = [
  { y: 150, name: 'V · GENAI AND AGENTS' },
  { y: 222, name: 'IV · RESPONSIBLE AI' },
  { y: 294, name: 'III · PROCESS' },
  { y: 366, name: 'II · PEOPLE' },
  { y: 438, name: 'I · FOUNDATIONS' },
];
export const ROOF_LABEL = { x: 70, y: 38, text: 'VI · SCALE' };

const ROWS: [n: number, x: number, w: number][][] = [
  [[17, 70, 390], [18, 470, 390]],
  [[12, 70, 140], [13, 220, 140], [14, 370, 170], [15, 550, 140], [16, 700, 160]],
  [[8, 70, 160], [9, 240, 220], [10, 470, 200], [11, 680, 180]],
  [[5, 70, 250], [6, 330, 270], [7, 610, 250]],
  [[1, 70, 180], [2, 260, 200], [3, 470, 180], [4, 660, 200]],
];

export const PARTS: MachinePart[] = [
  ...ROWS.flatMap((row, r) => row.map(([n, x, w]) => ({ n, x, y: LAYERS[r].y, w, h: PART_H, row: r }))),
  { n: 21, x: 70, y: 44, w: 790, h: 40, row: -2 },
  { n: 19, x: 560, y: 104, w: 300, h: 20, row: -1 },
  { n: 20, x: 14, y: 150, w: 36, h: 328, row: 99 },
];

export function partOf(n: number): MachinePart {
  const p = PARTS.find((x) => x.n === n);
  if (!p) throw new Error(`no machine part for step ${n}`);
  return p;
}

/** Boxes the layer and roof labels occupy: baseline minus 11 to baseline plus 2. */
export function labelBoxes(): Rect[] {
  const box = (x: number, baseline: number, text: string): Rect => ({ x, y: baseline - 11, w: text.length * LABEL_CHAR_W, h: 13 });
  return [box(ROOF_LABEL.x, ROOF_LABEL.y, ROOF_LABEL.text), ...LAYERS.map((l) => box(70, l.y - 6, l.name))];
}
