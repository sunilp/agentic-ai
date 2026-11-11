import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, BRICK, MONO_W

ALT = ('The governed path runs idea, register, tier, gate, live. Three shortcuts leave it and land on live: '
       'real data before the entry, call it a pilot, and secure it later. Each one leaves where the path '
       'costs more than the way around it.')
s = Svg(880, 312, ALT)

# The governed path.
ROW_Y, ROW_H, BW = 212, 48, 136
steps = [('IDEA', 'a team wants it'), ('REGISTER', 'Step 3'), ('TIER', 'Step 4'), ('GATE', 'Step 9'), ('LIVE', 'real data and users')]
xs = [10 + i * 180 for i in range(5)]  # 10, 190, 370, 550, 730; boxes end at 146, 326, 506, 686, 866
for (title, sub), x in zip(steps, xs):
    s.box(x, ROW_Y, BW, ROW_H, title, sub)
for x in xs[:-1]:
    s.arrow(x + BW, ROW_Y + ROW_H / 2, x + 180 - 2, ROW_Y + ROW_H / 2)


def bez(p0, p1, p2, p3, t):
    u = 1 - t
    return tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d for a, b, c, d in zip(p0, p1, p2, p3))


# Three shortcuts, nested so no two cross. Each leaves the top of a box and lands on LIVE.
# (start x, landing x, apex y, label). Each label sits just above its own apex,
# in the band between that arc and the one outside it.
arcs = [
    (78, 846, 46, 'real data before the entry'),
    (258, 806, 106, 'call it a pilot'),
    (438, 766, 166, 'secure it later'),
]
labels = []
curves = []
for x1, x2, apex_y, label in arcs:
    cy = ROW_Y + (apex_y - ROW_Y) / 0.75  # a cubic with level control points peaks at 3/4 of the way
    p0, p1, p2, p3 = (x1, ROW_Y), (x1, cy), (x2, cy), (x2, ROW_Y)
    s.line(f'M{x1} {ROW_Y} C{x1} {cy} {x2} {cy} {x2} {ROW_Y}', stroke=GREY, sw=1.2, dash='5 4')
    # arrowhead into LIVE
    s.arrow(x2, ROW_Y - 12, x2, ROW_Y - 1, stroke=GREY)
    # departure marker: where the path costs more than the way around
    s.parts.append(f'<circle cx="{x1}" cy="{ROW_Y}" r="4.5" fill="{BRICK}"/>')
    mid = (x1 + x2) / 2
    base = apex_y - 9
    w = len(label) * 12 * MONO_W
    s.text(mid, base, label, size=12, anchor='middle', box=x2 - x1 - 40)
    labels.append((mid - w / 2, base - 12, mid + w / 2, base + 3))
    curves.append([bez(p0, p1, p2, p3, i / 400) for i in range(401)])

# No arc may cross any label, and nothing may leave the frame.
for (lx1, ly1, lx2, ly2), label in zip(labels, [a[3] for a in arcs]):
    assert 0 <= lx1 and lx2 <= s.w and 0 <= ly1, f'label out of frame: {label}'
    for pts in curves:
        for px, py in pts:
            assert not (lx1 - 3 <= px <= lx2 + 3 and ly1 - 3 <= py <= ly2 + 3), f'arc crosses label: {label}'
for pts in curves:
    assert min(py for _, py in pts) >= 4, 'arc leaves the frame'

# The point, once, in brick.
s.parts.append(f'<circle cx="16" cy="{ROW_Y + ROW_H + 30}" r="4.5" fill="{BRICK}"/>')
s.text(28, ROW_Y + ROW_H + 34, 'Each shortcut leaves where the path costs more than the way around it.', size=12, fill=BRICK, box=840)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-05-shortcuts.svg'))
