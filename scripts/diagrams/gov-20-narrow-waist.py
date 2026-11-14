import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, BRICK, TINT

ALT = ('The narrow waist. Above it, every team\'s AI systems. Below it, models, data and production. '
       'In the waist, five shared pieces, each with what it sees and two controls it enforces. '
       'Gateway: every model call; PM-006 the stop, DE-004 guardrails. '
       'Registry: every system; RA-006 entry first, GV-006 inventory reconciled. '
       'Policy gate: every release; DA-003 gates passed, DA-001 evidence checklist. '
       'Evaluation service: every suite run; EV-001 to EV-009 release suites, PM-004 live scoring. '
       'Audit store: every record; PM-007 audit log, DR-003 evidence archive.')
s = Svg(880, 352, ALT)

# The two wide bands: everything above the waist and everything below it.
BAND_X0, BAND_X1 = 20, 860
TOP_Y, TOP_H = 14, 46
BOT_Y, BOT_H = 290, 46

# The waist: narrower than the bands, so the funnel lines draw an hourglass.
W_X0, W_X1 = 116, 764
W_Y0, W_Y1 = 92, 258

# Five pieces inside the waist.
PIECES = [
    ('GATEWAY', 'every model call', [('PM-006', 'the stop'), ('DE-004', 'guardrails')]),
    ('REGISTRY', 'every system', [('RA-006', 'entry first'), ('GV-006', 'reconciled')]),
    ('POLICY GATE', 'every release', [('DA-003', 'gates passed'), ('DA-001', 'checklist')]),
    ('EVAL SERVICE', 'every suite run', [('EV-001 to EV-009', 'release suites'), ('PM-004', 'live scoring')]),
    ('AUDIT STORE', 'every record', [('PM-007', 'audit log'), ('DR-003', 'archive')]),
]
BOX_W, GAP = 118, 8
X0 = W_X0 + ((W_X1 - W_X0) - (5 * BOX_W + 4 * GAP)) / 2
BOX_Y, BOX_H = 104, 56


def col_x(i):
    return X0 + i * (BOX_W + GAP)


# Bands.
s.rect(BAND_X0, TOP_Y, BAND_X1 - BAND_X0, TOP_H)
s.text(440, TOP_Y + 20, "EVERY TEAM'S AI SYSTEMS", size=11, weight=500, anchor='middle', box=400)
s.text(440, TOP_Y + 35, 'many teams, each built on the paved road', size=10, fill=GREY, anchor='middle', box=400)
s.rect(BAND_X0, BOT_Y, BAND_X1 - BAND_X0, BOT_H)
s.text(440, BOT_Y + 20, 'MODELS, DATA AND PRODUCTION', size=11, weight=500, anchor='middle', box=400)
s.text(440, BOT_Y + 35, 'vendor models, sources, live traffic', size=10, fill=GREY, anchor='middle', box=400)

# Funnel lines from the bands to the waist corners.
s.line(f'M{BAND_X0} {TOP_Y + TOP_H} L{W_X0} {W_Y0}', stroke=GREY)
s.line(f'M{BAND_X1} {TOP_Y + TOP_H} L{W_X1} {W_Y0}', stroke=GREY)
s.line(f'M{W_X0} {W_Y1} L{BAND_X0} {BOT_Y}', stroke=GREY)
s.line(f'M{W_X1} {W_Y1} L{BAND_X1} {BOT_Y}', stroke=GREY)

# The waist outline.
s.rect(W_X0, W_Y0, W_X1 - W_X0, W_Y1 - W_Y0, fill='none', stroke=BRICK, sw=1.5)

# Right margin: name the waist.
s.text(W_X1 + 14, 136, 'NARROW', size=10, fill=BRICK, weight=500, box=80)
s.text(W_X1 + 14, 150, 'WAIST', size=10, fill=BRICK, weight=500, box=80)

# Left margin: row labels.
s.text(W_X0 - 10, BOX_Y + BOX_H / 2 + 13, 'SEES', size=10, fill=GREY, weight=500, anchor='end', box=90)
s.text(W_X0 - 10, 190, 'ENFORCES', size=10, fill=GREY, weight=500, anchor='end', box=90)

for i, (title, sees, controls) in enumerate(PIECES):
    x = col_x(i)
    cx = x + BOX_W / 2
    # Flow in from above and out below, through each piece.
    s.arrow(cx, TOP_Y + TOP_H, cx, BOX_Y - 1, stroke=GREY)
    s.box(x, BOX_Y, BOX_W, BOX_H, title, sees, brick=True)
    # Controls this piece enforces: ID in brick, plain gloss in grey.
    for j, (cid, gloss) in enumerate(controls):
        y = 190 + j * 34
        s.text(cx, y, cid, size=11, fill=BRICK, weight=500, anchor='middle', box=BOX_W - 8)
        s.text(cx, y + 14, gloss, size=10, fill=GREY, anchor='middle', box=BOX_W - 8)
    s.arrow(cx, W_Y1, cx, BOT_Y - 1, stroke=GREY)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-20-narrow-waist.svg'))
