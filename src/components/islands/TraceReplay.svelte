<script lang="ts">
  /**
   * TraceReplay — homepage agent demo.
   * User picks a sample query chip; the trace JSON loads from /trace-replay/;
   * the response is replayed token-by-token. No live agent invocation.
   * Svelte 5 runes API.
   */

  interface TraceChip {
    id: string;
    label: string;
    file: string;
  }

  interface TraceSession {
    sessionId: string;
    model: string;
    query: string;
    response: string;
    totalTokens: number;
    totalCost: number;
    trace: Array<{
      step: number;
      type: 'tool_call' | 'tool_result' | 'reasoning';
      content: string;
    }>;
  }

  let { manifestUrl = '/agentic-ai/trace-replay/manifest.json' }: { manifestUrl?: string } = $props();

  // Resolve session files relative to the manifest's directory so a caller can
  // override manifestUrl to point at a different trace-replay folder and have
  // chips load from there.
  const sessionsBase = manifestUrl.replace(/[^/]*$/, '');

  let chips = $state<TraceChip[]>([]);
  let active = $state<string | null>(null);
  let session = $state<TraceSession | null>(null);
  let replayedText = $state('');
  let replayProgress = $state(0);
  let loading = $state(false);

  // Load manifest on mount
  $effect(() => {
    fetch(manifestUrl)
      .then((r) => r.json())
      .then((m: { chips: TraceChip[] }) => {
        chips = m.chips;
      })
      .catch((e) => console.error('TraceReplay: manifest load failed', e));
  });

  // Replay engine
  async function playSession(chip: TraceChip) {
    active = chip.id;
    loading = true;
    session = null;
    replayedText = '';
    replayProgress = 0;

    try {
      const r = await fetch(`${sessionsBase}${chip.file}`);
      const data: TraceSession = await r.json();
      loading = false;
      session = data;

      // Token-by-token replay at ~25 tokens/sec
      const chars = data.response;
      const chunkSize = 3;
      const intervalMs = 24;
      for (let i = 0; i <= chars.length; i += chunkSize) {
        replayedText = chars.slice(0, i);
        replayProgress = i / chars.length;
        await new Promise((res) => setTimeout(res, intervalMs));
        if (active !== chip.id) return; // user clicked a different chip
      }
      replayedText = chars;
      replayProgress = 1;
    } catch (e) {
      console.error('TraceReplay: session load failed', e);
      loading = false;
    }
  }

  function reset() {
    active = null;
    session = null;
    replayedText = '';
    replayProgress = 0;
  }
</script>

<section class="trace-replay">
  <header class="trace-replay__header">
    <div class="trace-replay__label">Try the agent · pre-recorded sessions</div>
    {#if active}
      <button class="trace-replay__reset" onclick={reset}>← Pick another</button>
    {/if}
  </header>

  {#if !active}
    <div class="trace-replay__chips">
      {#each chips as chip}
        <button class="trace-replay__chip" onclick={() => playSession(chip)}>
          {chip.label}
        </button>
      {/each}
      {#if chips.length === 0}
        <span class="trace-replay__chips-empty">Loading sample sessions…</span>
      {/if}
    </div>
  {:else}
    <div class="trace-replay__session">
      <div class="trace-replay__query">{chips.find((c) => c.id === active)?.label}</div>
      {#if loading}
        <div class="trace-replay__loading">…</div>
      {:else if session}
        <pre class="trace-replay__response">{replayedText}<span class="trace-replay__cursor" class:trace-replay__cursor--blink={replayProgress < 1}></span></pre>
        {#if replayProgress === 1}
          <footer class="trace-replay__footer">
            <span class="trace-replay__cost">${session.totalCost.toFixed(4)} · {session.totalTokens} tokens · {session.model}</span>
          </footer>
        {/if}
      {/if}
    </div>
  {/if}
</section>

<style>
  .trace-replay {
    margin: var(--space-7, 48px) 0;
    background: var(--ink, #1a1a1a);
    color: var(--paper, #fafaf8);
    padding: 32px 28px 28px;
    border-radius: var(--radius-md, 4px);
  }

  .trace-replay__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .trace-replay__label {
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: rgba(255, 255, 255, 0.5);
  }

  .trace-replay__reset {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.75);
    padding: 4px 10px;
    border-radius: 2px;
    cursor: pointer;
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    transition: all 150ms ease;
  }

  .trace-replay__reset:hover {
    border-color: rgba(255, 255, 255, 0.5);
    color: var(--paper, #fafaf8);
  }

  .trace-replay__chips {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .trace-replay__chip {
    text-align: left;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: var(--paper, #fafaf8);
    padding: 12px 16px;
    border-radius: var(--radius-sm, 2px);
    cursor: pointer;
    font-family: var(--font-display, serif);
    font-size: 16px;
    line-height: 1.4;
    transition: all 150ms ease;
  }

  .trace-replay__chip:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: var(--brick, #9b4a3f);
  }

  .trace-replay__chip:focus-visible {
    outline: 2px solid var(--brick, #9b4a3f);
    outline-offset: 2px;
  }

  .trace-replay__chips-empty {
    color: rgba(255, 255, 255, 0.4);
    font-style: italic;
    font-family: var(--font-mono, monospace);
  }

  .trace-replay__query {
    font-family: var(--font-display, serif);
    font-style: italic;
    font-size: 18px;
    line-height: 1.35;
    color: rgba(255, 255, 255, 0.85);
    margin-bottom: 16px;
    padding-left: 12px;
    border-left: 2px solid var(--brick, #9b4a3f);
  }

  .trace-replay__loading {
    font-family: var(--font-mono, monospace);
    font-size: 18px;
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 0.2em;
  }

  .trace-replay__response {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-sm, 2px);
    padding: 16px;
    margin: 0;
    font-family: var(--font-body, system-ui);
    font-size: 14px;
    line-height: 1.65;
    white-space: pre-wrap;
    word-break: break-word;
    color: var(--paper, #fafaf8);
    min-height: 100px;
  }

  .trace-replay__cursor {
    display: inline-block;
    width: 8px;
    height: 14px;
    background: var(--brick, #9b4a3f);
    vertical-align: text-bottom;
    margin-left: 2px;
  }

  .trace-replay__cursor--blink {
    animation: trace-cursor 800ms infinite;
  }

  @keyframes trace-cursor {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }

  .trace-replay__footer {
    margin-top: 12px;
    font-family: var(--font-mono, monospace);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: rgba(255, 255, 255, 0.4);
  }

  @media (prefers-reduced-motion: reduce) {
    .trace-replay__cursor--blink { animation: none; opacity: 1; }
  }
</style>
