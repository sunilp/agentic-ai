"""Tiny SVG kit for the governance guide's diagrams. Lab brand, 880px viewBox,
system font stacks (an SVG loaded through <img> cannot see the page's webfonts).
Every label goes through text(), which refuses em dashes and, given box=, text
wider than its box."""
import math

PAPER, INK, GREY, RULE, BRICK, TINT = '#fafaf8', '#1a1a1a', '#6b6b6b', '#e8e8e8', '#9b4a3f', '#f5ece9'
MONO = "'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace"
MONO_W = 0.605  # character width per unit of font size


class Svg:
    def __init__(self, w=880, h=300, title=''):
        self.w, self.h, self.title, self.parts = w, h, title, []

    def rect(self, x, y, w, h, fill='#fff', stroke=INK, sw=1):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def line(self, d, stroke=INK, sw=1, dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.parts.append(f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}"{da}/>')

    def arrow(self, x1, y1, x2, y2, stroke=INK):
        self.line(f'M{x1} {y1} L{x2} {y2}', stroke=stroke)
        a, L = math.atan2(y2 - y1, x2 - x1), 7
        p1 = (x2 - L * math.cos(a - 0.4), y2 - L * math.sin(a - 0.4))
        p2 = (x2 - L * math.cos(a + 0.4), y2 - L * math.sin(a + 0.4))
        self.parts.append(f'<path d="M{p1[0]:.1f} {p1[1]:.1f} L{x2} {y2} L{p2[0]:.1f} {p2[1]:.1f}" fill="none" stroke="{stroke}" stroke-width="1"/>')

    def text(self, x, y, s, size=12, fill=INK, anchor='start', weight=400, box=None):
        if chr(0x2014) in s:
            raise ValueError(f'em dash in label: {s}')
        if box is not None and len(s) * size * MONO_W > box:
            raise ValueError(f'"{s}" is {len(s) * size * MONO_W:.0f}px wide, box is {box}px')
        esc = s.replace('&', '&amp;').replace('<', '&lt;')
        self.parts.append(f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" xml:space="preserve">{esc}</text>')

    def box(self, x, y, w, h, title, sub='', brick=False):
        self.rect(x, y, w, h, fill=TINT if brick else '#fff', stroke=BRICK if brick else INK, sw=1.5 if brick else 1)
        cx = x + w / 2
        self.text(cx, y + (h / 2 - 2 if sub else h / 2 + 4), title, size=11, fill=BRICK if brick else INK, anchor='middle', weight=500, box=w - 16)
        if sub:
            self.text(cx, y + h / 2 + 13, sub, size=10, fill=GREY, anchor='middle', box=w - 16)

    def save(self, path):
        body = '\n'.join(self.parts)
        with open(path, 'w') as f:
            f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{self.title}">'
                    f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>\n{body}\n</svg>\n')
