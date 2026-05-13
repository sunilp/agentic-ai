<script lang="ts">
  /**
   * ArchitectureToggle — A vs B architecture comparison.
   * Renders one of two SVG diagrams at a time. Toggle uses fade-and-scale
   * via {#key} block to re-trigger the entry animation.
   * Svelte 5 runes API.
   */
  interface Architecture {
    label: string;
    src: string;
    alt: string;
    caption?: string;
  }

  let { a, b }: { a: Architecture; b: Architecture } = $props();

  let active = $state<'a' | 'b'>('a');
  const current = $derived(active === 'a' ? a : b);
</script>

<figure class="arch-toggle">
  <div class="arch-toggle__tabs" role="tablist" aria-label="Architecture comparison">
    <button
      type="button"
      role="tab"
      aria-selected={active === 'a'}
      class="arch-toggle__tab"
      class:arch-toggle__tab--active={active === 'a'}
      onclick={() => (active = 'a')}
    >
      {a.label}
    </button>
    <button
      type="button"
      role="tab"
      aria-selected={active === 'b'}
      class="arch-toggle__tab"
      class:arch-toggle__tab--active={active === 'b'}
      onclick={() => (active = 'b')}
    >
      {b.label}
    </button>
  </div>
  <div class="arch-toggle__viewport">
    {#key active}
      <img class="arch-toggle__img" src={current.src} alt={current.alt} />
    {/key}
  </div>
  {#if current.caption}
    <figcaption class="arch-toggle__caption">{current.caption}</figcaption>
  {/if}
</figure>

<style>
  .arch-toggle {
    margin: var(--space-5, 24px) 0;
    border: 1px solid var(--fg-faint, #e8e8e8);
    border-radius: var(--radius-md, 4px);
    overflow: hidden;
    background: var(--paper-bright, #fff);
  }

  .arch-toggle__tabs {
    display: flex;
    background: var(--paper-recess, #f5f5f3);
    border-bottom: 1px solid var(--fg-faint, #e8e8e8);
  }

  .arch-toggle__tab {
    flex: 1;
    padding: 10px 16px;
    background: transparent;
    border: 0;
    cursor: pointer;
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--fg-light, #6b6b6b);
    transition: background 150ms ease, color 150ms ease;
  }

  .arch-toggle__tab:hover {
    color: var(--fg, #1a1a1a);
  }

  .arch-toggle__tab--active {
    background: var(--paper, #fafaf8);
    color: var(--brick, #9b4a3f);
    font-weight: 600;
    border-bottom: 2px solid var(--brick, #9b4a3f);
  }

  .arch-toggle__viewport {
    padding: 24px;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 240px;
  }

  .arch-toggle__img {
    width: 100%;
    max-width: 800px;
    height: auto;
    animation: arch-fade-in 250ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
  }

  @keyframes arch-fade-in {
    from { opacity: 0; transform: scale(0.985); }
    to { opacity: 1; transform: scale(1); }
  }

  @media (prefers-reduced-motion: reduce) {
    .arch-toggle__img { animation: none; }
  }

  .arch-toggle__caption {
    padding: 12px 16px;
    background: var(--paper-recess, #f5f5f3);
    border-top: 1px solid var(--fg-faint, #e8e8e8);
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    color: var(--fg-light, #6b6b6b);
    text-align: center;
  }
</style>
