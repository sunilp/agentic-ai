import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, BRICK, TINT

ALT = ('The four moving parts of a GenAI system, each with a version and the route a change takes. '
       'Model: a pinned, dated version, never a latest alias; the vendor retires or updates it; the change is '
       'material: re-tier, full suite, MRM, the signers. Prompt: major.minor, changed by a pull request; the reviewer '
       'decides which: a major version is material, a minor version takes peer review and the suite still runs. '
       'Sources: an index build and each page version, changed by a page owner; the suite re-runs with expected '
       'answers checked and permissions re-tested. Vendor: the contract and assessment; new terms or a sub-processor '
       'bring a contract re-check, and a new provider is material. Every change: a new version, the suite before '
       'release, a line in the release record and a rollback to the last approved version.')
s = Svg(880, 486, ALT)

LABEL_X, LABEL_W = 10, 120
COL_X0, COL_W, COL_GAP = 136, 178, 4
cols = [COL_X0 + i * (COL_W + COL_GAP) for i in range(4)]  # 136, 318, 500, 682; last ends at 860
RIGHT = cols[-1] + COL_W
assert RIGHT <= s.w - 10, 'columns leave the frame'


def cell(x, y, w, h, title, subs=(), brick=False):
    """One title line and up to two grey lines, centred as a block."""
    s.rect(x, y, w, h, fill=TINT if brick else '#fff', stroke=BRICK if brick else INK, sw=1.5 if brick else 1)
    lines = [(title, 11, BRICK if brick else INK, 500)] + [(t, 10, GREY, 400) for t in subs]
    step = 14
    top = y + h / 2 - (len(lines) - 1) * step / 2 + 4
    for i, (t, size, fill, weight) in enumerate(lines):
        s.text(x + w / 2, top + i * step, t, size=size, fill=fill, anchor='middle', weight=weight, box=w - 14)


def row_label(y, h, title, sub):
    s.text(LABEL_X, y + h / 2 - 2, title, size=11, weight=500, box=LABEL_W)
    s.text(LABEL_X, y + h / 2 + 13, sub, size=10, fill=GREY, box=LABEL_W)


# Column heads: the four parts that move.
s.text(LABEL_X, 30, 'MOVING PART', size=10, fill=GREY, weight=500, box=LABEL_W)
heads = [('MODEL', 'the vendor serves it'), ('PROMPT', 'your team writes it'),
         ('SOURCES', 'other teams edit them'), ('VENDOR', 'the contract behind it')]
for x, (head, sub) in zip(cols, heads):
    s.text(x + COL_W / 2, 26, head, size=12, anchor='middle', weight=500, box=COL_W)
    s.text(x + COL_W / 2, 42, sub, size=10, fill=GREY, anchor='middle', box=COL_W - 8)

# Two rows that describe each part: what its version is, and who changes it.
ROW_Y0, ROW_H, ROW_GAP = 56, 48, 6
rows = [
    ('VERSION', 'what you record', [
        ('pinned, dated ID', ['never a latest alias']),
        ('major.minor', ['no unversioned change']),
        ('index build', ['and each page version']),
        ('contract, assessment', ['checked at renewal'])]),
    ('CHANGED BY', 'who moves it', [
        ('the vendor', ['retires or updates it']),
        ('a pull request', ['from your own team']),
        ('a page owner', ['fees, dates, terms']),
        ('new terms', ['or a new sub-processor'])]),
]
for r, (label, sub, cells) in enumerate(rows):
    y = ROW_Y0 + r * (ROW_H + ROW_GAP)
    row_label(y, ROW_H, label, sub)
    for x, (title, subs) in zip(cols, cells):
        cell(x, y, COL_W, ROW_H, title, subs)

# The route a change takes. Brick is the material route: re-tier, full suite, MRM, signers.
ROUTE_Y = ROW_Y0 + 2 * (ROW_H + ROW_GAP)  # 164
ROUTE_H = 124
row_label(ROUTE_Y, ROUTE_H, 'ROUTE', 'what a change takes')
cell(cols[0], ROUTE_Y, COL_W, ROUTE_H, 'material change', ['re-tier · full suite', 'MRM · the signers'], brick=True)
HALF = (ROUTE_H - 6) / 2
cell(cols[1], ROUTE_Y, COL_W, HALF, 'major · material', ['same route as a model'], brick=True)
cell(cols[1], ROUTE_Y + HALF + 6, COL_W, HALF, 'minor · peer review', ['the suite still runs'])
cell(cols[2], ROUTE_Y, COL_W, ROUTE_H, 'suite re-runs', ['expected answers checked', 'permissions re-tested'])
cell(cols[3], ROUTE_Y, COL_W, HALF, 'contract re-check', ['region, retention, DPA'])
cell(cols[3], ROUTE_Y + HALF + 6, COL_W, HALF, 'new provider', ['material, like a model'], brick=True)
route_bottom = ROUTE_Y + ROUTE_H  # 288

# Who decides between the prompt's two routes.
s.text(cols[1] + COL_W / 2, route_bottom + 18, 'the reviewer decides which', size=10, fill=BRICK,
       anchor='middle', weight=500, box=COL_W)

# What every change shares, whatever the part.
SPAN_Y, SPAN_H = route_bottom + 34, 48
row_label(SPAN_Y, SPAN_H, 'EVERY CHANGE', 'any part')
s.rect(cols[0], SPAN_Y, RIGHT - cols[0], SPAN_H)
s.text(cols[0] + 14, SPAN_Y + 20, 'A new version, the suite before release, a new line in the release record,',
       size=11, box=RIGHT - cols[0] - 28)
s.text(cols[0] + 14, SPAN_Y + 36, 'and a rollback to the last approved version.', size=11, box=RIGHT - cols[0] - 28)
span_bottom = SPAN_Y + SPAN_H  # 370

# Legend.
LY = span_bottom + 22
s.rect(cols[0], LY, 28, 14, fill=TINT, stroke=BRICK, sw=1.5)
s.text(cols[0] + 38, LY + 11, 'material: revalidation, then the signers', size=10, fill=GREY, box=300)
s.rect(cols[2], LY, 28, 14)
s.text(cols[2] + 38, LY + 11, 'reviewed and tested, no revalidation', size=10, fill=GREY, box=300)

# The point, once, in brick.
PY = LY + 52
s.parts.append(f'<circle cx="16" cy="{PY - 4}" r="4.5" fill="{BRICK}"/>')
s.text(28, PY, 'The release record names one version of each part, and the evidence that passed them together.',
       size=12, fill=BRICK, box=840)
assert PY + 8 <= s.h, 'last line leaves the frame'

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-17-four-moving-parts.svg'))
