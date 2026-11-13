/**
 * The in-page contents list for a governance step, built from the essay's own
 * h2 headings so the rail always matches the page. The Deep dive heading lives
 * in a component, so it is added by hand when the essay has one.
 */
export interface Anchor { label: string; anchor: string }
interface Heading { depth: number; slug: string; text: string }

export function stepAnchors(headings: Heading[], body = ''): Anchor[] {
  const anchors = headings.filter((h) => h.depth === 2).map((h) => ({ label: h.text, anchor: h.slug }));
  if (body.includes('<DeepDive>')) anchors.push({ label: 'Deep dive', anchor: 'deep-dive' });
  return anchors;
}
