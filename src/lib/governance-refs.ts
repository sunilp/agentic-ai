import type { Ref } from '~/data/governance-figures';

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');

/** SVG <tspan> runs for a list of step references; a written step becomes a link. */
export function renderRefs(refs: Ref[], href: (n: number) => string | null): string {
  return refs
    .map((r) => {
      if (typeof r === 'string') return `<tspan>${esc(r)}</tspan>`;
      const h = href(r);
      return h ? `<a href="${esc(h)}"><tspan class="ref ref--link">${r}</tspan></a>` : `<tspan class="ref">${r}</tspan>`;
    })
    .join('');
}
