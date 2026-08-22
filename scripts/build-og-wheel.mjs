#!/usr/bin/env node
/**
 * build-og-wheel.mjs — generates the LinkedIn/OG social card for the pattern
 * catalogue at /patterns/.
 *
 * The card is built FROM the catalogue, not hand-copied: it imports
 * `placeEntries()` from src/lib/pattern-wheel.ts (the same placement logic
 * PatternWheel.svelte renders) and `counts()` from src/data/pattern-language.ts,
 * so the wheel geometry, the layer/kind of every mark, and the "N patterns and
 * anti-patterns" line can never drift out of sync with the catalogue.
 *
 * Node's built-in TypeScript type-stripping (no flag needed since Node 22.18 /
 * 23.6+; this repo requires Node >=22 and this was verified on v26) loads the
 * two .ts source files directly. The only thing plain Node doesn't understand
 * is this project's '~/*' -> 'src/*' tsconfig path alias (Astro/Vite resolve
 * it, Node does not), so a small synchronous module hook remaps it before
 * handing back to Node's default resolver.
 *
 * Usage: node scripts/build-og-wheel.mjs
 * Output: public/assets/og/patterns.png (1200x630)
 * Requires: rsvg-convert on PATH (brew install librsvg).
 */

import { registerHooks } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync, writeFileSync, statSync } from 'node:fs';
import { execFileSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const rootURL = pathToFileURL(ROOT + '/').href;

// --- Resolve this project's '~/*' tsconfig path alias for plain Node -------
registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier.startsWith('~/')) {
      const rewritten = new URL(`src/${specifier.slice(2)}.ts`, rootURL).href;
      return nextResolve(rewritten, context);
    }
    return nextResolve(specifier, context);
  },
});

const { placeEntries, GEOMETRY, SECTORS } = await import(pathToFileURL(join(ROOT, 'src/lib/pattern-wheel.ts')).href);
const { counts } = await import(pathToFileURL(join(ROOT, 'src/data/pattern-language.ts')).href);

// --- Palette: exactly the on-site wheel (PatternWheel.svelte LAYER_COLOR) --
const LAYER_COLOR = {
  capability: '#205599',
  control: '#9b4a3f',
  evidence: '#b08d20',
};
const INK = '#1a1a1a';
const GREY = '#6b6b6b';
const SURFACE = '#fafaf8';
const RING_FAINT = '#e8e8e8';

const FONT_SERIF = "Georgia, 'Times New Roman', serif";
const FONT_MONO = "Menlo, Consolas, 'IBM Plex Mono', monospace";

// --- Canvas -----------------------------------------------------------------
const CARD_W = 1200;
const CARD_H = 630;

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// --- Wheel geometry: reproject the same placed marks onto the card ----------
// placeEntries() returns coordinates in the on-site 880x860 viewBox, centred
// on GEOMETRY.cx/cy with GEOMETRY.outerRadius. A circular figure can never
// exceed ~52.5% of a 1200-wide canvas while also filling its 630px height
// (630/1200 = 0.525 is the geometric ceiling at zero margin), so "55-60% of
// the width" describes the reserved right-hand region for the composition,
// not the circle's own diameter — the diameter itself is set by "fill the
// height with margin".
const marginY = 55;
const wheelDiameter = CARD_H - marginY * 2; // 520
const scale = wheelDiameter / (GEOMETRY.outerRadius * 2);
const rightMargin = 40;
const wheelCx = CARD_W - rightMargin - wheelDiameter / 2;
const wheelCy = CARD_H / 2;

function toCanvas(x, y) {
  return {
    x: wheelCx + (x - GEOMETRY.cx) * scale,
    y: wheelCy + (y - GEOMETRY.cy) * scale,
  };
}

function polarToXY(cx, cy, r, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

const placed = placeEntries();

let wheelMarks = '';

// Ring boundary circles: 6 radii (innerRadius + ringWidth*0..5). Innermost and
// outermost rings drawn ink/edge, the rest faint — same treatment as the site.
const ringCount = 5; // RINGS.length, but avoid importing RINGS just for a constant already implied by GEOMETRY
for (let i = 0; i <= ringCount; i++) {
  const r = (GEOMETRY.innerRadius + GEOMETRY.ringWidth * i) * scale;
  const isEdge = i === 0 || i === ringCount;
  wheelMarks += `<circle cx="${wheelCx}" cy="${wheelCy}" r="${r.toFixed(2)}" fill="none" stroke="${isEdge ? INK : RING_FAINT}" stroke-width="1" opacity="${isEdge ? 0.55 : 1}" />\n`;
}

// Sector divider lines at the three 120-degree boundaries (0/120/240 degrees,
// matching sectorBounds()'s convention of sector 0 starting due east).
for (const angle of [0, 120, 240]) {
  const inner = polarToXY(GEOMETRY.cx, GEOMETRY.cy, GEOMETRY.innerRadius, angle);
  const outer = polarToXY(GEOMETRY.cx, GEOMETRY.cy, GEOMETRY.outerRadius, angle);
  const p1 = toCanvas(inner.x, inner.y);
  const p2 = toCanvas(outer.x, outer.y);
  wheelMarks += `<line x1="${p1.x.toFixed(2)}" y1="${p1.y.toFixed(2)}" x2="${p2.x.toFixed(2)}" y2="${p2.y.toFixed(2)}" stroke="${RING_FAINT}" stroke-width="1" />\n`;
}

// Marks: circles for patterns, diamonds for anti-patterns, filled by layer.
// No numerals -- unreadable at feed size and there is no list on this card to
// key them to; this is the one rendering of the wheel that is marks only.
const MARK_R = 9.5 * scale;
for (const p of placed) {
  const { x, y } = toCanvas(p.x, p.y);
  const fill = LAYER_COLOR[p.layer];
  if (p.kind === 'anti-pattern') {
    const r = MARK_R;
    const d = `M ${x.toFixed(2)} ${(y - r).toFixed(2)} L ${(x + r).toFixed(2)} ${y.toFixed(2)} L ${x.toFixed(2)} ${(y + r).toFixed(2)} L ${(x - r).toFixed(2)} ${y.toFixed(2)} Z`;
    wheelMarks += `<path d="${d}" fill="${fill}" stroke="${INK}" stroke-width="1" />\n`;
  } else {
    wheelMarks += `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="${MARK_R.toFixed(2)}" fill="${fill}" stroke="${INK}" stroke-width="1" />\n`;
  }
}

// --- Left column: eyebrow, title, dek line (derived from counts()), legend --
const c = counts();
const dekLines = [`${c.total} patterns and anti-patterns`,
                  'across capability, control and evidence'];

const LEFT_X = 64;
// Fixed title (not catalogue-derived), hand-wrapped to two lines that fit
// comfortably left of the wheel at the sizes/positions below -- verified
// visually at both full size and shrunk to feed width; re-check by eye if
// this string is ever edited.
const titleLines = ['A Pattern Language', 'for Agentic Systems'];
const TITLE_SIZE = 52;
const TITLE_LINE_H = 60;
const titleTop = 262;

let leftSvg = '';
leftSvg += `<text x="${LEFT_X}" y="130" font-family="${FONT_MONO}" font-size="22" letter-spacing="3" fill="${GREY}">AGENT ENGINEERING LAB</text>\n`;

titleLines.forEach((line, i) => {
  leftSvg += `<text x="${LEFT_X}" y="${titleTop + i * TITLE_LINE_H}" font-family="${FONT_SERIF}" font-size="${TITLE_SIZE}" font-weight="700" fill="${INK}">${esc(line)}</text>\n`;
});

const DEK_SIZE = 25;
const DEK_LINE_H = 34;
const dekTop = titleTop + titleLines.length * TITLE_LINE_H + 44;
dekLines.forEach((line, i) => {
  leftSvg += `<text x="${LEFT_X}" y="${dekTop + i * DEK_LINE_H}" font-family="${FONT_SERIF}" font-size="${DEK_SIZE}" fill="${GREY}">${esc(line)}</text>\n`;
});
const dekY = dekTop + (dekLines.length - 1) * DEK_LINE_H;

// Legend: one row per layer, swatch + mono label, stacked with generous gaps.
const legendY = dekY + 48;
const legendGap = 34;
let legendSvg = '';
SECTORS.forEach((layer, i) => {
  const y = legendY + i * legendGap;
  legendSvg += `<circle cx="${LEFT_X + 8}" cy="${y - 7}" r="8" fill="${LAYER_COLOR[layer]}" />\n`;
  legendSvg += `<text x="${LEFT_X + 26}" y="${y}" font-family="${FONT_MONO}" font-size="21" letter-spacing="1.5" fill="${INK}">${layer.toUpperCase()}</text>\n`;
});

// --- Assemble ---------------------------------------------------------------
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${CARD_W}" height="${CARD_H}" viewBox="0 0 ${CARD_W} ${CARD_H}">
  <rect x="0" y="0" width="${CARD_W}" height="${CARD_H}" fill="${SURFACE}" />
  <g id="card-text">
${leftSvg}${legendSvg}  </g>
  <g id="card-wheel" data-cx="${wheelCx}" data-cy="${wheelCy}" data-r="${(GEOMETRY.outerRadius * scale).toFixed(2)}">
${wheelMarks}  </g>
</svg>
`;

const outDir = join(ROOT, 'public/assets/og');
mkdirSync(outDir, { recursive: true });
const svgPath = join(outDir, 'patterns.svg');
const pngPath = join(outDir, 'patterns.png');
writeFileSync(svgPath, svg, 'utf8');

execFileSync('rsvg-convert', ['-w', String(CARD_W), '-h', String(CARD_H), '-o', pngPath, svgPath], { stdio: 'inherit' });

const { size } = statSync(pngPath);
console.log(`Wrote ${pngPath} (${size} bytes) from ${placed.length} placed entries, ${c.total} total (dek: "${dekLines.join(' ')}")`);
