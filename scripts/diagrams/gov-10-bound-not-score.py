import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, RULE, BRICK

ALT = ('Four evaluation runs against the T1 hallucination cap of 1%. Each shows its score as a dot '
       'and its 95% upper bound as the end of a bar. No failures in 200 cases: score 0%, bound 1.49%, fail. '
       'No failures in 300: bound 0.99%, pass. Four failures in 500: score 0.8%, bound 1.82%, fail. '
       'One failure in 500: score 0.2%, bound 0.95%, pass.')
s = Svg(880, 330, ALT)

# Plot area: 0% to 2% failure rate across x0..x1. The T1 cap sits at 1%.
X0, X1, MAX = 300, 780, 2.0
CAP = 1.0


def x(pct):
    return X0 + (X1 - X0) * pct / MAX


TOP, BOTTOM = 58, 262

# Recessive grid and axis.
for pct in (0, 0.5, 1.0, 1.5, 2.0):
    if pct != CAP:
        s.line(f'M{x(pct)} {TOP} L{x(pct)} {BOTTOM}', stroke=RULE)
    s.text(x(pct), BOTTOM + 16, f'{pct:g}%', size=10, fill=GREY, anchor='middle', box=40)
s.text((X0 + X1) / 2, BOTTOM + 32, 'failure rate', size=10, fill=GREY, anchor='middle', box=200)

# Column heads.
s.text(10, 30, 'RUN', size=10, fill=GREY, weight=500, box=100)
s.text(X1 + 75, 30, 'GATE', size=10, fill=GREY, weight=500, anchor='middle', box=60)

# The cap: the line the bound has to stay inside.
s.line(f'M{x(CAP)} {TOP - 16} L{x(CAP)} {BOTTOM}', stroke=BRICK, sw=1.5)
s.text(x(CAP), 30, 'T1 CAP 1%', size=10, fill=BRICK, weight=500, anchor='middle', box=120)

# Runs: label, sub-label, failures, n, score %, bound %.
runs = [
    ('0 failures in 200', 'score 0%', 0.0, 1.49),
    ('0 failures in 300', 'score 0% · the T1 minimum', 0.0, 0.99),
    ('4 failures in 500', 'first candidate · score 0.8%', 0.8, 1.82),
    ('1 failure in 500', 'candidate 2 · score 0.2%', 0.2, 0.95),
]
ROW0, STEP = 84, 52
for i, (label, sub, score, bound) in enumerate(runs):
    y = ROW0 + i * STEP
    s.text(10, y - 3, label, size=12, weight=500, box=270)
    s.text(10, y + 12, sub, size=10, fill=GREY, box=270)
    fails = bound > CAP
    # The interval from the score to the bound. Past the cap, it turns brick.
    inside_end = min(bound, CAP)
    s.line(f'M{x(score)} {y} L{x(inside_end)} {y}', stroke=INK, sw=2)
    if fails:
        s.line(f'M{x(CAP)} {y} L{x(bound)} {y}', stroke=BRICK, sw=2)
    end = BRICK if fails else INK
    s.line(f'M{x(bound)} {y - 7} L{x(bound)} {y + 7}', stroke=end, sw=2)
    s.text(x(bound) + 7, y + 4, f'{bound:.2f}%', size=10, fill=end, box=50)
    # The score: a dot with a white ring so it reads on top of the bar.
    s.parts.append(f'<circle cx="{x(score)}" cy="{y}" r="5" fill="{INK}" stroke="#fff" stroke-width="2"/>')
    s.text(X1 + 75, y + 4, 'FAIL' if fails else 'PASS', size=12, fill=BRICK if fails else INK,
           weight=500, anchor='middle', box=60)

# Legend.
LY = 314
s.parts.append(f'<circle cx="16" cy="{LY - 4}" r="5" fill="{INK}"/>')
s.text(28, LY, 'score: what the run measured', size=10, fill=GREY, box=220)
s.line(f'M300 {LY - 4} L330 {LY - 4}', stroke=INK, sw=2)
s.line(f'M330 {LY - 11} L330 {LY + 3}', stroke=INK, sw=2)
s.text(340, LY, 'end of bar: 95% upper bound, what the gate reads', size=10, fill=GREY, box=330)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-10-bound-not-score.svg'))
