<script lang="ts">
  /**
   * D3Chart — bar / compare chart Svelte 5 island.
   * Loads chart data from a static JSON URL OR receives inline data prop.
   * Renders SVG with brick-red accent on the "winning" datum.
   */
  import { scaleLinear, scaleBand, max, formatTick } from '~/lib/d3-helpers';

  interface DataPoint {
    label: string;
    value: number;
    accent?: boolean;
  }

  interface ComparePoint {
    label: string;
    a: number;
    b: number;
  }

  type ChartData = DataPoint[] | ComparePoint[];

  let {
    type = 'bar',
    data,
    src,
    height = 240,
    unit = '',
    aLabel = 'A',
    bLabel = 'B',
  }: {
    type?: 'bar' | 'compare';
    data?: ChartData;
    src?: string;
    height?: number;
    unit?: '%' | '×' | 'pp' | '';
    aLabel?: string;
    bLabel?: string;
  } = $props();

  let loadedData = $state<ChartData | null>(data ?? null);

  $effect(() => {
    if (!src || loadedData) return;
    let aborted = false;
    fetch(src)
      .then((r) => r.json())
      .then((d: ChartData) => {
        if (!aborted) loadedData = d;
      })
      .catch((e) => console.error('D3Chart: load failed', src, e));
    return () => { aborted = true; };
  });

  // Layout
  const margin = { top: 12, right: 20, bottom: 36, left: 44 };
  const width = 720;
  const innerW = width - margin.left - margin.right;
  const innerH = $derived(height - margin.top - margin.bottom);

  // Bar chart scales
  const barScales = $derived.by(() => {
    if (!loadedData || type !== 'bar') return null;
    const points = loadedData as DataPoint[];
    const x = scaleBand<string>().domain(points.map((p) => p.label)).range([0, innerW]).padding(0.2);
    const yMax = (max(points, (p) => p.value) ?? 0) * 1.1;
    const y = scaleLinear().domain([0, yMax]).range([innerH, 0]);
    return { x, y, points };
  });

  // Compare chart scales
  const compareScales = $derived.by(() => {
    if (!loadedData || type !== 'compare') return null;
    const points = loadedData as ComparePoint[];
    const x = scaleBand<string>().domain(points.map((p) => p.label)).range([0, innerW]).padding(0.25);
    const yMax = (max(points, (p) => Math.max(p.a, p.b)) ?? 0) * 1.1;
    const y = scaleLinear().domain([0, yMax]).range([innerH, 0]);
    return { x, y, points };
  });
</script>

{#if !loadedData}
  <div class="d3-chart d3-chart--loading">Loading chart…</div>
{:else}
  <figure class="d3-chart">
    <svg viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Chart">
      <g transform="translate({margin.left}, {margin.top})">
        {#if type === 'bar' && barScales}
          {@const s = barScales}
          {#each s.points as p}
            {@const bw = s.x.bandwidth()}
            {@const bx = s.x(p.label) ?? 0}
            <rect
              x={bx}
              y={s.y(p.value)}
              width={bw}
              height={innerH - s.y(p.value)}
              fill={p.accent ? '#9b4a3f' : '#1a1a1a'}
            />
            <text x={bx + bw / 2} y={innerH + 16} text-anchor="middle" font-size="11" fill="#6b6b6b">{p.label}</text>
            <text x={bx + bw / 2} y={s.y(p.value) - 4} text-anchor="middle" font-size="11" fill="#1a1a1a" font-weight="500">
              {formatTick(p.value, unit)}
            </text>
          {/each}
        {/if}
        {#if type === 'compare' && compareScales}
          {@const s = compareScales}
          {#each s.points as p}
            {@const bw = s.x.bandwidth() / 2 - 2}
            {@const bx = s.x(p.label) ?? 0}
            <rect x={bx} y={s.y(p.a)} width={bw} height={innerH - s.y(p.a)} fill="#1a1a1a" />
            <rect x={bx + bw + 4} y={s.y(p.b)} width={bw} height={innerH - s.y(p.b)} fill="#9b4a3f" />
            <text x={bx + s.x.bandwidth() / 2} y={innerH + 16} text-anchor="middle" font-size="11" fill="#6b6b6b">{p.label}</text>
          {/each}
        {/if}
      </g>
    </svg>
    {#if type === 'compare'}
      <figcaption class="d3-chart__legend">
        <span class="d3-chart__legend-dot d3-chart__legend-dot--a"></span> {aLabel}
        <span class="d3-chart__legend-dot d3-chart__legend-dot--b"></span> {bLabel}
      </figcaption>
    {/if}
  </figure>
{/if}

<style>
  .d3-chart {
    margin: var(--space-5, 24px) 0;
    padding: 16px;
    border: 1px solid var(--fg-faint, #e8e8e8);
    border-radius: var(--radius-md, 4px);
    background: var(--paper-bright, #fff);
  }

  .d3-chart--loading {
    color: var(--fg-light, #6b6b6b);
    font-style: italic;
    text-align: center;
    padding: 32px 16px;
  }

  .d3-chart svg {
    display: block;
    width: 100%;
    height: auto;
  }

  .d3-chart__legend {
    display: flex;
    gap: 16px;
    justify-content: center;
    margin-top: 12px;
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    color: var(--fg-light, #6b6b6b);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .d3-chart__legend-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    margin-right: 4px;
    vertical-align: middle;
  }

  .d3-chart__legend-dot--a { background: #1a1a1a; }
  .d3-chart__legend-dot--b { background: #9b4a3f; }
</style>
