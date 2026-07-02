<script lang="ts">
  /**
   * LoopLab — interactive companion to FN-004.
   * A deterministic, in-browser port of src/fn04/loop.py. Pick an agent
   * scenario, toggle the three external fences, and watch the same loop either
   * delete the database or get stopped. No API keys, no network: the logic is
   * the same as the Python tests. Svelte 5 runes.
   */

  type Scenario = 'hallucinated' | 'runaway';
  type Status = 'executed' | 'blocked';

  interface TraceRow {
    turn: number;
    label: string;
    status: Status | 'done' | 'halt';
    note: string;
  }

  interface Result {
    deleted: boolean;
    stopReason: string;
    trace: TraceRow[];
  }

  let scenario = $state<Scenario>('hallucinated');
  let cap = $state(true);
  let noProgress = $state(true);
  let gate = $state(true);
  let result = $state<Result | null>(null);

  const MAX_ITERATIONS = 8;
  const SAFETY_BOUND = 40; // hard stop so an unfenced runaway cannot hang the page

  const mode = $derived(cap && noProgress && gate ? 'enforced' : !cap && !noProgress && !gate ? 'prompted' : 'custom');

  function* steps(s: Scenario): Generator<{ name: string; destructive: boolean }> {
    if (s === 'hallucinated') {
      yield { name: 'read_rows', destructive: false };
      yield { name: 'delete_all', destructive: true };
      return; // then the agent claims it is done
    }
    // runaway: the agent repeats the same call forever, making no progress
    while (true) yield { name: 'check_status', destructive: false };
  }

  function run() {
    const db = { rows: 3, deleted: false };
    const trace: TraceRow[] = [];
    const seen = new Set<string>();
    let turn = 0;
    let stopReason = 'agent said done';
    const gen = steps(scenario);

    while (true) {
      const next = gen.next();
      if (next.done) {
        trace.push({ turn: turn + 1, label: 'done', status: 'done', note: 'agent claims the task is complete' });
        stopReason = 'agent said done';
        break;
      }
      turn += 1;
      const call = next.value;
      const key = call.name;

      if (noProgress && seen.has(key)) {
        trace.push({ turn, label: call.name, status: 'halt', note: 'no-progress fence: same call repeated, halted' });
        stopReason = 'no progress';
        break;
      }
      seen.add(key);

      if (call.destructive && gate) {
        trace.push({ turn, label: call.name, status: 'blocked', note: 'capability gate: no out-of-band approval, refused' });
      } else {
        if (call.name === 'delete_all') db.deleted = true;
        trace.push({ turn, label: call.name, status: 'executed', note: call.destructive ? 'destructive call executed' : 'ran' });
      }

      if (cap && turn >= MAX_ITERATIONS) {
        trace.push({ turn, label: 'cap', status: 'halt', note: `iteration cap: stopped at ${MAX_ITERATIONS} turns` });
        stopReason = 'iteration cap';
        break;
      }
      if (turn >= SAFETY_BOUND) {
        trace.push({ turn, label: 'unbounded', status: 'halt', note: 'no brake: still running at 40 turns (page safety stop)' });
        stopReason = 'never stopped';
        break;
      }
    }

    result = { deleted: db.deleted, stopReason, trace };
  }

  function preset(p: 'prompted' | 'enforced') {
    const on = p === 'enforced';
    cap = on;
    noProgress = on;
    gate = on;
    result = null;
  }
</script>

<div class="lab">
  <div class="lab__head">
    <span class="lab__eyebrow">Loop Lab</span>
    <span class="lab__mode" class:lab__mode--enforced={mode === 'enforced'} class:lab__mode--prompted={mode === 'prompted'}>{mode}</span>
  </div>

  <div class="lab__grid">
    <div class="lab__controls">
      <div class="lab__field">
        <span class="lab__label">Agent scenario</span>
        <label class="lab__radio"><input type="radio" name="scn" checked={scenario === 'hallucinated'} onchange={() => { scenario = 'hallucinated'; result = null; }} /> Hallucinated done <em>(reads, deletes, says done)</em></label>
        <label class="lab__radio"><input type="radio" name="scn" checked={scenario === 'runaway'} onchange={() => { scenario = 'runaway'; result = null; }} /> Runaway <em>(repeats the same call forever)</em></label>
      </div>

      <div class="lab__field">
        <span class="lab__label">External fences</span>
        <label class="lab__check"><input type="checkbox" bind:checked={gate} onchange={() => result = null} /> Capability gate <em>(destructive calls need out-of-band approval)</em></label>
        <label class="lab__check"><input type="checkbox" bind:checked={noProgress} onchange={() => result = null} /> No-progress detector <em>(halt on a repeated call)</em></label>
        <label class="lab__check"><input type="checkbox" bind:checked={cap} onchange={() => result = null} /> Iteration cap <em>(stop after {MAX_ITERATIONS} turns)</em></label>
      </div>

      <div class="lab__presets">
        <button type="button" class="lab__preset" onclick={() => preset('prompted')}>All off = prompted</button>
        <button type="button" class="lab__preset" onclick={() => preset('enforced')}>All on = enforced</button>
      </div>

      <button type="button" class="lab__run" onclick={run}>Run the loop →</button>
    </div>

    <div class="lab__output">
      {#if result}
        <div class="lab__db" class:lab__db--gone={result.deleted}>
          <span class="lab__db-label">production database</span>
          <span class="lab__db-state">{result.deleted ? 'DELETED' : 'intact'}</span>
        </div>
        <ol class="lab__trace">
          {#each result.trace as row}
            <li class="lab__trace-row lab__trace-row--{row.status}">
              <span class="lab__turn">{row.turn}</span>
              <span class="lab__call">{row.label}</span>
              <span class="lab__note">{row.note}</span>
            </li>
          {/each}
        </ol>
        <p class="lab__stop">stopped: <strong>{result.stopReason}</strong></p>
      {:else}
        <p class="lab__empty">Toggle the fences and run. With the gate off, the hallucinated-done agent deletes the database. With it on, the same agent cannot, by construction.</p>
      {/if}
    </div>
  </div>
</div>

<style>
  .lab {
    margin: var(--space-6, 32px) 0;
    border: 1px solid var(--ink);
    border-radius: var(--radius-md, 4px);
    background: var(--paper);
    overflow: hidden;
  }
  .lab__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--space-3, 12px) var(--space-4, 16px);
    background: var(--paper);
    color: var(--ink);
    border-bottom: 1px solid var(--ink);
  }
  .lab__eyebrow {
    font-family: var(--font-mono, monospace);
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--fg-light, #6b6b6b);
  }
  .lab__mode {
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 2px;
    background: var(--code-bg);
    border: 1px solid var(--code-border);
    color: var(--ink);
  }
  .lab__mode--enforced { background: var(--brick, #9b4a3f); color: var(--paper); border-color: var(--brick, #9b4a3f); }
  .lab__mode--prompted { background: var(--fg-light, #6b6b6b); color: var(--paper); border-color: var(--fg-light, #6b6b6b); }

  .lab__grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
  @media (max-width: 640px) { .lab__grid { grid-template-columns: 1fr; } }

  .lab__controls {
    padding: var(--space-4, 16px);
    border-right: 1px solid var(--fg-faint, #e8e8e8);
    display: flex;
    flex-direction: column;
    gap: var(--space-4, 16px);
  }
  @media (max-width: 640px) { .lab__controls { border-right: 0; border-bottom: 1px solid var(--fg-faint, #e8e8e8); } }

  .lab__label {
    display: block;
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--fg-light, #6b6b6b);
    margin-bottom: 8px;
  }
  .lab__radio, .lab__check {
    display: block;
    font-family: var(--font-ui);
    font-size: 14px;
    color: var(--fg, #1a1a1a);
    margin-bottom: 6px;
    cursor: pointer;
  }
  .lab__radio em, .lab__check em { color: var(--fg-light, #6b6b6b); font-style: normal; font-size: 12px; }

  .lab__presets { display: flex; gap: 8px; flex-wrap: wrap; }
  .lab__preset {
    font-family: var(--font-mono, monospace);
    font-size: 11px;
    padding: 4px 8px;
    border: 1px solid var(--fg-faint, #e8e8e8);
    background: var(--paper, #fafaf8);
    border-radius: 2px;
    cursor: pointer;
  }
  .lab__preset:hover { border-color: var(--brick, #9b4a3f); color: var(--brick, #9b4a3f); }

  .lab__run {
    align-self: flex-start;
    font-family: var(--font-ui);
    font-size: 14px;
    font-weight: 500;
    color: var(--paper, #fafaf8);
    background: var(--ink, #1a1a1a);
    border: 0;
    border-radius: 2px;
    padding: 10px 16px;
    cursor: pointer;
  }
  .lab__run:hover { background: var(--brick, #9b4a3f); }

  .lab__output { padding: var(--space-4, 16px); }

  .lab__db {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border: 1px solid var(--fg-faint, #e8e8e8);
    border-radius: 4px;
    margin-bottom: var(--space-3, 12px);
  }
  .lab__db--gone { border-color: var(--brick, #9b4a3f); background: var(--brick-wash, rgba(155, 74, 63, 0.06)); }
  .lab__db-label { font-family: var(--font-mono, monospace); font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--fg-light, #6b6b6b); }
  .lab__db-state { font-family: var(--font-mono, monospace); font-weight: 600; }
  .lab__db--gone .lab__db-state { color: var(--brick, #9b4a3f); }

  .lab__trace { list-style: none; margin: 0; padding: 0; }
  .lab__trace-row {
    display: grid;
    grid-template-columns: 24px auto 1fr;
    gap: 8px;
    align-items: baseline;
    padding: 5px 0;
    border-bottom: 1px dashed var(--fg-faint, #e8e8e8);
    font-size: 13px;
  }
  .lab__turn { font-family: var(--font-mono, monospace); color: var(--fg-light, #6b6b6b); font-size: 11px; }
  .lab__call { font-family: var(--font-mono, monospace); font-weight: 600; }
  .lab__note { color: var(--fg-light, #6b6b6b); font-size: 12px; }
  .lab__trace-row--blocked .lab__call, .lab__trace-row--halt .lab__call { color: var(--brick, #9b4a3f); }
  .lab__trace-row--executed .lab__call { color: var(--fg, #1a1a1a); }

  .lab__stop { margin-top: var(--space-3, 12px); font-size: 13px; color: var(--fg-light, #6b6b6b); }
  .lab__stop strong { color: var(--fg, #1a1a1a); }
  .lab__empty { color: var(--fg-light, #6b6b6b); font-size: 14px; line-height: 1.6; }
</style>
