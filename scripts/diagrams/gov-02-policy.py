import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, BRICK, TINT

s = Svg(880, 280, 'A one-page AI policy: principles, rules, one owner and a review trigger, each pointing to the step that makes it real.')
s.rect(300, 12, 280, 256)
s.text(440, 34, 'ONE PAGE', size=11, fill=GREY, anchor='middle', box=260)
bands = [
    ('PRINCIPLES', 'each one testable', 'tested in Step 12'),
    ('RULES', 'acceptable and prohibited uses', 'screened and tiered, Step 4'),
    ('OWNER', 'one named executive', 'decision rights, Step 8'),
    ('REVIEW', 'a date and a trigger', 'run in Step 11'),
]
for i, (title, sub, note) in enumerate(bands):
    y = 46 + i * 54
    s.box(316, y, 248, 44, title, sub, brick=(title == 'OWNER'))
    s.arrow(564, y + 22, 640, y + 22, stroke=BRICK if title == 'OWNER' else INK)
    s.text(648, y + 26, note, size=11, fill=BRICK if title == 'OWNER' else INK, box=226)
s.text(282, 140, 'one page,', size=11, fill=GREY, anchor='end', box=270)
s.text(282, 156, 'one owner', size=11, fill=GREY, anchor='end', box=270)
s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-02-policy.svg'))
