import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, RULE, BRICK, TINT

ALT = ('The centre above, every business unit below, and what crosses between them. '
       'The centre sets and builds the standards and the control set, the paved road and its patterns, '
       'the register, calibration across units and the portfolio view. It decides T1 and T2 approvals, '
       'exceptions above T4 and new patterns for the road. Each business unit, such as Customer Support '
       'and Business Customer Support, delivers its systems end to end with its own owners, data and raters, '
       'runs its own gate and adds local requirements on top. It decides T3 and T4 approvals, and its '
       'business owner accepts the residual risk. Standards and the road go out, written once for every unit, '
       'and a unit adds to them but never loosens them. Evidence comes back from every gate run in every unit '
       'into the register, and the portfolio view is read from it.')
s = Svg(880, 448, ALT)

LEFT, RIGHT = 20, 860
COL2 = 470  # second column inside each band
ITEM = 17   # line step for list items


def band(x, y, w, h, brick):
    s.rect(x, y, w, h, fill=TINT if brick else '#fff', stroke=BRICK if brick else INK, sw=1.5 if brick else 1)


def column(x, y, head, items, width):
    s.text(x, y, head, size=10, fill=GREY, weight=500, box=width)
    for i, t in enumerate(items):
        s.text(x, y + 20 + i * ITEM, t, size=12, box=width)
    return y + 20 + (len(items) - 1) * ITEM


def thick_arrow(x, y1, y2, colour):
    """A vertical arrow from y1 to y2 with a filled head."""
    tip = y2
    back = y2 - 9 if y2 > y1 else y2 + 9
    s.line(f'M{x} {y1} L{x} {back}', stroke=colour, sw=2)
    s.parts.append(f'<path d="M{x - 6} {back} L{x} {tip} L{x + 6} {back} Z" fill="{colour}"/>')


# The centre: one band, tinted, because it is the waist every unit passes through.
CY, CH = 20, 158
band(LEFT, CY, RIGHT - LEFT, CH, brick=True)
s.text(LEFT + 20, CY + 24, 'THE CENTRE', size=12, fill=BRICK, weight=500, box=200)
s.text(RIGHT - 20, CY + 24, 'AI Risk · MRM · the platform team · the committee', size=10, fill=GREY,
       anchor='end', box=360)
c1 = column(LEFT + 20, CY + 52, 'SETS AND BUILDS', [
    'the standards and the control set',
    'the paved road and its patterns',
    'the register',
    'calibration across units',
    'the portfolio view',
], COL2 - LEFT - 40)
c2 = column(COL2, CY + 52, 'DECIDES', [
    'T1 and T2 approvals',
    'exceptions above T4',
    'new patterns for the road',
], RIGHT - COL2 - 20)
s.line(f'M{COL2 - 20} {CY + 40} L{COL2 - 20} {CY + CH - 12}', stroke=RULE)
assert c1 + 10 <= CY + CH, 'centre list leaves its band'

# What crosses: two arrows, each labelled once.
TOP, BOT = CY + CH, 276
OUT_X, BACK_X = 200, 560
thick_arrow(OUT_X, TOP + 4, BOT - 4, BRICK)
s.text(OUT_X + 16, TOP + 30, 'GOES OUT', size=10, fill=BRICK, weight=500, box=250)
s.text(OUT_X + 16, TOP + 48, 'standards · the road', size=12, weight=500, box=250)
s.text(OUT_X + 16, TOP + 64, 'written once, for every unit', size=10, fill=GREY, box=250)
s.text(OUT_X + 16, TOP + 80, 'a unit adds to them, never loosens', size=10, fill=GREY, box=250)
thick_arrow(BACK_X, BOT - 4, TOP + 4, INK)
s.text(BACK_X + 16, TOP + 30, 'COMES BACK', size=10, fill=INK, weight=500, box=RIGHT - BACK_X - 20)
s.text(BACK_X + 16, TOP + 48, 'evidence · into the register', size=12, weight=500, box=RIGHT - BACK_X - 20)
s.text(BACK_X + 16, TOP + 64, 'from every gate run, in every unit', size=10, fill=GREY, box=RIGHT - BACK_X - 20)
s.text(BACK_X + 16, TOP + 80, 'the portfolio view is read from it', size=10, fill=GREY, box=RIGHT - BACK_X - 20)
assert TOP + 80 + 8 <= BOT, 'arrow labels run into the units'

# Each business unit: a stack of cards, because there are many of them.
UY, UH, OFF = BOT, 148, 6
UW = RIGHT - LEFT - 2 * OFF
for k in (2, 1):
    band(LEFT + k * OFF, UY + k * OFF, UW, UH, brick=False)
band(LEFT, UY, UW, UH, brick=False)
s.text(LEFT + 20, UY + 24, 'EACH BUSINESS UNIT', size=12, weight=500, box=220)
s.text(LEFT + UW - 20, UY + 24, 'Customer Support · Business Customer Support · every unit after', size=10,
       fill=GREY, anchor='end', box=400)
u1 = column(LEFT + 20, UY + 52, 'DELIVERS', [
    'its systems, end to end',
    'its own owners, data and raters',
    'its own gate runs',
    'local requirements, added on top',
], COL2 - LEFT - 40)
u2 = column(COL2, UY + 52, 'DECIDES', [
    'T3 and T4 approvals',
    'residual risk, by its business owner',
], LEFT + UW - COL2 - 20)
s.line(f'M{COL2 - 20} {UY + 40} L{COL2 - 20} {UY + UH - 12}', stroke=RULE)
assert u1 + 10 <= UY + UH, 'unit list leaves its card'
assert UY + UH + 2 * OFF <= s.h - 6, 'cards leave the frame'

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-19-centre-and-units.svg'))
