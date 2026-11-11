/**
 * Routes the links from a selected step to the steps it rests on, like circuit traces:
 * out of the part's edge, along the gaps between layers, and down a side channel when
 * a link spans more than one layer. Pure geometry; the static and interactive renders
 * both call it, so they can never differ. Links may cross each other in a channel
 * (the paper halo keeps that readable). They never cross a part or a label.
 */
import { GUTTER, partOf, type MachinePart } from '~/data/governance-machine';
import { stepByN } from '~/data/governance-path';

export type Pt = [number, number];
export interface RoutedLink { from: number; to: number; points: Pt[]; d: string }

const LANE_OFFSET = 5;
const LANE_STEP = 4;
const LEFT_TRUNK = 56; // lanes 56, 60, 64: between the rail (ends 50) and the stack (starts 70)
const RIGHT_TRUNK = 874; // lanes 874, 870, 866: right of the stack (ends 860)
const MID = 440;

const bottom = (p: MachinePart) => p.y + p.h;
const cx = (p: MachinePart) => p.x + p.w / 2;

export function roundedPath(points: Pt[], r = 7): string {
  let d = `M${points[0][0]} ${points[0][1]}`;
  for (let i = 1; i < points.length - 1; i++) {
    const [a, v, b] = [points[i - 1], points[i], points[i + 1]];
    const l1 = Math.hypot(v[0] - a[0], v[1] - a[1]);
    const l2 = Math.hypot(b[0] - v[0], b[1] - v[1]);
    if (l1 < 0.1 || l2 < 0.1) continue;
    const rr = Math.min(r, l1 / 2, l2 / 2);
    const p1: Pt = [v[0] - ((v[0] - a[0]) / l1) * rr, v[1] - ((v[1] - a[1]) / l1) * rr];
    const p2: Pt = [v[0] + ((b[0] - v[0]) / l2) * rr, v[1] + ((b[1] - v[1]) / l2) * rr];
    d += ` L${+p1[0].toFixed(2)} ${+p1[1].toFixed(2)} Q${v[0]} ${v[1]} ${+p2[0].toFixed(2)} ${+p2[1].toFixed(2)}`;
  }
  const e = points[points.length - 1];
  return `${d} L${e[0]} ${e[1]}`;
}

type Kind = 'same' | 'next' | 'trunk';

function kindOf(s: MachinePart, t: MachinePart): Kind {
  if (t.row === s.row) return 'same';
  if (t.y < s.y) throw new Error(`step ${s.n} rests on step ${t.n}, which sits above it`);
  return t.row === s.row + 1 ? 'next' : 'trunk';
}

export function routeLinks(selected: number): RoutedLink[] {
  const step = stepByN(selected);
  if (!step || selected === 22) return [];
  const s = partOf(selected);
  const targets = step.restsOn.map(partOf);
  const link = (t: MachinePart, points: Pt[]): RoutedLink => ({ from: s.n, to: t.n, points, d: roundedPath(points) });

  // The rail leaves its right edge in the gutter under each target; nearer targets take shallower lanes.
  if (s.n === 20) {
    const used = new Map<number, number>();
    return [...targets]
      .sort((a, b) => a.row - b.row || cx(a) - cx(b))
      .map((t) => {
        const li = (used.get(t.row) ?? -1) + 1;
        used.set(t.row, li);
        const y = bottom(t) + LANE_OFFSET + LANE_STEP * li;
        return link(t, [[s.x + s.w, y], [cx(t), y], [cx(t), bottom(t)]]);
      });
  }

  const plans = targets.map((t) => {
    const kind = kindOf(s, t);
    const side: 'left' | 'right' | undefined = kind === 'trunk' ? ((cx(s) + cx(t)) / 2 < MID ? 'left' : 'right') : undefined;
    const key = side === 'left' ? -1 : side === 'right' ? 10_000 + cx(t) : cx(t);
    return { t, kind, side, key };
  });
  plans.sort((a, b) => a.key - b.key);

  const ports = plans.map((_, i) => s.x + (s.w * (i + 1)) / (plans.length + 1));
  // Left-going links take lanes left to right and right-going links right to left,
  // so no horizontal run passes under a sibling's port.
  const goesLeft = plans.map((p, i) => (p.kind === 'trunk' ? p.side === 'left' : cx(p.t) <= ports[i]));
  const lane: number[] = [];
  let nl = 0;
  plans.forEach((_, i) => { if (goesLeft[i]) lane[i] = nl++; });
  let nr = 0;
  for (let i = plans.length - 1; i >= 0; i--) if (!goesLeft[i]) lane[i] = nr++;
  // The first link to reach a trunk takes its outermost lane.
  const trunkX: number[] = [];
  let tl = 0;
  plans.forEach((p, i) => { if (p.side === 'left') trunkX[i] = LEFT_TRUNK + LANE_STEP * tl++; });
  let tr = 0;
  for (let i = plans.length - 1; i >= 0; i--) if (plans[i].side === 'right') trunkX[i] = RIGHT_TRUNK - LANE_STEP * tr++;

  return plans.map((p, i) => {
    const { t } = p;
    const port = +ports[i].toFixed(2);
    const tx = cx(t);
    const y1 = bottom(s) + LANE_OFFSET + LANE_STEP * lane[i];
    if (p.kind === 'same') return link(t, [[port, bottom(s)], [port, y1], [tx, y1], [tx, bottom(t)]]);
    if (p.kind === 'next') return link(t, [[port, bottom(s)], [port, y1], [tx, y1], [tx, t.y]]);
    const y2 = t.y - GUTTER + LANE_OFFSET + LANE_STEP * lane[i];
    return link(t, [[port, bottom(s)], [port, y1], [trunkX[i], y1], [trunkX[i], y2], [tx, y2], [tx, t.y]]);
  });
}
