import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, RULE, BRICK, TINT

# Made-up counts for the framework's credit scoring model: 1,000 applicants in each group,
# one model, one cutoff. It approves 90% of those who would repay and 30% of those who would
# default, in both groups. Every figure is recomputed in NOTES/returns/step-13.md.
A = dict(repay=900, default=100, repay_ok=810, default_ok=30)
B = dict(repay=750, default=250, repay_ok=675, default_ok=75)


def rates(g):
    approved = g['repay_ok'] + g['default_ok']
    return dict(
        base=100 * g['repay'] / 1000,
        declined=100 * (g['repay'] - g['repay_ok']) / g['repay'],
        let_in=100 * g['default_ok'] / g['default'],
        ppv=100 * g['repay_ok'] / approved,
        selection=100 * approved / 1000,
    )


ra, rb = rates(A), rates(B)
assert ra['declined'] == rb['declined'] == 10 and ra['let_in'] == rb['let_in'] == 30
assert round(ra['ppv'], 1) == 96.4 and rb['ppv'] == 90 and ra['selection'] == 84 and rb['selection'] == 75

ALT = ('One credit model, one cutoff, made-up counts for two groups of 1,000 applicants. '
       'The base rates differ: 900 would repay in group A and 750 in group B. '
       'Error rates are level: 10% of the people who would repay are declined in both groups, '
       'and 30% of the people who would default are approved in both. '
       'Predictive value is apart: 96% of approvals are repaid in A against 90% in B. '
       'Selection rates are apart: 84% of A is approved against 75% of B. '
       'Level the error rates and the other two come apart. Even a perfect model approves 90% of A and 75% of B.')
s = Svg(880, 428, ALT)

X0, X1 = 330, 690          # 0% to 100%
VERDICT_X = 800            # centre of the right-hand column


def x(pct):
    return X0 + (X1 - X0) * pct / 100


TOP, ROW0, STEP = 64, 92, 56
rows = [
    # key, title, sub-label
    ('base', 'Would repay', 'the base rate · 900 and 750 of 1,000'),
    ('declined', 'Error rate: good applicants declined', 'of those who would repay · 90 of 900, 75 of 750'),
    ('let_in', 'Error rate: defaulters approved', 'of those who would default · 30 of 100, 75 of 250'),
    ('ppv', 'Predictive value', 'approvals that are repaid · 810 of 840, 675 of 750'),
    ('selection', 'Selection rate', 'applicants approved · 840 and 750 of 1,000'),
]
BOTTOM = ROW0 + (len(rows) - 1) * STEP + 24

# The cause row sits on a tint band, set apart from the three metrics it drives.
s.rect(4, ROW0 - 24, 872, 48, fill=TINT, stroke=TINT)

# Recessive grid and axis.
for pct in (0, 25, 50, 75, 100):
    s.line(f'M{x(pct)} {TOP} L{x(pct)} {BOTTOM}', stroke=RULE)
    s.text(x(pct), BOTTOM + 16, f'{pct}%', size=10, fill=GREY, anchor='middle', box=40)

# Column heads and legend.
s.text(10, 30, 'Same model, same cutoff, two groups', size=11, weight=500, box=310)
s.text(10, 46, '1,000 applicants in each · counts made up', size=10, fill=GREY, box=310)
s.parts.append(f'<circle cx="{X0 + 6}" cy="26" r="5" fill="{INK}"/>')
s.text(X0 + 18, 30, 'group A', size=10, fill=GREY, box=70)
s.parts.append(f'<circle cx="{X0 + 106}" cy="26" r="5" fill="#fff" stroke="{BRICK}" stroke-width="2"/>')
s.text(X0 + 118, 30, 'group B', size=10, fill=GREY, box=70)
s.text(VERDICT_X, 30, 'A against B', size=10, fill=GREY, weight=500, anchor='middle', box=110)


def dot_a(cx, cy):
    s.parts.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="5" fill="{INK}" stroke="#fff" stroke-width="1.5"/>')


def ring_b(cx, cy):
    s.parts.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="7" fill="none" stroke="{BRICK}" stroke-width="2"/>')


for i, (key, title, sub) in enumerate(rows):
    y = ROW0 + i * STEP
    s.text(10, y - 3, title, size=12, weight=500, fill=BRICK if key == 'base' else INK, box=320)
    s.text(10, y + 12, sub, size=10, fill=GREY, box=320)
    a, b = ra[key], rb[key]
    if abs(a - b) < 0.05:
        # Level: the ring sits around the dot.
        ring_b(x(b), y)
        dot_a(x(a), y)
        s.text(x(a) + 14, y + 4, f'{a:.0f}% in both', size=10, fill=INK, box=110)
        s.text(VERDICT_X, y + 4, 'level', size=12, weight=500, anchor='middle', box=110)
    else:
        lo, hi = min(a, b), max(a, b)
        s.line(f'M{x(lo)} {y} L{x(hi)} {y}', stroke=BRICK if key != 'base' else INK, sw=2)
        ring_b(x(b), y)
        dot_a(x(a), y)
        # B sits left of A in every apart row: label B on the left, A on the right.
        assert b < a
        s.text(x(b) - 12, y + 4, f'{b:.0f}%', size=10, fill=BRICK, anchor='end', box=40)
        s.text(x(a) + 12, y + 4, f'{a:.0f}%', size=10, fill=INK, box=40)
        verdict = f'{a - b:.0f} points apart'
        s.text(VERDICT_X, y + 4, verdict, size=12, weight=500, anchor='middle',
               fill=GREY if key == 'base' else BRICK, box=118)

# What it adds up to.
NY = BOTTOM + 44
s.text(10, NY, 'Level the error rates and the other two come apart. Level either of the others and the error rates split.',
       size=11, box=860)
s.text(10, NY + 20, 'Even a perfect model approves 90% of A and 75% of B, because that is how many would repay.',
       size=11, fill=GREY, box=860)
assert NY + 20 <= s.h - 10, 'notes leave the frame'

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-13-three-metrics.svg'))
