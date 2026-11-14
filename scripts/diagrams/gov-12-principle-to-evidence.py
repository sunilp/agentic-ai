import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, RULE, BRICK

ALT = ('A principle becomes four more things: a commitment that names a breach, a test with its threshold, '
       'one owner who hears first if it fails, and a row in the evidence pack. For the assistant, reliability '
       'and safety becomes: fewer than 1 in 100 drafts states a wrong fee, date or policy term; 500 unseen emails, '
       'passing on the 95% bound under 1%; the AI lead, with MRM rerunning it; row 10 of the pack, the evaluation '
       "report. 'We use AI responsibly' has none of the four. Without a test, a principle is a slogan.")
s = Svg(880, 316, ALT)

# The chain, left to right. The test is the step's call, so it is the one brick box.
links = [
    ('PRINCIPLE', 'from the policy'),
    ('COMMITMENT', 'a breach you can name'),
    ('TEST', 'and its threshold'),
    ('OWNER', 'one name, hears first'),
    ('EVIDENCE', 'a row in the pack'),
]
BW, GAP, X0 = 148, 30, 10
ROW_Y, ROW_H = 28, 54
xs = [X0 + i * (BW + GAP) for i in range(len(links))]  # last box ends at 870
assert xs[-1] + BW <= s.w - 8, 'row leaves the frame'
cxs = [x + BW / 2 for x in xs]
COL = BW + GAP - 6  # width a column's text may use

for (title, sub), x in zip(links, xs):
    s.box(x, ROW_Y, BW, ROW_H, title, sub, brick=(title == 'TEST'))
for x in xs[:-1]:
    s.arrow(x + BW, ROW_Y + ROW_H / 2, x + BW + GAP - 2, ROW_Y + ROW_H / 2)


def row(label, top, cells, colours):
    s.text(X0, top, label, size=10, fill=GREY, weight=500, box=400)
    s.line(f'M{X0} {top + 6} L{xs[-1] + BW} {top + 6}', stroke=RULE)
    for cx, lines, colour in zip(cxs, cells, colours):
        for j, t in enumerate(lines):
            s.text(cx, top + 28 + j * 16, t, size=11, fill=colour, anchor='middle', box=COL)


# One principle carried all the way, from Step 10.
row('THE ASSISTANT', 122, [
    ('reliability', 'and safety'),
    ('fewer than 1 in 100', 'drafts states a wrong', 'fee, date or policy term'),
    ('500 unseen emails', 'pass on the 95% bound', 'under the 1% cap'),
    ('AI lead', 'MRM reruns it'),
    ('row 10', 'evaluation report'),
], [INK] * 5)

# The line Step 2 struck out. It never leaves the first box.
row('A SLOGAN', 216, [
    ('"We use AI', 'responsibly"'),
    ('none',),
    ('none',),
    ('none',),
    ('none',),
], [INK, GREY, GREY, GREY, GREY])

# The point, once, in brick.
s.parts.append(f'<circle cx="16" cy="292" r="4.5" fill="{BRICK}"/>')
s.text(28, 296, 'Without a test, a principle is a slogan. Every link has to exist.', size=12, fill=BRICK, box=840)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-12-principle-to-evidence.svg'))
