/**
 * The book: which chapters are free to read on the site, and what a book-only
 * chapter's preview says. One place, so the Book index, the chapter pages and
 * the chapter map agree.
 */
export const BOOK_TITLE = 'Agentic AI for Serious Engineers';
export const AMAZON_URL = 'https://www.amazon.com/dp/B0GVG6848F';
export const CODE_REPO = 'https://github.com/sunilp/agentic-ai';

/** A chapter is free when its full text is on the site. Book-only chapters are stored as drafts holding a preview. */
export const isFree = (c: { data: { status?: string } }): boolean => c.data.status !== 'draft';

/** '02-tools-context-agent-loop' -> '02'; '00a-how-llms-work' -> '00a'. */
export const chapterNumber = (id: string): string => id.match(/^(\d+[a-z]?)/)?.[1] ?? id;

export interface PreviewPoint { title: string; text: string }
export interface ChapterPreview { points: PreviewPoint[]; code?: { href: string; label: string } }

const section = (body: string, heading: string): string => {
  const start = body.indexOf(`## ${heading}`);
  if (start < 0) return '';
  const rest = body.slice(start + heading.length + 3);
  const end = rest.search(/\n## /);
  return end < 0 ? rest : rest.slice(0, end);
};

/**
 * Read a book-only chapter's preview from its Markdown body: the bullets under
 * "What this chapter covers" and the first link under "Code companion".
 * A preview without those sections returns no points and no code.
 */
export function parsePreview(body: string): ChapterPreview {
  const points = [...section(body, 'What this chapter covers').matchAll(/^- \*\*(.+?)\*\*\s*(?:--|:)?\s*(.*)$/gm)].map((m) => ({
    title: m[1].trim(),
    text: m[2].trim(),
  }));
  const link = section(body, 'Code companion').match(/\[`?([^\]`]+)`?\]\((https?:[^)]+)\)/);
  return { points, code: link ? { label: link[1], href: link[2] } : undefined };
}
