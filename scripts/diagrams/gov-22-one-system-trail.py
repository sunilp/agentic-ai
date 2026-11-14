import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, RULE, BRICK

# Part names follow PART_LABEL in src/data/governance-path.ts. Records follow the published
# <RunningExample> boxes of Steps 2 to 21 and Step 1's deep dive. Brick marks a record that shows
# something failing or being refused.
ALT = ("The support assistant's trail through all 22 steps, grouped in the guide's six parts and the close, "
       'with the record each step left, from three decisions at Step 1 to this walk at Step 22. Eight '
       'records are in brick. Each shows something failing or being refused: the evaluation case from a '
       'flagged wrong fee, two evaluation reports with the failed first candidate kept, the incident report, '
       'the bias evaluation, the planted-error drill, the release record, the identity record with its '
       'refused call, and the signed failure mode the gateway outage tested.')

# (part header, [(step, record, what it shows, failed or refused?)])
LEFT = [
    ('PART I · FOUNDATIONS', [
        (1, 'three decisions', 'build, ship and stop, each owned', False),
        (2, 'one-page policy', 'three of its lines govern it', False),
        (3, 'register entry', 'proposed · tier pending', False),
        (4, 'signed risk assessment', 'T1 · data exposure Critical', False),
    ]),
    ('PART II · PEOPLE BEFORE PROCESS', [
        (5, 'three named shortcuts', 'each with its cause and fix', False),
        (6, 'governance.yaml', 'ID, tier, gate in the pipeline', False),
        (7, 'evaluation case', 'from a flagged wrong fee', True),
    ]),
    ('PART III · SETTING IT UP', [
        (8, 'decision table', 'one accountable name each', False),
        (9, 'deployment approvals', 'pilot, then production', False),
        (10, 'two evaluation reports', 'RC1 failed and is kept', True),
        (11, 'incident report', 'S2 · stopped, fixed, restarted', True),
    ]),
]
RIGHT = [
    ('PART IV · RESPONSIBLE AI IN DEPTH', [
        (12, 'principles table', 'a test and owner per principle', False),
        (13, 'bias evaluation', 'fluency failed, then passed', True),
        (14, 'contest decision', 'all four keep the 30 days', False),
        (15, 'planted-error drill', '17 of 20 caught, then 20', True),
        (16, 'signed limits', 'set before the run, then tested', False),
    ]),
    ('PART V · GENAI AND AGENTS', [
        (17, 'release record', 'successor failed, then passed', True),
        (18, 'identity record', 'waive_fee refused, no grant', True),
    ]),
    ('PART VI · ENTERPRISE SCALE', [
        (19, 'reuse table', 'what travels · one shared model', False),
        (20, 'signed failure mode', 'gateway down, every call refused', True),
        (21, 'applicability record', 'one gap, owned by Compliance', False),
    ]),
    ('CLOSE', [
        (22, 'this walk', 'every gap with an owner', False),
    ]),
]

COL_W = 416
TOP = 14
HEAD_H, ROW_H, PART_GAP = 26, 28, 6
DOT_R = 10
REC_X, REC_W = 32, 178          # record label, from the column's left edge
FACT_X, FACT_W = 216, 196       # what the record shows

assert sum(len(r) for _, r in LEFT + RIGHT) == 22


def column_height(parts):
    return sum(HEAD_H + ROW_H * len(rows) for _, rows in parts) + PART_GAP * (len(parts) - 1)


H_COL = max(column_height(LEFT), column_height(RIGHT))
LEGEND_Y = TOP + H_COL + 26
s = Svg(880, LEGEND_Y + 16, ALT)


def draw_column(x0, parts):
    # First pass: where every dot sits, so the trail line can run behind them.
    y, dots, heads = TOP, [], []
    for i, (head, rows) in enumerate(parts):
        if i:
            y += PART_GAP
        heads.append((head, y))
        y += HEAD_H
        for row in rows:
            dots.append((row, y + ROW_H / 2))
            y += ROW_H
    cx = x0 + 12
    s.line(f'M{cx} {dots[0][1]} L{cx} {dots[-1][1]}', stroke=RULE, sw=2)
    for head, hy in heads:
        s.text(x0 + REC_X, hy + 17, head, size=10, fill=GREY, weight=500, box=COL_W - REC_X)
        s.line(f'M{x0 + REC_X} {hy + 22} L{x0 + COL_W} {hy + 22}', stroke=RULE)
    for (n, record, shows, failed), cy in dots:
        colour = BRICK if failed else INK
        s.parts.append(f'<circle cx="{cx}" cy="{cy}" r="{DOT_R}" fill="{colour}"/>')
        s.text(cx, cy + 3.5, str(n), size=9.5, fill='#fff', anchor='middle', weight=500, box=2 * DOT_R - 2)
        s.text(x0 + REC_X, cy + 4, record, size=11, fill=colour, weight=500, box=REC_W)
        s.text(x0 + FACT_X, cy + 4, shows, size=10, fill=GREY, box=FACT_W)


draw_column(12, LEFT)
draw_column(452, RIGHT)

# Legend.
s.parts.append(f'<circle cx="24" cy="{LEGEND_Y - 4}" r="6" fill="{BRICK}"/>')
s.text(38, LEGEND_Y, 'a record that shows something failing or being refused', size=10, fill=GREY, box=390)
s.parts.append(f'<circle cx="464" cy="{LEGEND_Y - 4}" r="6" fill="{INK}"/>')
s.text(478, LEGEND_Y, 'every other record · each opened where it was made', size=10, fill=GREY, box=390)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-22-one-system-trail.svg'))
