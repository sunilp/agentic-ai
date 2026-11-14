import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, RULE, BRICK, TINT

ALT = ('Three kinds of failure, each with a limit signed before the run and judged against that limit alone. '
       'Wrong output: the T1 hallucination cap, a bound of at most 1%, set by the framework. The run found '
       '1 failure in 500, bound 0.95%: pass. Abuse: a safety bound of at most 1%, no open Critical '
       'finding and no unaddressed High, set by the framework. The run found 0 failures in 300 and the red team closed its High, '
       'bound 0.99%: pass. Leaks: zero canaries in any draft or its context, the guide\'s recommendation. '
       'The run found 0 in 300 tickets, bound 0.99%, which is not proof of zero: pass. A limit moved after '
       'the run takes an exception, with an approver and an expiry.')
s = Svg(880, 352, ALT)

# Columns: the failure, its limit (signed before), the line where the run starts,
# what the run found, and the gate's verdict.
A_X, A_W = 10, 170
B_X, B_W = 190, 268
RUN_X = 484
C_X, C_W = 510, 246
D_X = 826
assert B_X + B_W < RUN_X < C_X, 'the run line must sit between the limit and the result'
assert D_X + 40 <= s.w, 'gate column leaves the frame'

# Column heads.
HEAD_Y = 30
s.text(A_X, HEAD_Y, 'FAILURE', size=10, fill=GREY, weight=500, box=A_W)
s.text(B_X + B_W / 2, HEAD_Y, 'LIMIT · SIGNED BEFORE THE RUN', size=10, fill=GREY, weight=500, anchor='middle', box=B_W)
s.text(C_X + C_W / 2, HEAD_Y, 'WHAT THE RUN FOUND', size=10, fill=GREY, weight=500, anchor='middle', box=C_W)
s.text(D_X, HEAD_Y, 'GATE', size=10, fill=GREY, weight=500, anchor='middle', box=60)

ROW0, ROW_H, ROW_GAP = 52, 66, 16
rows = [
    (('WRONG OUTPUT', 'hallucination: a false', 'fee, date or term'),
     ('bound at most 1%', 'T1 hallucination cap', 'set by the framework'),
     ('1 failure in 500', 'bound 0.95%')),
    (('ABUSE', 'injection, jailbreak,', 'misuse'),
     ('safety bound at most 1%', 'no Critical · no unaddressed High', 'set by the framework'),
     ('0 failures in 300', 'bound 0.99% · High closed')),
    (('LEAKS', 'personal data out', 'of bounds'),
     ('zero canaries', 'in any draft or its context', "the guide's recommendation"),
     ('0 canaries in 300 tickets', 'bound 0.99% · not proof of zero')),
]
BOTTOM = ROW0 + len(rows) * ROW_H + (len(rows) - 1) * ROW_GAP

# The run: everything left of this line was signed before any case ran.
s.line(f'M{RUN_X} {HEAD_Y + 8} L{RUN_X} {BOTTOM + 8}', stroke=BRICK, sw=1.5)
s.text(RUN_X, BOTTOM + 24, 'the run', size=10, fill=BRICK, weight=500, anchor='middle', box=80)


def stack(cx, y, h, lines, anchor='middle'):
    """Lines centred as a block inside a row of height h."""
    step = 15
    top = y + h / 2 - (len(lines) - 1) * step / 2 + 4
    for i, (t, size, fill, weight, box) in enumerate(lines):
        s.text(cx, top + i * step, t, size=size, fill=fill, anchor=anchor, weight=weight, box=box)


for i, (fail, limit, run) in enumerate(rows):
    y = ROW0 + i * (ROW_H + ROW_GAP)
    # The failure: a label, no box.
    stack(A_X, y, ROW_H, [(fail[0], 12, INK, 500, A_W)] + [(t, 10, GREY, 400, A_W) for t in fail[1:]], anchor='start')
    # The limit: brick, because it is the step's call.
    s.rect(B_X, y, B_W, ROW_H, fill=TINT, stroke=BRICK, sw=1.5)
    stack(B_X + B_W / 2, y, ROW_H, [(limit[0], 12, BRICK, 500, B_W - 16), (limit[1], 10, INK, 400, B_W - 16),
                                     (limit[2], 10, GREY, 400, B_W - 16)])
    # What the run found.
    s.rect(C_X, y, C_W, ROW_H, fill='#fff', stroke=INK, sw=1)
    stack(C_X + C_W / 2, y, ROW_H, [(run[0], 12, INK, 500, C_W - 16), (run[1], 10, GREY, 400, C_W - 16)])
    # The gate reads this row against its own limit, and nothing else.
    s.arrow(C_X + C_W, y + ROW_H / 2, D_X - 30, y + ROW_H / 2)
    s.text(D_X, y + ROW_H / 2 + 4, 'PASS', size=12, weight=500, anchor='middle', box=60)

# Separate the rows lightly so each reads as its own test.
for i in range(1, len(rows)):
    yy = ROW0 + i * (ROW_H + ROW_GAP) - ROW_GAP / 2
    s.line(f'M{A_X} {yy} L{B_X - 8} {yy}', stroke=RULE)

# The point, once, in brick.
NOTE_Y = BOTTOM + 52
s.parts.append(f'<circle cx="16" cy="{NOTE_Y - 4}" r="4.5" fill="{BRICK}"/>')
s.text(28, NOTE_Y, 'Moving a limit after the run takes an exception, with an approver and an expiry.',
       size=12, fill=BRICK, box=840)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-16-three-limits.svg'))
