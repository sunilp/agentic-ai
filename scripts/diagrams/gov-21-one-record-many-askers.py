import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, RULE, BRICK, TINT

ALT = ('Five askers on the left, each labelled with its force: ISO/IEC 42001, a standard the company chose; '
       'the NIST AI RMF, a voluntary framework; a business customer\'s contract; the company\'s own AI policy; '
       'and Article 50(2) of the EU AI Act, a law. Four lines run to one record in the evidence pack, the '
       'assistant\'s evaluation report, which names its model, prompt and index versions and its result: '
       '2 drafts wrong in 700, a bound of 0.90%. The fifth line ends at a written gap with an owner.')
s = Svg(880, 430, ALT)

# Left: who asks, each with its force. Right: one record, and one written gap.
AX, AW, AH = 10, 300, 58
ROW0, STEP = 46, 70
CX, CW = 470, 400

s.text(AX, 28, 'WHO ASKS · WITH WHAT FORCE', size=10, fill=GREY, weight=500, box=AW)
s.text(CX, 28, 'ONE RECORD IN THE EVIDENCE PACK', size=10, fill=GREY, weight=500, box=CW)

askers = [
    ('STANDARD · CHOSEN', 'ISO/IEC 42001', 'tested before release?'),
    ('FRAMEWORK · VOLUNTARY', 'NIST AI RMF · MEASURE 2', 'evaluated for trustworthy characteristics?'),
    ('COMMITMENT · CONTRACT', 'Business customer contract', 'AI output tested before every release?'),
    ('COMMITMENT · INTERNAL', 'Your AI policy', 'fewer than 1 draft in 100 wrong?'),
    ('LAW · BINDS', 'EU AI Act · Art. 50(2)', 'text output marked as AI-generated?'),
]
mids = []
for i, (force, name, ask) in enumerate(askers):
    y = ROW0 + i * STEP
    gap = i == len(askers) - 1
    s.rect(AX, y, AW, AH, fill='#fff', stroke=INK)
    s.text(AX + 10, y + 16, force, size=9, fill=BRICK if gap else GREY, weight=500, box=AW - 20)
    s.text(AX + 10, y + 33, name, size=12, weight=500, box=AW - 20)
    s.text(AX + 10, y + 49, ask, size=10, fill=GREY, box=AW - 20)
    mids.append(y + AH / 2)

# The record: what it describes, so every asker can tell whether it still holds.
RY, RH = ROW0, 4 * STEP - 12
s.rect(CX, RY, CW, RH, fill='#fff', stroke=INK, sw=1.5)
s.text(CX + 16, RY + 22, 'EV-001 · EVALUATION REPORT', size=11, fill=BRICK, weight=500, box=CW - 32)
s.text(CX + 16, RY + 41, 'support-reply-assistant-v0.1 · T1', size=12, weight=500, box=CW - 32)
s.line(f'M{CX + 16} {RY + 54} L{CX + CW - 16} {RY + 54}', stroke=RULE)
fields = [
    ('model', 'vendor-model-2027-01-20'),
    ('prompt', 'support-reply/draft/v4.0'),
    ('index', 'plan terms and policies, build 212'),
    ('dataset', '700 unseen emails'),
    ('result', '2 wrong · bound 0.90% · pass'),
]
for j, (k, v) in enumerate(fields):
    fy = RY + 78 + j * 23
    s.text(CX + 16, fy, k, size=10, fill=GREY, box=70)
    s.text(CX + 96, fy, v, size=11, weight=500 if k == 'result' else 400, box=CW - 112)
s.line(f'M{CX + 16} {RY + 186} L{CX + CW - 16} {RY + 186}', stroke=RULE)
s.text(CX + 16, RY + 207, 'each asker holds a link to this record', size=10, fill=GREY, box=CW - 32)
s.text(CX + 16, RY + 225, 'a new model, prompt or index replaces it', size=10, fill=GREY, box=CW - 32)
s.text(CX + 16, RY + 243, 'in every row at once · the old one is archived', size=10, fill=GREY, box=CW - 32)

# The written gap: the one asker with no settled answer.
GY, GH = ROW0 + 4 * STEP, AH
s.rect(CX, GY, CW, GH, fill=TINT, stroke=BRICK, sw=1.5)
s.text(CX + 16, GY + 18, 'GAP · ART. 50(2) FOR EDITED DRAFTS', size=11, fill=BRICK, weight=500, box=CW - 32)
s.text(CX + 16, GY + 34, 'undecided · owner: Compliance, with counsel', size=10, box=CW - 32)
s.text(CX + 16, GY + 50, 'meanwhile: the mark goes on every sent reply', size=10, fill=GREY, box=CW - 32)

# Mapping lines. Four meet at one point on the record: one record, many askers. The fifth lands on the gap.
T = RY + 124
for m in mids[:4]:
    s.line(f'M{AX + AW} {m} C{AX + AW + 90} {m} {CX - 70} {T} {CX} {T}', stroke=INK)
    s.parts.append(f'<circle cx="{AX + AW}" cy="{m}" r="3" fill="{INK}"/>')
s.parts.append(f'<circle cx="{CX}" cy="{T}" r="4" fill="{INK}"/>')
gm = mids[4]
s.line(f'M{AX + AW} {gm} L{CX} {GY + GH / 2}', stroke=BRICK, sw=1.5)
s.parts.append(f'<circle cx="{AX + AW}" cy="{gm}" r="3" fill="{BRICK}"/>')
s.parts.append(f'<circle cx="{CX}" cy="{GY + GH / 2}" r="3" fill="{BRICK}"/>')

# Legend.
LY = 414
s.line(f'M{AX} {LY - 4} L{AX + 30} {LY - 4}', stroke=INK)
s.text(AX + 40, LY, 'a link to the record, never a copy', size=10, fill=GREY, box=260)
s.line(f'M{CX} {LY - 4} L{CX + 30} {LY - 4}', stroke=BRICK, sw=1.5)
s.text(CX + 40, LY, 'a gap, written down with an owner', size=10, fill=GREY, box=CW - 40)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-21-one-record-many-askers.svg'))
