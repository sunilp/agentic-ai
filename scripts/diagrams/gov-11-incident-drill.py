import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, GREY, BRICK, RULE, MONO_W

ALT = ('The incident path a drill walks: detect, stop, preserve, tell, fix, restart, then back to what you watch. '
       'Under each link, what the drill has to prove: acknowledged inside the clock, the stop in effect within 15 minutes, '
       'evidence pulled within the hour, the right people told in order, a change that sticks, and a restart lifted by name '
       'and recorded.')
s = Svg(880, 252, ALT)

# The path, left to right. The stop is the step's call, so it is the one brick box.
links = [
    ('DETECT', 'the real route', ('acknowledged', 'inside the clock')),
    ('STOP', 'a named person', ('in effect within', '15 minutes')),
    ('PRESERVE', 'logs, versions', ('evidence pulled', 'within the hour')),
    ('TELL', 'who hears, when', ('the right people,', 'in order')),
    ('FIX', 'test or control', ('a change', 'that sticks')),
    ('RESTART', 'on evidence', ('lifted by name,', 'recorded')),
]
BW, GAP, X0 = 118, 30, 11
ROW_Y, ROW_H = 56, 56
xs = [X0 + i * (BW + GAP) for i in range(len(links))]  # last box ends at 869
assert xs[-1] + BW <= s.w - 8, 'row leaves the frame'

for (title, sub, _), x in zip(links, xs):
    s.box(x, ROW_Y, BW, ROW_H, title, sub, brick=(title == 'STOP'))
for x in xs[:-1]:
    s.arrow(x + BW, ROW_Y + ROW_H / 2, x + BW + GAP - 2, ROW_Y + ROW_H / 2)

# Back to the start: the fix becomes something you watch.
first_cx, last_cx = xs[0] + BW / 2, xs[-1] + BW / 2
s.line(f'M{last_cx} {ROW_Y} L{last_cx} 24 L{first_cx} 24')
s.arrow(first_cx, 24, first_cx, ROW_Y - 2)
s.text(s.w / 2, 42, 'the fix joins what you watch', size=11, fill=GREY, anchor='middle', box=last_cx - first_cx - 40)

# What the drill proves at each link.
PROOF_Y = 168
s.text(X0, 150, 'THE DRILL PROVES', size=10, fill=GREY, weight=500, box=200)
s.line(f'M{X0} 156 L{xs[-1] + BW} 156', stroke=RULE)
for (title, _, (l1, l2)), x in zip(links, xs):
    cx = x + BW / 2
    s.line(f'M{cx} {ROW_Y + ROW_H} L{cx} 134', stroke=GREY)
    colour = BRICK if title == 'STOP' else '#1a1a1a'
    s.text(cx, PROOF_Y + 6, l1, size=11, fill=colour, anchor='middle', box=BW + GAP - 6)
    s.text(cx, PROOF_Y + 22, l2, size=11, fill=colour, anchor='middle', box=BW + GAP - 6)

# The point, once, in brick.
s.parts.append(f'<circle cx="16" cy="226" r="4.5" fill="{BRICK}"/>')
s.text(28, 230, 'A drill plants one fault and walks it down every link. Each link has to hold.', size=12, fill=BRICK, box=840)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-11-incident-drill.svg'))
