<script lang="ts">
  /**
   * CommandPalette — Cmd+K Pagefind-powered fuzzy search.
   * Mounted globally via PageLayout. Slides in from top with backdrop blur.
   * Svelte 5 runes API.
   */

  interface SearchResult {
    url: string;
    title: string;
    excerpt: string;
  }

  let isOpen = $state(false);
  let query = $state('');
  let results = $state<SearchResult[]>([]);
  let activeIdx = $state(0);
  let pagefindLoaded = $state(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let pagefind: any = null;

  // Lazy-load Pagefind only when the palette is first opened.
  async function loadPagefind() {
    if (pagefindLoaded) return;
    try {
      pagefind = await import(/* @vite-ignore */ '/agentic-ai/pagefind/pagefind.js');
      pagefindLoaded = true;
    } catch (e) {
      console.error('CommandPalette: Pagefind load failed', e);
    }
  }

  async function runSearch() {
    if (!query.trim() || !pagefind) {
      results = [];
      return;
    }
    try {
      const r = await pagefind.search(query);
      const top10 = r.results.slice(0, 10);
      const datas = await Promise.all(top10.map((x: { data: () => Promise<SearchResult> }) => x.data()));
      results = datas;
      activeIdx = 0;
    } catch (e) {
      console.error('CommandPalette: search failed', e);
    }
  }

  function open() {
    isOpen = true;
    loadPagefind();
    setTimeout(() => {
      document.getElementById('cmdk-input')?.focus();
    }, 50);
  }

  function close() {
    isOpen = false;
    query = '';
    results = [];
  }

  function onKey(e: KeyboardEvent) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      if (isOpen) close();
      else open();
      return;
    }
    if (!isOpen) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (results.length === 0) return;
      activeIdx = Math.min(activeIdx + 1, results.length - 1);
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (results.length === 0) return;
      activeIdx = Math.max(activeIdx - 1, 0);
    }
    if (e.key === 'Enter' && results[activeIdx]) {
      window.location.href = results[activeIdx].url;
    }
  }

  $effect(() => {
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  });

  $effect(() => {
    if (isOpen) runSearch();
  });
</script>

{#if isOpen}
  <div class="cmdk" role="dialog" aria-modal="true" aria-label="Search">
    <div class="cmdk__backdrop" onclick={close} role="presentation"></div>
    <div class="cmdk__panel">
      <input
        id="cmdk-input"
        type="search"
        placeholder="Search this site (Cmd+K)…"
        bind:value={query}
        class="cmdk__input"
        autocomplete="off"
      />
      {#if results.length > 0}
        <ul class="cmdk__results">
          {#each results as r, i}
            <li class:cmdk__result--active={i === activeIdx}>
              <a href={r.url} class="cmdk__result">
                <div class="cmdk__result-title">{r.title}</div>
                <div class="cmdk__result-excerpt" innerHTML={r.excerpt}></div>
              </a>
            </li>
          {/each}
        </ul>
      {:else if query.length > 0 && pagefindLoaded}
        <p class="cmdk__empty">No results.</p>
      {:else if !pagefindLoaded}
        <p class="cmdk__empty">Loading search…</p>
      {/if}
    </div>
  </div>
{/if}

<style>
  .cmdk {
    position: fixed;
    inset: 0;
    z-index: 200;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 12vh;
  }

  .cmdk__backdrop {
    position: absolute;
    inset: 0;
    background: rgba(26, 26, 26, 0.4);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    animation: cmdk-fade 200ms ease-out;
  }

  .cmdk__panel {
    position: relative;
    width: 100%;
    max-width: 680px;
    margin: 0 24px;
    background: var(--paper, #fafaf8);
    border-radius: var(--radius-md, 4px);
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
    overflow: hidden;
    animation: cmdk-slide 250ms cubic-bezier(0.2, 0.8, 0.2, 1);
  }

  @keyframes cmdk-fade {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes cmdk-slide {
    from { opacity: 0; transform: translateY(-12px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .cmdk__input {
    width: 100%;
    padding: 20px 24px;
    border: 0;
    background: transparent;
    font-family: var(--font-body, system-ui);
    font-size: 18px;
    color: var(--fg, #1a1a1a);
    border-bottom: 1px solid var(--fg-faint, #e8e8e8);
  }

  .cmdk__input:focus {
    outline: none;
  }

  .cmdk__results {
    list-style: none;
    margin: 0;
    padding: 8px 0;
    max-height: 60vh;
    overflow-y: auto;
  }

  .cmdk__result {
    display: block;
    padding: 12px 24px;
    color: var(--fg, #1a1a1a);
    text-decoration: none;
  }

  .cmdk__result--active .cmdk__result,
  .cmdk__result:hover {
    background: var(--paper-recess, #f5f5f3);
  }

  .cmdk__result-title {
    font-family: var(--font-display, serif);
    font-weight: 500;
    font-size: 16px;
    margin-bottom: 4px;
  }

  .cmdk__result-excerpt {
    font-size: 13px;
    line-height: 1.55;
    color: var(--fg-light, #6b6b6b);
  }

  .cmdk__result-excerpt :global(mark) {
    background: var(--brick-wash, rgba(155, 74, 63, 0.15));
    color: var(--brick, #9b4a3f);
    font-weight: 500;
    padding: 0 1px;
  }

  .cmdk__empty {
    padding: 24px;
    color: var(--fg-light, #6b6b6b);
    font-style: italic;
    text-align: center;
    font-family: var(--font-mono, monospace);
    font-size: 13px;
  }
</style>
