<script lang="ts">
  /**
   * TraceViewer — interactive trace JSON viewer.
   * Displays an array of trace steps with collapsible tool-call details
   * and per-step token accounting. Svelte 5 runes API.
   *
   * Usage in MDX:
   *   <TraceViewer src="/agentic-ai/trace-replay/should-i-use-an-agent.json" client:visible />
   */

  interface TraceStep {
    timestamp: string;
    actor: 'user' | 'model' | 'tool';
    type: 'message' | 'tool_call' | 'tool_result';
    content: string;
    toolName?: string;
    inputTokens?: number;
    outputTokens?: number;
    cost?: number;
  }

  interface Trace {
    sessionId: string;
    model: string;
    timestamp: string;
    totalTokens: number;
    totalCost: number;
    steps: TraceStep[];
  }

  let { src, trace }: { src?: string; trace?: Trace } = $props();

  let loadedTrace = $state<Trace | null>(trace ?? null);
  let expanded = $state<Set<number>>(new Set());

  $effect(() => {
    if (!src || loadedTrace) return;
    let aborted = false;
    fetch(src)
      .then((r) => r.json())
      .then((data: Trace) => {
        if (!aborted) loadedTrace = data;
      })
      .catch((e) => console.error('TraceViewer: failed to load', src, e));
    return () => { aborted = true; };
  });

  function toggle(i: number) {
    if (expanded.has(i)) expanded.delete(i);
    else expanded.add(i);
    expanded = new Set(expanded);
  }
</script>

{#if !loadedTrace}
  <div class="trace-viewer trace-viewer--loading">Loading trace…</div>
{:else}
  <div class="trace-viewer">
    <div class="trace-viewer__header">
      <span class="trace-viewer__label">Trace</span>
      <span class="trace-viewer__meta">
        {loadedTrace.model} · {loadedTrace.totalTokens.toLocaleString()} tokens · ${loadedTrace.totalCost.toFixed(4)}
      </span>
    </div>
    <ol class="trace-viewer__steps">
      {#each loadedTrace.steps as step, i}
        <li class="trace-viewer__step trace-viewer__step--{step.actor}">
          <button class="trace-viewer__row" onclick={() => toggle(i)} aria-expanded={expanded.has(i)}>
            <span class="trace-viewer__actor">{step.actor}</span>
            <span class="trace-viewer__type">{step.type}{step.toolName ? `: ${step.toolName}` : ''}</span>
            <span class="trace-viewer__chevron">{expanded.has(i) ? '▾' : '▸'}</span>
          </button>
          {#if expanded.has(i)}
            <div class="trace-viewer__body">
              <pre>{step.content}</pre>
              {#if step.inputTokens || step.outputTokens}
                <div class="trace-viewer__tokens">
                  {step.inputTokens ?? 0} in · {step.outputTokens ?? 0} out
                  {#if step.cost}· ${step.cost.toFixed(4)}{/if}
                </div>
              {/if}
            </div>
          {/if}
        </li>
      {/each}
    </ol>
  </div>
{/if}

<style>
  .trace-viewer {
    margin: var(--space-5, 24px) 0;
    border: 1px solid var(--fg-faint, #e8e8e8);
    border-radius: var(--radius-md, 4px);
    overflow: hidden;
    font-family: var(--font-mono, monospace);
    font-size: 13px;
  }

  .trace-viewer--loading {
    padding: 16px;
    color: var(--fg-light, #6b6b6b);
    font-style: italic;
  }

  .trace-viewer__header {
    padding: 8px 16px;
    background: var(--paper-recess, #f5f5f3);
    border-bottom: 1px solid var(--fg-faint, #e8e8e8);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .trace-viewer__label { font-weight: 600; }
  .trace-viewer__meta { color: var(--fg-light, #6b6b6b); }

  .trace-viewer__steps {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .trace-viewer__step {
    border-bottom: 1px solid var(--fg-faint, #e8e8e8);
  }

  .trace-viewer__step:last-child {
    border-bottom: 0;
  }

  .trace-viewer__step--user .trace-viewer__actor { color: var(--brick, #9b4a3f); }
  .trace-viewer__step--tool .trace-viewer__actor { color: #4a7c6e; }

  .trace-viewer__row {
    display: flex;
    width: 100%;
    padding: 8px 16px;
    background: transparent;
    border: 0;
    cursor: pointer;
    text-align: left;
    align-items: center;
    gap: 12px;
    font: inherit;
    color: inherit;
  }

  .trace-viewer__row:hover {
    background: var(--paper-recess, #f5f5f3);
  }

  .trace-viewer__actor {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 10px;
    font-weight: 600;
    min-width: 50px;
  }

  .trace-viewer__type {
    flex: 1;
    color: var(--fg-light, #6b6b6b);
  }

  .trace-viewer__chevron {
    color: var(--fg-lighter, #999);
  }

  .trace-viewer__body {
    padding: 0 16px 12px;
    background: var(--paper-recess, #f5f5f3);
  }

  .trace-viewer__body pre {
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0 0 8px;
    font-size: 12px;
    line-height: 1.55;
    color: var(--fg, #1a1a1a);
  }

  .trace-viewer__tokens {
    font-size: 11px;
    color: var(--fg-light, #6b6b6b);
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
</style>
