import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, BRICK, TINT

ALT = ('Two routes from idea to production. Without a road: find an approver, argue the tier, '
       'answer vendor checks again, build evidence by hand, wait for a meeting. On the paved road: '
       'register, use an approved pattern, let pipeline checks write the evidence, then wait only '
       'for the approvals the tier sets.')
s = Svg(880, 262, ALT)


def dashed_box(x, y, w, h, title, sub, brick=False):
    """A wait: time the team spends on someone else. Dashed border, same labels as box()."""
    stroke = BRICK if brick else INK
    s.rect(x, y, w, h, fill=TINT if brick else '#fff', stroke='none')
    s.line(f'M{x} {y} L{x + w} {y} L{x + w} {y + h} L{x} {y + h} Z', stroke=stroke, sw=1.5 if brick else 1, dash='5 3')
    cx = x + w / 2
    s.text(cx, y + h / 2 - 2, title, size=11, fill=BRICK if brick else INK, anchor='middle', weight=500, box=w - 16)
    s.text(cx, y + h / 2 + 13, sub, size=10, fill=GREY, anchor='middle', box=w - 16)


TOP_Y, BOT_Y, H = 34, 158, 56
TOP_MID, BOT_MID = TOP_Y + H / 2, BOT_Y + H / 2
MID = (TOP_MID + BOT_MID) / 2

# Shared ends: one idea, one production.
s.box(10, MID - 28, 70, 56, 'IDEA')
s.box(770, MID - 28, 100, 56, 'PRODUCTION')

# Row labels.
s.text(105, TOP_Y - 12, 'WITHOUT A ROAD', size=10, fill=GREY, weight=500, box=200)
s.text(105, BOT_Y - 12, 'THE PAVED ROAD', size=10, fill=BRICK, weight=500, box=200)

# Top row: five boxes, four of them waits.
top = [('APPROVER', 'find who signs', True), ('TIER', 'argued per case', True),
       ('VENDOR CHECKS', 'asked again', True), ('EVIDENCE', 'built by hand', False),
       ('MEETING', 'next free slot', True)]
W_TOP, GAP = 112, 20
for i, (title, sub, wait) in enumerate(top):
    x = 105 + i * (W_TOP + GAP)
    (dashed_box if wait else s.box)(x, TOP_Y, W_TOP, H, title, sub)
    if i:
        s.arrow(x - GAP, TOP_MID, x - 1, TOP_MID)

# Bottom row: four boxes, one wait, all brick.
bot = [('REGISTER', 'entry and credential', False), ('APPROVED PATTERN', 'endpoint and template', False),
       ('PIPELINE CHECKS', 'evidence produced', False), ('TIER APPROVALS', 'set by the tier', True)]
W_BOT = 145
for i, (title, sub, wait) in enumerate(bot):
    x = 105 + i * (W_BOT + GAP)
    if wait:
        dashed_box(x, BOT_Y, W_BOT, H, title, sub, brick=True)
    else:
        s.box(x, BOT_Y, W_BOT, H, title, sub, brick=True)
    if i:
        s.arrow(x - GAP, BOT_MID, x - 1, BOT_MID, stroke=BRICK)

# Idea forks into both rows; both rows join at production.
s.line(f'M80 {MID} L92 {MID} L92 {TOP_MID} L104 {TOP_MID}')
s.arrow(92, TOP_MID, 104, TOP_MID)
s.line(f'M92 {MID} L92 {BOT_MID} L104 {BOT_MID}', stroke=BRICK)
s.arrow(92, BOT_MID, 104, BOT_MID, stroke=BRICK)
s.line(f'M745 {TOP_MID} L757 {TOP_MID} L757 {MID - 6} L769 {MID - 6}')
s.arrow(757, MID - 6, 769, MID - 6)
s.line(f'M745 {BOT_MID} L757 {BOT_MID} L757 {MID + 6} L769 {MID + 6}', stroke=BRICK)
s.arrow(757, MID + 6, 769, MID + 6, stroke=BRICK)

# Legend.
s.line('M105 238 L135 238 L135 252 L105 252 Z', dash='5 3')
s.text(145, 249, 'waiting on someone', size=10, fill=GREY, box=140)
s.rect(300, 238, 30, 14)
s.text(340, 249, 'work the team does', size=10, fill=GREY, box=140)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-06-paved-road.svg'))
