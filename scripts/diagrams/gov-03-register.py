import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, GREY, BRICK, TINT

s = Svg(880, 250, 'Five discovery sources feed one AI register, which feeds tiering, owners and audit.')
sources = ['Contracts and procurement', 'Cloud bills and API keys', 'Code and model registries', 'SaaS admin consoles', 'Team declarations']
for i, label in enumerate(sources):
    y = 14 + i * 46
    s.rect(10, y, 250, 32)
    s.text(24, y + 21, label, size=12, box=226)
    s.line(f'M260 {y + 16} L360 125')
s.rect(360, 95, 210, 60, fill=TINT, stroke=BRICK, sw=1.5)
s.text(465, 121, 'AI REGISTER', size=13, fill=BRICK, anchor='middle', weight=500, box=190)
s.text(465, 141, 'system of record', size=11, fill=GREY, anchor='middle', box=190)
for label, y in [('Tiering · Step 4', 40), ('Owners · Step 8', 109), ('Audit · Step 21', 178)]:
    s.line(f'M570 125 L650 {y + 16}')
    s.rect(650, y, 220, 32)
    s.text(664, y + 21, label, size=12, box=196)
s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-03-register.svg'))
