/**
 * The governance machine as an SVG string. One function for both renders:
 * static on step pages ('progress': earlier steps built, later steps faded) and
 * interactive on the hub ('explore': unrelated steps faded).
 */
import { FRAME, LAYERS, PARTS, ROOF_LABEL } from '~/data/governance-machine';
import { stepByN, holdsUp } from '~/data/governance-path';
import { routeLinks } from './machine-routing';

export type MachineMode = 'explore' | 'progress';
export type PartState = 'selected' | 'restsOn' | 'holdsUp' | 'built' | 'future' | 'idle' | 'faded';

export interface MachineSvgOptions {
  selected: number | null;
  mode: MachineMode;
  /** Link for a part, or null when its step has no page yet. */
  href?: (n: number) => string | null;
  /** Parts become buttons for the hub island instead of links. */
  interactive?: boolean;
  title?: string;
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');

export function partState(n: number, selected: number | null, mode: MachineMode): PartState {
  if (selected === null) return 'idle';
  if (n === selected) return 'selected';
  if (stepByN(selected)?.restsOn.includes(n)) return 'restsOn';
  if (holdsUp(selected).includes(n)) return 'holdsUp';
  if (mode === 'progress') return n < selected ? 'built' : 'future';
  return 'faded';
}

export function machineLabel(n: number): string {
  if (n === 20) return '20  PLATFORM · BUILT INTO EVERY LAYER';
  const s = stepByN(n);
  if (!s) throw new Error(`no step ${n}`);
  return `${n}  ${s.short}`;
}

export function renderMachineSvg(o: MachineSvgOptions): string {
  const title = o.title ?? 'The governance machine: every step of the guide as one part of a layered structure.';
  const out: string[] = [
    `<svg class="machine" viewBox="0 0 ${FRAME.width} ${FRAME.height}" role="group" aria-label="${esc(title)}">`,
    `<text class="machine__layer" x="${ROOF_LABEL.x}" y="${ROOF_LABEL.y}">${ROOF_LABEL.text}</text>`,
    ...LAYERS.map((l) => `<text class="machine__layer" x="70" y="${l.y - 6}">${l.name}</text>`),
  ];

  for (const p of PARTS) {
    const step = stepByN(p.n)!;
    const state = partState(p.n, o.selected, o.mode);
    const label = esc(machineLabel(p.n));
    const rx = p.x + p.w / 2 + 4;
    const ry = p.y + p.h - 14;
    const text = p.n === 20
      ? `<text class="machine__label" x="${rx}" y="${ry}" transform="rotate(-90 ${rx} ${ry})">${label}</text>`
      : `<text class="machine__label" x="${p.x + 10}" y="${p.y + (p.h > 30 ? 25 : 15)}">${label}</text>`;
    const shape = `<rect class="machine__part" x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}"/>`;
    const name = esc(`Step ${p.n}: ${step.title}`);
    const attrs = `class="machine__node is-${state}" data-step="${p.n}"`;
    const href = o.href?.(p.n) ?? null;
    if (o.interactive) {
      out.push(`<g ${attrs} tabindex="0" role="button" aria-label="${name}" aria-pressed="${state === 'selected'}">${shape}${text}</g>`);
    } else if (href) {
      out.push(`<a ${attrs} href="${esc(href)}" aria-label="${name}">${shape}${text}</a>`);
    } else {
      out.push(`<g ${attrs} aria-label="${name}">${shape}${text}</g>`);
    }
  }

  if (o.selected !== null) {
    routeLinks(o.selected).forEach((l, i) => {
      const [sx, sy] = l.points[0];
      const [ex, ey] = l.points[l.points.length - 1];
      out.push(`<path class="machine__halo" d="${l.d}"/>`);
      out.push(`<path class="machine__link" d="${l.d}" pathLength="1" style="animation-delay:${(i * 0.12).toFixed(2)}s"/>`);
      out.push(`<circle class="machine__port" cx="${sx}" cy="${sy}" r="2.2"/>`);
      out.push(`<circle class="machine__end" cx="${ex}" cy="${ey}" r="3"/>`);
    });
  }

  out.push('</svg>');
  return out.join('');
}
