/** Data for the machine's side panel: rests on, holds up, patterns in play. */
import { stepByN, holdsUp, stepHref } from '~/data/governance-path';
import { bySlug, type Layer } from '~/data/pattern-language';

export const LAYER_COLOUR: Record<Layer, string> = { capability: '#205599', control: '#9b4a3f', evidence: '#b08d20' };

export interface PanelRef { n: number; short: string; href: string | null }
export interface PanelPattern { slug: string; name: string; layer: Layer; anti: boolean; colour: string; href: string }
export interface Panel { n: number; title: string; href: string | null; restsOn: PanelRef[]; holdsUp: PanelRef[]; patterns: PanelPattern[] }

export function panelFor(n: number, written: ReadonlySet<string>): Panel {
  const s = stepByN(n);
  if (!s) throw new Error(`no step ${n}`);
  const ref = (k: number): PanelRef => {
    const t = stepByN(k)!;
    return { n: k, short: t.short, href: written.has(t.slug) ? stepHref(t) : null };
  };
  return {
    n,
    title: s.title,
    href: written.has(s.slug) ? stepHref(s) : null,
    restsOn: n === 22 ? [] : s.restsOn.map(ref),
    holdsUp: holdsUp(n).map(ref),
    patterns: s.patterns.map((slug) => {
      const e = bySlug(slug);
      if (!e) throw new Error(`unknown pattern ${slug}`);
      return { slug, name: e.name, layer: e.layer, anti: e.kind === 'anti-pattern', colour: LAYER_COLOUR[e.layer], href: `/patterns/${slug}/` };
    }),
  };
}
