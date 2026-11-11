import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, GREY

s = Svg(880, 226, 'The reporting loop: notice, report, thank, fix, share, and back to notice. Each fix lands as an evaluation case or a control change.')

# The loop, left to right. Thanks come before the fix.
steps = [
    ('NOTICE', 'a near-miss'),
    ('REPORT', 'one route, minutes'),
    ('THANK', 'the first reply'),
    ('FIX', 'the system behind it'),
    ('SHARE', 'what changed'),
]
for i, (title, sub) in enumerate(steps):
    x = 10 + i * 180
    s.box(x, 56, 140, 56, title, sub, brick=(title == 'THANK'))
    if i < len(steps) - 1:
        s.arrow(x + 140, 84, x + 178, 84)

# Back to the start: people see what a report changes, and notice the next one.
s.line('M800 56 L800 24 L80 24')
s.arrow(80, 24, 80, 54)
s.text(440, 44, 'people see what a report changes', size=11, fill=GREY, anchor='middle', box=440)

# Where the finding lands.
s.line('M620 112 L620 136')
s.line('M530 136 L710 136')
s.arrow(530, 136, 530, 158)
s.arrow(710, 136, 710, 158)
s.box(450, 160, 160, 48, 'EVALUATION CASE', 'the suite tests it')
s.box(630, 160, 160, 48, 'CONTROL CHANGE', 'the hole is closed')
s.text(434, 188, 'where the finding lands', size=11, fill=GREY, anchor='end', box=300)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-07-reporting-loop.svg'))
