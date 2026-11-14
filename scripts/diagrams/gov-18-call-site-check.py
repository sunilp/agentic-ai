import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, RULE, BRICK, TINT

ALT = ('One agent, sra-reply-agent, makes two calls, and both meet two checks at the call site, outside the model. '
       'Identity: a live credential and an approved record with an active owner. Grant: this tool, this resource, '
       'inside its caps, before its end date. queue_reply on a password-reset ticket passes both and is queued. '
       'waive_fee on the billing service passes identity, fails the grant check and never runs. '
       'Both decisions go to the agent action audit record.')
s = Svg(880, 394, ALT)

# Geometry, left to right: the agent, the two requests, the two checks, where the effect happens.
AG_X, AG_W = 10, 140
ID_X, GR_X, COL_W = 300, 520, 180
FX_X, FX_W = 730, 140
COL_TOP, COL_BOTTOM = 44, 274
ROW_A, ROW_B = 178, 238
assert FX_X + FX_W <= s.w - 8, 'right column leaves the frame'
assert ID_X + COL_W < GR_X and GR_X + COL_W < FX_X, 'columns overlap'

# The call site: both checks sit outside the model, where the effect happens.
s.line(f'M{ID_X} 34 L{ID_X} 28 L{GR_X + COL_W} 28 L{GR_X + COL_W} 34', stroke=BRICK, sw=1.2)
s.text((ID_X + GR_X + COL_W) / 2, 20, 'AT THE CALL SITE · OUTSIDE THE MODEL', size=10, fill=BRICK, anchor='middle',
       weight=500, box=GR_X + COL_W - ID_X)

# Column heads for the two ends.
s.text(AG_X, 60, 'THE AGENT', size=10, fill=GREY, weight=500, box=AG_W)
s.text(FX_X, 60, 'WHERE IT HAPPENS', size=10, fill=GREY, weight=500, box=FX_W)

# The two checks, as tall columns every call passes through.
checks = [
    (ID_X, '1 · IDENTITY', 'who is calling', ['live credential', 'record approved', 'owner active']),
    (GR_X, '2 · GRANT', 'may it do this', ['this tool, this resource', 'inside its caps', 'before its end date']),
]
for x, head, sub, lines in checks:
    s.rect(x, COL_TOP, COL_W, COL_BOTTOM - COL_TOP, fill='#fff', stroke=INK)
    cx = x + COL_W / 2
    s.text(cx, 68, head, size=11, anchor='middle', weight=500, box=COL_W - 16)
    s.text(cx, 84, sub, size=10, fill=GREY, anchor='middle', box=COL_W - 16)
    s.line(f'M{x + 16} 96 L{x + COL_W - 16} 96', stroke=RULE)
    for i, t in enumerate(lines):
        s.text(cx, 114 + i * 14, t, size=10, fill=GREY, anchor='middle', box=COL_W - 16)

# The agent: one identity, two requests.
AG_Y, AG_H = 160, 96
s.box(AG_X, AG_Y, AG_W, AG_H, 'sra-reply-agent', 'one identity')

requests = [
    (ROW_A, 'queue_reply', 'password-reset ticket'),
    (ROW_B, 'waive_fee', 'billing service'),
]
for y, tool, target in requests:
    # Both labels sit above their own line, so neither reads as the other row's.
    s.text((AG_X + AG_W + ID_X) / 2, y - 21, tool, size=11, anchor='middle', weight=500, box=ID_X - AG_X - AG_W - 10)
    s.text((AG_X + AG_W + ID_X) / 2, y - 7, target, size=10, fill=GREY, anchor='middle', box=ID_X - AG_X - AG_W - 10)


def mark(cx, y, label, colour=INK, weight=400):
    """A verdict sitting on the line, on a white chip so the line does not strike it through."""
    w = len(label) * 10 * 0.605 + 10
    s.rect(cx - w / 2, y - 9, w, 15, fill='#fff', stroke='#fff')
    s.text(cx, y + 3, label, size=10, fill=colour, anchor='middle', weight=weight, box=COL_W - 16)


id_cx, gr_cx = ID_X + COL_W / 2, GR_X + COL_W / 2

# Row A: passes both checks and reaches the outbox.
s.line(f'M{AG_X + AG_W} {ROW_A} L{FX_X - 2} {ROW_A}')
s.arrow(FX_X - 20, ROW_A, FX_X - 2, ROW_A)
mark(id_cx, ROW_A, 'pass')
mark(gr_cx, ROW_A, 'pass')
s.box(FX_X, ROW_A - 22, FX_W, 44, 'outbox', 'reply queued')

# Row B: passes identity, stops at the grant check. Nothing reaches the billing service.
STOP_X = gr_cx - 6
s.line(f'M{AG_X + AG_W} {ROW_B} L{STOP_X} {ROW_B}')
s.line(f'M{STOP_X} {ROW_B - 10} L{STOP_X} {ROW_B + 10}', stroke=BRICK, sw=3)
mark(id_cx, ROW_B, 'pass')
s.text(gr_cx, ROW_B + 22, 'refused · no grant', size=10, fill=BRICK, anchor='middle', weight=500, box=COL_W - 16)
s.rect(FX_X, ROW_B - 22, FX_W, 44, fill='#fff', stroke=GREY)
s.text(FX_X + FX_W / 2, ROW_B - 3, 'billing service', size=11, fill=GREY, anchor='middle', weight=500, box=FX_W - 16)
s.text(FX_X + FX_W / 2, ROW_B + 12, 'waive_fee never runs', size=10, fill=BRICK, anchor='middle', box=FX_W - 12)

# Both decisions go to the audit record.
BAND_Y, BAND_H = 302, 40
s.line(f'M{gr_cx} {COL_BOTTOM} L{gr_cx} {BAND_Y - 2}')
s.arrow(gr_cx, BAND_Y - 14, gr_cx, BAND_Y - 1)
s.text(gr_cx + 10, 292, 'both decisions', size=10, fill=GREY, box=150)
s.rect(ID_X, BAND_Y, GR_X + COL_W - ID_X, BAND_H, fill=TINT, stroke=BRICK, sw=1.5)
s.text(ID_X + 14, BAND_Y + 17, 'AGENT ACTION AUDIT RECORD', size=11, fill=BRICK, weight=500, box=300)
s.text(ID_X + 14, BAND_Y + 32, 'agent_id · tool · authorisation_decision · rule', size=10, fill=GREY,
       box=GR_X + COL_W - ID_X - 28)

# The point, once, in brick.
s.parts.append(f'<circle cx="16" cy="374" r="4.5" fill="{BRICK}"/>')
s.text(28, 378, 'The model can ask for any tool. The check where the effect happens decides what runs.', size=12,
       fill=BRICK, box=840)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-18-call-site-check.svg'))
