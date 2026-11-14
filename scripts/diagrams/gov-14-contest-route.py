import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, BRICK, RULE, TINT

ALT = ('The route a contest travels, left to right: the person affected, first contact, the reviewer and the decider, '
       'then back to the person with the outcome and its reasons, in writing. Under each stop, what it can see. '
       'The person affected: the output and its label, the rule that applied, who sent the reply. '
       'First contact, who logs it and starts the clock: the case, the request as written, the deadline. '
       'The reviewer, who did not produce the outcome: the case rebuilt, with the input, sources and versions, '
       'and the output beside what was sent. The decider, who can change the outcome: the reviewer\'s finding '
       'and every case like this one. Underneath, the auditor reads the log afterwards: every request, its deadline, '
       'whether the outcome was upheld or changed, and who decided. A contest ends with a person who can change the '
       'outcome. It never goes back to the system.')
s = Svg(880, 332, ALT)

# The route, left to right. The decider is the step's point, so it is the one brick box.
stops = [
    ('THE PERSON AFFECTED', 'asks why, contests', ('the output and its label', 'the rule that applied', 'who sent the reply')),
    ('FIRST CONTACT', 'logs it, starts the clock', ('the case', 'the request, as written', 'the deadline')),
    ('THE REVIEWER', 'did not produce it', ('the case, rebuilt:', 'input, sources, versions', 'output and what was sent')),
    ('THE DECIDER', 'can change the outcome', ("the reviewer's finding", 'every case like this one')),
]
BW, GAP, X0 = 190, 32, 12
ROW_Y, ROW_H = 56, 60
xs = [X0 + i * (BW + GAP) for i in range(len(stops))]  # 12, 234, 456, 678; last ends at 868
assert xs[-1] + BW <= s.w - 8, 'row leaves the frame'

for (title, sub, _), x in zip(stops, xs):
    s.box(x, ROW_Y, BW, ROW_H, title, sub, brick=(title == 'THE DECIDER'))
for x in xs[:-1]:
    s.arrow(x + BW, ROW_Y + ROW_H / 2, x + BW + GAP - 2, ROW_Y + ROW_H / 2)

# Back to the person: the decision goes back in writing.
first_cx, last_cx = xs[0] + BW / 2, xs[-1] + BW / 2
s.line(f'M{last_cx} {ROW_Y} L{last_cx} 24 L{first_cx} 24', stroke=BRICK)
s.arrow(first_cx, 24, first_cx, ROW_Y - 2, stroke=BRICK)
s.text(s.w / 2, 42, 'the outcome and its reasons, in writing', size=11, fill=BRICK, anchor='middle', box=last_cx - first_cx - 40)

# What each stop can see.
SEE_Y = 150
s.text(X0, SEE_Y, 'WHAT EACH CAN SEE', size=10, fill=GREY, weight=500, box=200)
s.line(f'M{X0} {SEE_Y + 6} L{xs[-1] + BW} {SEE_Y + 6}', stroke=RULE)
for (title, _, lines), x in zip(stops, xs):
    cx = x + BW / 2
    s.line(f'M{cx} {ROW_Y + ROW_H} L{cx} {SEE_Y - 14}', stroke=GREY)
    for i, ln in enumerate(lines):
        s.text(cx, SEE_Y + 28 + i * 18, ln, size=11, fill=INK, anchor='middle', box=BW + GAP - 8)

# The auditor reads the whole log afterwards, across every case.
AUD_Y, AUD_H = 238, 44
s.rect(X0, AUD_Y, xs[-1] + BW - X0, AUD_H, fill='#fff', stroke=GREY)
s.text(X0 + 14, AUD_Y + 27, 'THE AUDITOR', size=11, weight=500, box=110)
s.text(X0 + 124, AUD_Y + 27, 'reads the log afterwards · every request · its deadline · upheld or changed · who decided',
       size=11, fill=GREY, box=xs[-1] + BW - X0 - 138)

# The point, once, in brick.
s.parts.append(f'<circle cx="16" cy="310" r="4.5" fill="{BRICK}"/>')
s.text(28, 314, 'A contest ends with a person who can change the outcome. It never goes back to the system.',
       size=12, fill=BRICK, box=840)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-14-contest-route.svg'))
