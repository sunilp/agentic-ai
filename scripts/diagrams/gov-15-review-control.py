import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, GREY, BRICK, RULE, INK

ALT = ('What a reviewer needs for a review to be a control. Four conditions mean reviewers can overrule the system: '
       'the decision, one question written down; the evidence, in view beside the output; the time, a cap per shift; '
       'and the authority to say no at no cost. The fifth, the test, planted errors that get caught, shows that they '
       'sometimes do. Without each one: the reviewer checks how it reads, an error that looks right goes out, rare errors '
       'slip by late in a session, yes becomes the quick answer, and a check and a stamp look the same.')
s = Svg(880, 262, ALT)

# Five conditions, left to right. The test is the step's call, so it is the one brick box.
conds = [
    ('THE DECISION', 'one question, written', ('the reviewer checks', 'how it reads')),
    ('THE EVIDENCE', 'in view, beside it', ('an error that looks', 'right goes out')),
    ('THE TIME', 'a cap per shift', ('rare errors slip by', 'late in a session')),
    ('THE AUTHORITY', 'to say no, at no cost', ('yes becomes the', 'quick answer')),
    ('THE TEST', 'planted errors, caught', ('a check and a stamp', 'look the same')),
]
BW, GAP, X0 = 152, 20, 20
ROW_Y, ROW_H = 60, 56
xs = [X0 + i * (BW + GAP) for i in range(len(conds))]  # last box ends at 860
assert xs[-1] + BW <= s.w - 16, 'row leaves the frame'

# Brackets: the first four let reviewers overrule; the test shows they do.
BR_Y = 44


def bracket(x1, x2, label, colour):
    s.line(f'M{x1} {BR_Y + 8} L{x1} {BR_Y} L{x2} {BR_Y} L{x2} {BR_Y + 8}', stroke=colour)
    s.text((x1 + x2) / 2, BR_Y - 10, label, size=11, fill=colour, anchor='middle', weight=500, box=x2 - x1 - 8)


bracket(xs[0], xs[3] + BW, 'reviewers can overrule the system', INK)
bracket(xs[4], xs[4] + BW, 'and sometimes do', BRICK)

for (title, sub, _), x in zip(conds, xs):
    s.box(x, ROW_Y, BW, ROW_H, title, sub, brick=(title == 'THE TEST'))

# What the review turns into when a condition is missing.
LBL_Y = 152
s.text(X0, LBL_Y, 'WITHOUT IT', size=10, fill=GREY, weight=500, box=200)
s.line(f'M{X0} {LBL_Y + 6} L{xs[-1] + BW} {LBL_Y + 6}', stroke=RULE)
for (title, _, (l1, l2)), x in zip(conds, xs):
    cx = x + BW / 2
    s.line(f'M{cx} {ROW_Y + ROW_H} L{cx} {LBL_Y - 16}', stroke=GREY)
    colour = BRICK if title == 'THE TEST' else INK
    s.text(cx, LBL_Y + 26, l1, size=11, fill=colour, anchor='middle', box=BW + GAP - 6)
    s.text(cx, LBL_Y + 42, l2, size=11, fill=colour, anchor='middle', box=BW + GAP - 6)

# The point, once, in brick.
s.parts.append(f'<circle cx="{X0 + 4}" cy="236" r="4.5" fill="{BRICK}"/>')
s.text(X0 + 16, 240, 'The first four make a no possible. Only the test shows one happening.', size=12, fill=BRICK, box=820)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-15-review-control.svg'))
