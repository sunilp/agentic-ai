/**
 * Count-up animation for evidence numbers.
 * Triggered via IntersectionObserver. One-shot per element.
 * Respects prefers-reduced-motion: snaps to final value instantly.
 */
import { animate } from 'motion';

interface CountUpOptions {
  to: number;
  duration?: number;
  decimals?: number;
  suffix?: string;
}

export function startCountUp(el: HTMLElement, opts: CountUpOptions): void {
  const { to, duration = 0.8, decimals = 1, suffix = '' } = opts;
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (prefersReduced) {
    el.textContent = to.toFixed(decimals) + suffix;
    return;
  }

  animate(0, to, {
    duration,
    ease: [0.2, 0.8, 0.2, 1],
    onUpdate: (value) => {
      el.textContent = value.toFixed(decimals) + suffix;
    },
  });
}

/**
 * Observe a NodeList of count-up targets and trigger on viewport entry.
 * Each element must have `data-count-to`, optional `data-count-decimals`, `data-count-suffix`.
 *
 * Returns an IntersectionObserver so the caller can disconnect it before
 * re-initializing on View Transition navigation. Without this, observers
 * accumulate across navigations and leak memory.
 */
export function observeCountUps(selector = '[data-count-to]'): IntersectionObserver | null {
  const targets = document.querySelectorAll<HTMLElement>(selector);
  if (!targets.length) return null;

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      const el = entry.target as HTMLElement;
      const to = parseFloat(el.dataset.countTo || '0');
      const decimals = parseInt(el.dataset.countDecimals || '1', 10);
      const suffix = el.dataset.countSuffix || '';
      startCountUp(el, { to, decimals, suffix });
      observer.unobserve(el);
    }
  }, { threshold: 0.5 });

  targets.forEach((el) => observer.observe(el));
  return observer;
}
