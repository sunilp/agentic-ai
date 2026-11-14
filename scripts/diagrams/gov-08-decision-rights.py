import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, BRICK, TINT, MONO_W

ALT = ('Who decides, by tier. Four rows across T1 to T4. Build, meaning approve the risk assessment: '
       'AI Risk Committee, AI Risk, team lead, team lead. Validate: MRM in full, MRM or another second-line '
       'reviewer in reduced scope, a peer who is not the developer, a self-test. Ship: AI Risk Committee with '
       'the CISO and, for personal data, the DPO; Head of AI with the Business Unit Head; team lead with the '
       'business owner; team lead. Exception: AI Risk Committee, Head of AI Risk, Head of AI, team lead. '
       'Cells decided outside the build team are shaded: every T1 and T2 cell, and the T3 exception. '
       'Two rows apply at every tier: a material change goes back to the ship approver after revalidation, and '
       'whoever is on call can stop a system first and tell the owners after.')
s = Svg(880, 482, ALT)

LABEL_X, LABEL_W = 10, 120
COL_X0, COL_W, COL_GAP = 136, 178, 4
cols = [COL_X0 + i * (COL_W + COL_GAP) for i in range(4)]  # 136, 318, 500, 682; last ends at 860
RIGHT = cols[-1] + COL_W
assert RIGHT <= s.w - 10, 'columns leave the frame'


def cell(x, y, w, h, title, subs=(), brick=False):
    """A table cell: one title line and up to two grey lines, centred as a block."""
    s.rect(x, y, w, h, fill=TINT if brick else '#fff', stroke=BRICK if brick else INK, sw=1.5 if brick else 1)
    lines = [(title, 11, BRICK if brick else INK, 500)] + [(t, 10, GREY, 400) for t in subs]
    step = 14
    top = y + h / 2 - (len(lines) - 1) * step / 2 + 4
    for i, (t, size, fill, weight) in enumerate(lines):
        s.text(x + w / 2, top + i * step, t, size=size, fill=fill, anchor='middle', weight=weight, box=w - 14)


def row_label(y, h, title, sub):
    s.text(LABEL_X, y + h / 2 - 2, title, size=11, weight=500, box=LABEL_W)
    s.text(LABEL_X, y + h / 2 + 13, sub, size=10, fill=GREY, box=LABEL_W)


# The two high-risk tiers, bracketed.
bx1, bx2 = cols[0], cols[1] + COL_W
s.line(f'M{bx1} 34 L{bx1} 28 L{bx2} 28 L{bx2} 34', stroke=BRICK, sw=1.2)
s.text((bx1 + bx2) / 2, 20, 'HIGH-RISK · THE BUILD TEAM NEVER VALIDATES', size=10, fill=BRICK, anchor='middle', weight=500, box=bx2 - bx1)

# Column headers.
for x, head in zip(cols, ['T1 · CRITICAL', 'T2 · HIGH', 'T3 · MEDIUM', 'T4 · LOW']):
    s.text(x + COL_W / 2, 52, head, size=11, anchor='middle', weight=500, box=COL_W)

# Four decisions whose owner changes with the tier. True means decided outside the build team.
ROW_Y0, ROW_H, ROW_GAP = 62, 60, 6
rows = [
    ('BUILD', 'risk assessment', [
        ('AI Risk Committee', ['MRM checks the tier'], True),
        ('AI Risk', ['second line'], True),
        ('Team lead', [], False),
        ('Team lead', ['acknowledges the', 'self-assessment'], False)]),
    ('VALIDATE', 'independent check', [
        ('MRM', ['full scope'], True),
        ('MRM or second line', ['reduced scope'], True),
        ('Peer review', ['not the developer'], False),
        ('Self-test', ['by the developer'], False)]),
    ('SHIP', 'deployment', [
        ('AI Risk Committee', ['CISO co-signs', 'DPO too, if personal data'], True),
        ('Head of AI', ['Business Unit Head', 'co-signs'], True),
        ('Team lead', ['business owner co-signs'], False),
        ('Team lead', [], False)]),
    ('EXCEPTION', 'to a control', [
        ('AI Risk Committee', [], True),
        ('Head of AI Risk', [], True),
        ('Head of AI', [], True),
        ('Team lead', [], False)]),
]
for r, (label, sub, cells) in enumerate(rows):
    y = ROW_Y0 + r * (ROW_H + ROW_GAP)
    row_label(y, ROW_H, label, sub)
    for x, (title, subs, outside) in zip(cols, cells):
        cell(x, y, COL_W, ROW_H, title, subs, brick=outside)
grid_bottom = ROW_Y0 + 4 * ROW_H + 3 * ROW_GAP  # 320

# Two decisions that sit with the same people at every tier.
s.text(cols[0], grid_bottom + 24, 'AT EVERY TIER', size=10, fill=GREY, weight=500, box=200)
SPAN_H = 40
span = [
    ('CHANGE', 'material change', 'The ship approver signs again, after revalidation. A higher tier brings its own approvers.'),
    ('STOP', 'pause it now', 'Whoever is on call can stop it first. The owners hear after.'),
]
for i, (label, sub, line) in enumerate(span):
    y = grid_bottom + 32 + i * (SPAN_H + ROW_GAP)
    row_label(y, SPAN_H, label, sub)
    s.rect(cols[0], y, RIGHT - cols[0], SPAN_H)
    s.text(cols[0] + 14, y + SPAN_H / 2 + 4, line, size=11, box=RIGHT - cols[0] - 28)
span_bottom = grid_bottom + 32 + 2 * SPAN_H + ROW_GAP  # 438

# Legend.
LY = span_bottom + 22
s.rect(cols[0], LY, 28, 14, fill=TINT, stroke=BRICK, sw=1.5)
s.text(cols[0] + 38, LY + 11, 'decided outside the build team', size=10, fill=GREY, box=220)
s.rect(cols[2], LY, 28, 14)
s.text(cols[2] + 38, LY + 11, 'decided inside the team', size=10, fill=GREY, box=220)
assert LY + 14 <= s.h - 6, 'legend leaves the frame'

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-08-decision-rights.svg'))
