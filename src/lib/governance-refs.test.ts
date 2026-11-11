import { describe, it, expect } from 'vitest';
import { renderRefs } from './governance-refs';

describe('renderRefs', () => {
  it('links written steps and leaves the rest as text', () => {
    const out = renderRefs([3, ' · ', 4], (n) => (n === 3 ? '/governance/03-list-every-ai-system/' : null));
    expect(out).toBe('<a href="/governance/03-list-every-ai-system/"><tspan class="ref ref--link">3</tspan></a><tspan> · </tspan><tspan class="ref">4</tspan>');
  });

  it('escapes text', () => {
    expect(renderRefs(['a < b'], () => null)).toBe('<tspan>a &lt; b</tspan>');
  });
});
