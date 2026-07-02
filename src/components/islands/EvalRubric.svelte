<script lang="ts">
  /**
   * EvalRubric — interactive scorecard with hover-to-expand criterion detail.
   * Svelte 5 runes API.
   */
  interface Criterion {
    score: number;
    weight: number;
    detail?: string;
  }

  interface Dimension {
    name: string;
    score: number;
    maxScore: number;
    criteria?: Record<string, Criterion>;
  }

  interface Rubric {
    title?: string;
    dimensions: Dimension[];
  }

  let { rubric }: { rubric: Rubric } = $props();
  let activeDim = $state<number | null>(null);

  const totalScore = $derived(rubric.dimensions.reduce((sum, d) => sum + d.score, 0));
  const totalMax = $derived(rubric.dimensions.reduce((sum, d) => sum + d.maxScore, 0));
</script>

<div class="eval-rubric">
  {#if rubric.title}
    <div class="eval-rubric__header">
      <span class="eval-rubric__title">{rubric.title}</span>
      <span class="eval-rubric__total">{totalScore} / {totalMax}</span>
    </div>
  {/if}
  <div class="eval-rubric__grid">
    {#each rubric.dimensions as dim, i}
      <div
        class="eval-rubric__cell"
        class:eval-rubric__cell--active={activeDim === i}
        onmouseenter={() => (activeDim = i)}
        onmouseleave={() => (activeDim = null)}
        role="button"
        tabindex="0"
        onfocus={() => (activeDim = i)}
        onblur={() => (activeDim = null)}
      >
        <div class="eval-rubric__name">{dim.name}</div>
        <div class="eval-rubric__score">
          <span class="eval-rubric__score-value">{dim.score}</span>
          <span class="eval-rubric__score-max">/ {dim.maxScore}</span>
        </div>
        <div class="eval-rubric__bar">
          <div
            class="eval-rubric__bar-fill"
            style="width: {dim.maxScore > 0 ? Math.max(0, Math.min(100, (dim.score / dim.maxScore) * 100)) : 0}%"
          ></div>
        </div>
        {#if activeDim === i && dim.criteria}
          <div class="eval-rubric__detail">
            {#each Object.entries(dim.criteria) as [name, c]}
              <div class="eval-rubric__criterion">
                <span class="eval-rubric__criterion-name">{name}</span>
                <span class="eval-rubric__criterion-score">{c.score} × w{c.weight}</span>
                {#if c.detail}
                  <div class="eval-rubric__criterion-detail">{c.detail}</div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>

<style>
  .eval-rubric {
    margin: var(--space-5, 24px) 0;
    border: 1px solid var(--ink);
    border-radius: var(--radius-md, 4px);
    background: var(--paper);
  }

  .eval-rubric__header {
    padding: 8px 16px;
    background: var(--paper-recess, #f5f5f3);
    display: flex;
    justify-content: space-between;
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--fg-light, #6b6b6b);
    border-bottom: 1px solid var(--fg-faint, #e8e8e8);
  }

  .eval-rubric__title { font-weight: 600; color: var(--fg, #1a1a1a); }
  .eval-rubric__total { color: var(--brick, #9b4a3f); font-weight: 600; }

  .eval-rubric__grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 1px;
    background: var(--fg-faint, #e8e8e8);
  }

  .eval-rubric__cell {
    background: var(--paper, #fafaf8);
    padding: 16px;
    position: relative;
    cursor: pointer;
    transition: background 150ms ease;
    outline: none;
  }

  .eval-rubric__cell:focus-visible {
    outline: 2px solid var(--brick, #9b4a3f);
    outline-offset: -2px;
  }

  .eval-rubric__cell--active {
    background: var(--paper-recess, #f5f5f3);
    z-index: 1;
  }

  .eval-rubric__name {
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--fg-light, #6b6b6b);
    margin-bottom: 4px;
  }

  .eval-rubric__score {
    font-family: var(--font-display, serif);
    font-size: 24px;
    font-weight: 500;
    line-height: 1;
  }

  .eval-rubric__score-max {
    color: var(--fg-light, #6b6b6b);
    font-size: 14px;
    margin-left: 2px;
  }

  .eval-rubric__bar {
    margin-top: 8px;
    height: 3px;
    background: var(--fg-faint, #e8e8e8);
    border-radius: 1.5px;
    overflow: hidden;
  }

  .eval-rubric__bar-fill {
    height: 100%;
    background: var(--brick, #9b4a3f);
    transition: width 250ms ease;
  }

  .eval-rubric__detail {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    z-index: 10;
    background: var(--paper);
    color: var(--ink);
    border: 1px solid var(--ink);
    padding: 12px;
    border-radius: 4px;
    font-size: 12px;
    line-height: 1.5;
    box-shadow: var(--shadow-card-hover, 0 4px 12px rgba(0, 0, 0, 0.08));
  }

  .eval-rubric__criterion {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 8px;
    margin-bottom: 6px;
  }

  .eval-rubric__criterion-name {
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--fg-light, #6b6b6b);
  }

  .eval-rubric__criterion-score {
    font-family: var(--font-mono, monospace);
    color: var(--ink);
  }

  .eval-rubric__criterion-detail {
    grid-column: 1 / -1;
    margin-top: 2px;
    color: var(--fg-light, #6b6b6b);
  }
</style>
