<script lang="ts">
  /**
   * PatternWheel — the periodic-table view of the pattern language catalogue.
   * Position encodes use: rings are lifecycle stage (design innermost to
   * govern outermost), sectors are architectural layer (capability, control,
   * evidence). Every mark's cell comes straight from src/lib/pattern-wheel.ts,
   * which does the placement and is unit-tested on its own. Svelte 5 runes.
   *
   * Static-first: everything below renders from plain data at build time.
   * Hovering, selecting (chords + dimming) and keyboard nav are progressive
   * enhancement layered on top once client:visible hydrates the island. This
   * component no longer carries its own 26-row legend: the "by layer" list
   * in src/pages/patterns/index.astro, rendered directly below the wheel, is
   * the keyed catalogue now, and its list items repeat each mark's numeral so
   * the two stay cross-referenced in both directions.
   */
  import { ENTRIES, type Entry } from '~/data/pattern-language';
  import {
    placeEntries,
    replacesIndex,
    SECTORS,
    RINGS,
    GEOMETRY,
    VIEWBOX,
    sectorBounds,
    ringBounds,
    ringMidRadius,
    type PlacedEntry,
  } from '~/lib/pattern-wheel';

  interface Props {
    essaySlugs?: string[];
  }
  let { essaySlugs = [] }: Props = $props();

  const MARK_R = 9.5;

  // Colour encodes layer, one hue per sector. Selection/hover use an ink halo
  // instead of hue, since brick is now control's colour, not a state marker.
  // All three re-validated all-pairs (every sector touches every other on a
  // wheel, so every pair must clear the floor, not just an adjacent-pair
  // sampling): worst-case CVD deltaE 15.4 protanopia vs an 8 target, 16.3
  // tritan, 19.1 normal vision, chroma above floor, all >=3:1 on the surface.
  const LAYER_COLOR: Record<string, string> = {
    capability: '#205599',
    control: '#9b4a3f',
    evidence: '#b08d20',
  };

  // Numeral colour is derived per layer, not set once globally: gold is much
  // lighter than blue and brick, so the light numeral that reads on those two
  // goes muddy on gold (measured ~2.57:1). Ink on gold measures ~5.53:1; light
  // on blue and brick measure ~6.08:1 and ~4.98:1. All three clear 4.5:1.
  const NUMERAL_LIGHT = '#e8e8e8';
  const NUMERAL_INK = '#1a1a1a';
  const NUMERAL_COLOR: Record<string, string> = {
    capability: NUMERAL_LIGHT,
    control: NUMERAL_LIGHT,
    evidence: NUMERAL_INK,
  };

  // Layout is fixed at build time: same 26 entries every render, so this is a
  // plain const, not reactive state.
  const placed: PlacedEntry[] = placeEntries();
  const bySlugMap = new Map(placed.map((p) => [p.slug, p]));
  const replaces = replacesIndex(ENTRIES as Entry[]);

  const ringBoundaryRadii: number[] = [
    ringBounds(0).inner,
    ...RINGS.map((_, i) => ringBounds(i).outer),
  ];

  function polarToXY(radius: number, angleDeg: number): { x: number; y: number } {
    const rad = (angleDeg * Math.PI) / 180;
    return { x: GEOMETRY.cx + radius * Math.cos(rad), y: GEOMETRY.cy + radius * Math.sin(rad) };
  }

  const sectorDividerLines = SECTORS.map((sector, i) => {
    const { start } = sectorBounds(i);
    const inner = polarToXY(GEOMETRY.innerRadius, start);
    const outer = polarToXY(GEOMETRY.outerRadius, start);
    return { key: sector, x1: inner.x, y1: inner.y, x2: outer.x, y2: outer.y };
  });

  // Ring labels sit along the single horizontal ruler at the sector-0/sector-2
  // boundary (due east, angle 0), which SECTOR_PAD keeps clear of every mark.
  const ringRulerLabels = RINGS.map((stage, i) => {
    const { x, y } = polarToXY(ringMidRadius(i), 0);
    return { stage, x, y, halfW: stage.length * 3.6 + 8 };
  });

  const sectorLabels = SECTORS.map((layer, i) => {
    const { start, end } = sectorBounds(i);
    const { x, y } = polarToXY(GEOMETRY.outerRadius + 30, (start + end) / 2);
    return { layer, x, y, halfW: layer.length * 3.8 + 10 };
  });

  function diamondPath(x: number, y: number, r: number): string {
    return `M ${x} ${y - r} L ${x + r} ${y} L ${x} ${y + r} L ${x - r} ${y} Z`;
  }

  let hoveredSlug = $state<string | null>(null);
  let selectedSlug = $state<string | null>(null);

  const activeSlug = $derived(hoveredSlug ?? selectedSlug);
  const activeEntry = $derived(activeSlug ? (bySlugMap.get(activeSlug) ?? null) : null);
  const essaySet = $derived(new Set(essaySlugs));

  const neighborSlugs = $derived.by(() => {
    const set = new Set<string>();
    if (!selectedSlug) return set;
    const entry = bySlugMap.get(selectedSlug);
    if (!entry) return set;
    for (const r of entry.related) set.add(r);
    if (entry.kind === 'anti-pattern' && entry.replacedBy) set.add(entry.replacedBy);
    for (const antiSlug of replaces.get(selectedSlug) ?? []) set.add(antiSlug);
    return set;
  });

  interface Chord {
    key: string;
    fromX: number;
    fromY: number;
    toX: number;
    toY: number;
    kind: 'related' | 'escape';
    layer: string;
  }

  const chords = $derived.by((): Chord[] => {
    if (!selectedSlug) return [];
    const entry = bySlugMap.get(selectedSlug);
    if (!entry) return [];
    const layer = entry.layer;
    const list: Chord[] = [];
    for (const r of entry.related) {
      const target = bySlugMap.get(r);
      if (!target) continue;
      list.push({ key: `${entry.slug}->${r}`, fromX: entry.x, fromY: entry.y, toX: target.x, toY: target.y, kind: 'related', layer });
    }
    if (entry.kind === 'anti-pattern' && entry.replacedBy) {
      const target = bySlugMap.get(entry.replacedBy);
      if (target) {
        list.push({ key: `${entry.slug}->${entry.replacedBy}`, fromX: entry.x, fromY: entry.y, toX: target.x, toY: target.y, kind: 'escape', layer });
      }
    }
    for (const antiSlug of replaces.get(entry.slug) ?? []) {
      const anti = bySlugMap.get(antiSlug);
      if (!anti) continue;
      list.push({ key: `${antiSlug}->${entry.slug}`, fromX: anti.x, fromY: anti.y, toX: entry.x, toY: entry.y, kind: 'escape', layer });
    }
    return list;
  });

  function isDimmed(slug: string): boolean {
    if (!selectedSlug || slug === selectedSlug) return false;
    return !neighborSlugs.has(slug);
  }

  function toggleSelect(slug: string) {
    selectedSlug = selectedSlug === slug ? null : slug;
  }

  function clearSelection() {
    selectedSlug = null;
  }

  function onMarkKeydown(e: KeyboardEvent, slug: string) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      toggleSelect(slug);
    } else if (e.key === 'Escape') {
      hoveredSlug = null;
      selectedSlug = null;
    }
  }

  $effect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        hoveredSlug = null;
        selectedSlug = null;
      }
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  });
</script>

<div
  class="wheel"
  style={`--layer-capability: ${LAYER_COLOR.capability}; --layer-control: ${LAYER_COLOR.control}; --layer-evidence: ${LAYER_COLOR.evidence}; --numeral-capability: ${NUMERAL_COLOR.capability}; --numeral-control: ${NUMERAL_COLOR.control}; --numeral-evidence: ${NUMERAL_COLOR.evidence};`}
>
  <header class="wheel__header">
    <h2 class="wheel__title">The Pattern Wheel</h2>
    <p class="wheel__dek">
      Position encodes use. Rings are lifecycle stage, design innermost to govern outermost. Sectors are architectural
      layer: capability, control, evidence. Hover a mark for its name. Click one to trace what it connects to.
    </p>
  </header>

  <div class="wheel__hero">
  <div class="wheel__figure-wrap">
    <svg
      viewBox={`0 0 ${VIEWBOX.width} ${VIEWBOX.height}`}
      class="wheel__svg"
      role="group"
      aria-label="Pattern wheel. Twenty-six patterns and anti-patterns placed by architectural layer and lifecycle stage. Every numeral is also listed, by layer, in the catalogue below."
    >
      <title>The Pattern Wheel</title>
      <desc>
        Five lifecycle-stage rings, design innermost through build, evaluate, operate, to govern outermost, crossed
        with three layer sectors: capability, control and evidence. Twenty-six entries, each placed once, in the cell
        matching what it is for and when it applies.
      </desc>

      <rect x="0" y="0" width={VIEWBOX.width} height={VIEWBOX.height} class="wheel__bg" onclick={clearSelection} />

      {#each ringBoundaryRadii as r, i (r)}
        <circle
          cx={GEOMETRY.cx}
          cy={GEOMETRY.cy}
          r={r}
          class="wheel__ring-line"
          class:wheel__ring-line--edge={i === 0 || i === ringBoundaryRadii.length - 1}
        />
      {/each}

      {#each sectorDividerLines as line (line.key)}
        <line x1={line.x1} y1={line.y1} x2={line.x2} y2={line.y2} class="wheel__sector-line" />
      {/each}

      {#each chords as c (c.key)}
        <path
          d={`M ${c.fromX} ${c.fromY} Q ${GEOMETRY.cx} ${GEOMETRY.cy} ${c.toX} ${c.toY}`}
          class={`wheel__chord wheel__chord--${c.layer}`}
          class:wheel__chord--escape={c.kind === 'escape'}
        />
      {/each}

      {#each ringRulerLabels as l (l.stage)}
        <rect x={l.x - l.halfW} y={l.y - 9} width={l.halfW * 2} height="14" class="wheel__label-halo" />
        <text x={l.x} y={l.y + 3} text-anchor="middle" class="wheel__ring-label">{l.stage}</text>
      {/each}

      {#each sectorLabels as l (l.layer)}
        <rect x={l.x - l.halfW} y={l.y - 10} width={l.halfW * 2} height="18" class="wheel__label-halo" />
        <text x={l.x} y={l.y + 4} text-anchor="middle" class="wheel__sector-label">{l.layer}</text>
      {/each}

      {#each placed as p (p.slug)}
        <g
          class={`wheel__mark wheel__mark--${p.layer}`}
          class:wheel__mark--anti={p.kind === 'anti-pattern'}
          class:wheel__mark--selected={selectedSlug === p.slug}
          class:wheel__mark--hovered={hoveredSlug === p.slug && selectedSlug !== p.slug}
          class:wheel__mark--dimmed={isDimmed(p.slug)}
          tabindex="0"
          role="button"
          aria-pressed={selectedSlug === p.slug}
          aria-label={`${p.name}. ${p.kind === 'anti-pattern' ? 'Anti-pattern' : 'Pattern'}, ${p.layer} layer, ${p.primaryStage} stage. ${p.oneLine}`}
          onmouseenter={() => (hoveredSlug = p.slug)}
          onmouseleave={() => (hoveredSlug = null)}
          onfocus={() => (hoveredSlug = p.slug)}
          onblur={() => (hoveredSlug = null)}
          onclick={() => toggleSelect(p.slug)}
          onkeydown={(e) => onMarkKeydown(e, p.slug)}
        >
          {#if selectedSlug === p.slug}
            {#if p.kind === 'anti-pattern'}
              <path d={diamondPath(p.x, p.y, MARK_R + 4.5)} class="wheel__mark-halo wheel__mark-halo--selected" />
            {:else}
              <circle cx={p.x} cy={p.y} r={MARK_R + 4.5} class="wheel__mark-halo wheel__mark-halo--selected" />
            {/if}
          {:else if hoveredSlug === p.slug}
            {#if p.kind === 'anti-pattern'}
              <path d={diamondPath(p.x, p.y, MARK_R + 3)} class="wheel__mark-halo wheel__mark-halo--hover" />
            {:else}
              <circle cx={p.x} cy={p.y} r={MARK_R + 3} class="wheel__mark-halo wheel__mark-halo--hover" />
            {/if}
          {/if}
          {#if p.kind === 'anti-pattern'}
            <path d={diamondPath(p.x, p.y, MARK_R)} class="wheel__mark-shape" />
          {:else}
            <circle cx={p.x} cy={p.y} r={MARK_R} class="wheel__mark-shape" />
          {/if}
          <text x={p.x} y={p.y + 3} text-anchor="middle" class="wheel__mark-key">{String(p.key).padStart(2, '0')}</text>
        </g>
      {/each}
    </svg>
  </div>

  <div class="wheel__detail" aria-live="polite">
    {#if activeEntry}
      <div class="wheel__detail-head">
        <span class={`wheel__legend-swatch wheel__legend-swatch--${activeEntry.layer}`} aria-hidden="true"></span>
        <span class="wheel__detail-cell">{activeEntry.layer} &middot; {activeEntry.primaryStage}</span>
        {#if activeEntry.kind === 'anti-pattern'}<span class="wheel__detail-tag">anti-pattern</span>{/if}
      </div>
      <h3 class="wheel__detail-name">{activeEntry.name}</h3>
      <p class="wheel__detail-line">{activeEntry.oneLine}</p>
      {#if activeEntry.alsoStages.length > 0}
        <p class="wheel__detail-also">Also relevant at: {activeEntry.alsoStages.join(', ')}</p>
      {/if}
      {#if activeEntry.replacedBy}
        <p class="wheel__detail-also">
          Replaced by <strong>{bySlugMap.get(activeEntry.replacedBy)?.name ?? activeEntry.replacedBy}</strong>
        </p>
      {/if}
      {#if (replaces.get(activeEntry.slug) ?? []).length > 0}
        <p class="wheel__detail-also">
          Escapes: {(replaces.get(activeEntry.slug) ?? []).map((s) => bySlugMap.get(s)?.name ?? s).join(', ')}
        </p>
      {/if}
      {#if essaySet.has(activeEntry.slug)}
        <a class="wheel__detail-link" href={`/patterns/${activeEntry.slug}/`}>Read the essay &rarr;</a>
      {:else}
        <span class="wheel__detail-unwritten">Essay not yet written</span>
      {/if}
    {:else}
      <div class="wheel__detail-legend">
        {#each SECTORS as sector (sector)}
          <span class="wheel__detail-legend-item">
            <span class={`wheel__legend-swatch wheel__legend-swatch--${sector}`} aria-hidden="true"></span>
            {sector}
          </span>
        {/each}
      </div>
      <p class="wheel__detail-empty">Select a pattern. Hover a mark for its name, click to see what it connects to.</p>
    {/if}
  </div>
  </div>

  <p class="wheel__note">
    Five of fifteen cells are empty, and that is deliberate. Capability's work is all up front, so it has nothing at
    evaluate, operate or govern. Control acts rather than measures, so it has nothing at evaluate. Evidence does not
    exist before something is built, so it has nothing at design.
  </p>
</div>

<style>
  .wheel {
    margin: var(--space-6, 32px) 0 var(--space-7, 48px);
  }

  /* Same idiom as .pat-group__header / .arch-layer__header below and on the
     architecture index: a 2px brick rule under the header ties the wheel's
     own heading to the rest of the page's section headers, so the wheel and
     its detail panel read as one composed figure, not a chart bolted to a
     sidebar. */
  .wheel__header {
    margin: 0 0 var(--space-5, 24px);
    padding-bottom: var(--space-2, 8px);
    border-bottom: 2px solid var(--brick, #9b4a3f);
  }

  .wheel__title {
    font-family: var(--font-display, Georgia, serif);
    font-size: var(--display-2, 24px);
    color: var(--fg, #1a1a1a);
    margin: 0 0 4px;
  }

  .wheel__dek {
    font-family: var(--font-body, Georgia, serif);
    font-size: var(--body-3, 14px);
    line-height: var(--lh-snug, 1.35);
    color: var(--fg-light, #6b6b6b);
    max-width: var(--reader-max, 660px);
    margin: 0;
  }

  /* The wheel and its detail panel as one composed figure: side by side once
     there is room for both, stacked (panel below wheel) on narrow viewports. */
  .wheel__hero {
    display: grid;
    grid-template-columns: 1fr;
    align-items: start;
    gap: var(--space-5, 24px);
    margin: 0 0 var(--space-5, 24px);
  }

  @media (min-width: 900px) {
    .wheel__hero {
      grid-template-columns: minmax(0, 880px) 1fr;
    }
  }

  /* Wide breakout + pan below ~800px, same treatment as ArchitectureDiagram:
     scaling would shrink the ring/sector labels and mark numerals past
     legibility, so the frame pans horizontally instead. */
  .wheel__figure-wrap {
    --wide: min(880px, calc(100vw - 3rem));
    width: var(--wide);
    max-width: 100%;
    padding: var(--space-4, 16px);
    background: var(--paper-bright, #fff);
    border: 1px solid var(--fg-faint, #e8e8e8);
    border-radius: var(--radius-md, 4px);
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior-x: contain;
  }

  .wheel__svg {
    display: block;
    width: 100%;
    height: auto;
    min-width: 720px;
  }

  .wheel__bg {
    fill: var(--paper-bright, #fff);
    cursor: default;
  }

  .wheel__ring-line {
    fill: none;
    stroke: var(--fg-faint, #e8e8e8);
    stroke-width: 1;
  }

  .wheel__ring-line--edge {
    stroke: var(--ink, #1a1a1a);
    opacity: 0.55;
  }

  .wheel__sector-line {
    stroke: var(--fg-faint, #e8e8e8);
    stroke-width: 1;
  }

  .wheel__label-halo {
    fill: var(--paper-bright, #fff);
    opacity: 0.9;
    pointer-events: none;
  }

  .wheel__ring-label {
    font-family: var(--font-mono, monospace);
    font-size: 9px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    fill: var(--fg-light, #6b6b6b);
    pointer-events: none;
  }

  .wheel__sector-label {
    font-family: var(--font-mono, monospace);
    font-size: 11.5px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    fill: var(--fg, #1a1a1a);
    pointer-events: none;
  }

  /* Chords take the SELECTED entry's own layer hue, never a fixed colour:
     they say "this is what this entry connects to", read through whichever
     sector started the selection. */
  .wheel__chord {
    fill: none;
    stroke: var(--ink, #1a1a1a);
    stroke-width: 1.8;
    opacity: 0.6;
  }

  .wheel__chord--capability {
    stroke: var(--layer-capability, #205599);
  }

  .wheel__chord--control {
    stroke: var(--layer-control, #9b4a3f);
  }

  .wheel__chord--evidence {
    stroke: var(--layer-evidence, #b08d20);
  }

  .wheel__chord--escape {
    stroke-dasharray: 5 4;
  }

  .wheel__mark {
    cursor: pointer;
    outline: none;
  }

  /* Fill carries the layer hue; stroke stays a thin ink edge for crispness
     against the paper so the shape reads cleanly at this size regardless of
     hue. A 2px surface gap is kept between adjacent marks at the geometry
     level (src/lib/pattern-wheel.ts), not here. */
  .wheel__mark-shape {
    fill: var(--paper-bright, #fff);
    stroke: var(--ink, #1a1a1a);
    stroke-width: 1;
    transition: fill 120ms ease, stroke-width 120ms ease, opacity 120ms ease;
  }

  .wheel__mark--capability .wheel__mark-shape {
    fill: var(--layer-capability, #205599);
  }

  .wheel__mark--control .wheel__mark-shape {
    fill: var(--layer-control, #9b4a3f);
  }

  .wheel__mark--evidence .wheel__mark-shape {
    fill: var(--layer-evidence, #b08d20);
  }

  /* Numeral colour is derived per layer, not set once globally: gold is much
     lighter than blue and brick, so one fixed numeral colour can't clear
     4.5:1 on all three. Light (#e8e8e8) reads on blue (~6.08:1) and brick
     (~4.98:1); ink (#1a1a1a) reads on gold (~5.53:1). Never a hue itself,
     just knockout/reversed text keyed to what sits under it. */
  .wheel__mark-key {
    font-family: var(--font-mono, monospace);
    font-size: 7.2px;
    pointer-events: none;
    user-select: none;
    transition: opacity 120ms ease;
  }

  .wheel__mark--capability .wheel__mark-key {
    fill: var(--numeral-capability, #e8e8e8);
  }

  .wheel__mark--control .wheel__mark-key {
    fill: var(--numeral-control, #e8e8e8);
  }

  .wheel__mark--evidence .wheel__mark-key {
    fill: var(--numeral-evidence, #1a1a1a);
  }

  /* Selection/hover are signalled by an ink halo, not colour: brick is a
     layer hue now (control), so it can no longer double as "selected". */
  .wheel__mark-halo {
    fill: none;
    stroke: var(--ink, #1a1a1a);
    pointer-events: none;
  }

  .wheel__mark-halo--hover {
    stroke-width: 1;
    opacity: 0.5;
  }

  .wheel__mark-halo--selected {
    stroke-width: 2;
    opacity: 0.9;
  }

  .wheel__mark:focus-visible .wheel__mark-shape,
  .wheel__mark--hovered .wheel__mark-shape,
  .wheel__mark--selected .wheel__mark-shape {
    stroke-width: 1.6;
  }

  .wheel__mark--dimmed .wheel__mark-shape,
  .wheel__mark--dimmed .wheel__mark-key {
    opacity: 0.25;
  }

  /* Detail panel: fixed min-height so hovering different entries doesn't
     jitter the page. Paper/ink treatment matches PatternCard.astro (brick
     wash + left spine, no full border box) so this reads as the same family
     of surface as the rest of the page, not a chart's sidebar. */
  .wheel__detail {
    min-height: 108px;
    padding: var(--space-4, 16px) var(--space-5, 24px);
    border-left: 3px solid var(--brick, #9b4a3f);
    background: var(--brick-wash, rgba(155, 74, 63, 0.06));
  }

  .wheel__detail-legend {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-4, 16px);
    margin-bottom: var(--space-3, 12px);
    padding-bottom: var(--space-3, 12px);
    border-bottom: 1px solid var(--fg-faint, #e8e8e8);
  }

  .wheel__detail-legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: var(--font-mono, monospace);
    font-size: var(--meta-2, 11px);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--fg-light, #6b6b6b);
  }

  .wheel__detail-head {
    display: flex;
    align-items: center;
    gap: var(--space-3, 12px);
    margin-bottom: 4px;
  }

  .wheel__detail-cell {
    font-family: var(--font-mono, monospace);
    font-size: var(--meta-2, 11px);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--fg-light, #6b6b6b);
  }

  .wheel__detail-tag {
    font-family: var(--font-mono, monospace);
    font-size: var(--meta-3, 10px);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--fg-light, #6b6b6b);
    border: 1px solid var(--fg-faint, #e8e8e8);
    border-radius: 2px;
    padding: 1px 6px;
  }

  .wheel__detail-name {
    font-family: var(--font-display, Georgia, serif);
    font-size: var(--display-3, 20px);
    color: var(--fg, #1a1a1a);
    margin: 0 0 4px;
  }

  .wheel__detail-line {
    font-family: var(--font-body, Georgia, serif);
    font-size: var(--body-3, 14px);
    line-height: var(--lh-snug, 1.35);
    color: var(--fg, #1a1a1a);
    margin: 0 0 6px;
  }

  .wheel__detail-also {
    font-family: var(--font-body, Georgia, serif);
    font-size: var(--body-3, 14px);
    color: var(--fg-light, #6b6b6b);
    margin: 0 0 4px;
  }

  .wheel__detail-link {
    display: inline-block;
    font-family: var(--font-mono, monospace);
    font-size: var(--meta-2, 11px);
    letter-spacing: 0.04em;
    color: var(--fg, #1a1a1a);
    text-decoration: underline;
    text-decoration-color: var(--fg-light, #6b6b6b);
    text-underline-offset: 3px;
    margin-top: 4px;
  }

  .wheel__detail-link:hover {
    text-decoration-color: var(--ink, #1a1a1a);
  }

  .wheel__detail-unwritten {
    display: inline-block;
    font-family: var(--font-mono, monospace);
    font-size: var(--meta-2, 11px);
    color: var(--fg-lighter, #999);
    margin-top: 4px;
  }

  .wheel__detail-empty {
    font-family: var(--font-body, Georgia, serif);
    font-size: var(--body-3, 14px);
    color: var(--fg-light, #6b6b6b);
    margin: 0;
  }

  .wheel__note {
    font-family: var(--font-body, Georgia, serif);
    font-style: italic;
    font-size: var(--body-3, 14px);
    line-height: var(--lh-snug, 1.35);
    color: var(--fg-light, #6b6b6b);
    max-width: var(--reader-max, 660px);
    margin: 0 0 var(--space-6, 32px);
  }

  /* Swatch dot is the one place the hue-to-layer key is spelled out plainly
     and statelessly: in the detail panel head once an entry is active, and
     in the panel's own empty-state legend. Present in the no-JS render. */
  .wheel__legend-swatch {
    display: inline-block;
    flex: none;
    width: 9px;
    height: 9px;
    border-radius: 50%;
  }

  .wheel__legend-swatch--capability {
    background: var(--layer-capability, #205599);
  }

  .wheel__legend-swatch--control {
    background: var(--layer-control, #9b4a3f);
  }

  .wheel__legend-swatch--evidence {
    background: var(--layer-evidence, #b08d20);
  }
</style>
