<script lang="ts">
  /**
   * The governance machine plus its panel. One component for both uses:
   * static on step pages (no client directive, zero JS) and interactive on the hub
   * (client:visible interactive). The drawing comes from renderMachineSvg, which is
   * unit-tested, so this file only wires selection.
   */
  import { tick } from 'svelte';
  import '~/styles/governance-machine.css';
  import { renderMachineSvg, type MachineMode } from '~/lib/machine-svg';
  import { panelFor } from '~/lib/machine-panel';
  import { writtenHref } from '~/data/governance-path';

  interface Props { initial: number; mode: MachineMode; written: string[]; interactive?: boolean }
  let { initial, mode, written, interactive = false }: Props = $props();

  let selected = $state(initial);
  let drawing: HTMLDivElement | undefined = $state();
  const writtenSet = $derived(new Set(written));
  const href = $derived(writtenHref(writtenSet));
  const svg = $derived(renderMachineSvg({ selected, mode, href, interactive }));
  const panel = $derived(panelFor(selected, writtenSet));

  async function pick(target: EventTarget | null, restoreFocus: boolean) {
    const node = (target as Element | null)?.closest?.('[data-step]');
    if (!node) return;
    selected = Number(node.getAttribute('data-step'));
    if (restoreFocus) {
      await tick();
      drawing?.querySelector<SVGGElement>(`[data-step="${selected}"]`)?.focus();
    }
  }
  function onclick(e: MouseEvent) {
    if (interactive) pick(e.target, true);
  }
  function onkeydown(e: KeyboardEvent) {
    if (interactive && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      pick(e.target, true);
    }
  }
</script>

<div class="machine-figure__grid">
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="machine-figure__drawing" bind:this={drawing} {onclick} {onkeydown}>{@html svg}</div>
  <aside class="machine-panel" aria-live="polite">
    <p class="machine-panel__k">Step {panel.n}</p>
    <p class="machine-panel__t">{#if panel.href}<a href={panel.href}>{panel.title}</a>{:else}{panel.title}{/if}</p>
    <p class="machine-panel__k">Rests on</p>
    <p class="machine-panel__l">
      {#if panel.restsOn.length === 0}Nothing. This is where you start.{:else}{#each panel.restsOn as r, i}{#if i > 0} · {/if}{#if r.href}<a href={r.href}>{r.n} {r.short}</a>{:else}{r.n} {r.short}{/if}{/each}{/if}
    </p>
    <p class="machine-panel__k">Holds up</p>
    <p class="machine-panel__l">
      {#if panel.holdsUp.length === 0}Step 22, the walk-through{:else}{#each panel.holdsUp as r, i}{#if i > 0} · {/if}{#if r.href}<a href={r.href}>{r.n} {r.short}</a>{:else}{r.n} {r.short}{/if}{/each}{/if}
    </p>
    {#if panel.patterns.length > 0}
      <p class="machine-panel__k">Patterns in play</p>
      <ul class="machine-panel__chips">
        {#each panel.patterns as p (p.slug)}
          <li>
            <span class="chip" class:chip--anti={p.anti} style={`background:${p.colour}`}></span>
            <a href={p.href}>{p.name}</a>{#if p.anti}<span class="machine-panel__anti">&nbsp;(anti-pattern)</span>{/if}
          </li>
        {/each}
      </ul>
    {/if}
    {#if interactive && panel.href}
      <p class="machine-panel__open"><a href={panel.href}>Open step {panel.n} →</a></p>
    {/if}
  </aside>
</div>
