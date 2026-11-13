import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from govkit import Svg, INK, GREY, BRICK

# Stage names follow framework/governance-operations/governance-workflow.md at v2.3.0:
# 1 Idea Intake, 2 Risk Assessment & Tiering, 3 Architecture & Design Review,
# 4 Development & Prompt Engineering, 5 Evaluation & Testing, 6 Security Review & Red-Teaming,
# 7 Deployment Approval, 8 Production Operations, 9 Ongoing Governance, 10 Deprecation & Retirement.
ALT = ('The framework\'s ten stages with a gate before each. Stages 1 and 2, intake and risk assessment '
       'with tiering, are shared. The tier then picks a lane. T1 and T2 systems run stages 3 to 7 with '
       'signers outside the team. The fast lane runs T3 and T4 through the same stages with a lighter pack '
       'and no committee. Both lanes meet the last gate before go-live. After go-live come operations, '
       'review and retirement, and a material change means the tier is checked again at stage 2.')
s = Svg(880, 366, ALT)

W, H, GAP = 96, 48, 22
C1, C2 = 12, 130
C3 = C2 + W + 32                      # wider gap: the gate after stage 2, then the fork
COLS = [C3 + i * (W + GAP) for i in range(5)]   # stages 3 to 7
TOP_Y, FAST_Y = 50, 160
TOP_MID, FAST_MID = TOP_Y + H / 2, FAST_Y + H / 2
SHARED_Y = (TOP_MID + FAST_MID) / 2 - H / 2
SHARED_MID = SHARED_Y + H / 2
BAR_X, BAR_W = 850, 6                 # the last gate before go-live, across both lanes


def gate(x, y):
    """A gate: a short brick bar across the path."""
    s.line(f'M{x} {y - 10} L{x} {y + 10}', stroke=BRICK, sw=2.5)


def link(x1, x2, y):
    """Path from one stage to the next, with the gate in the gap."""
    s.arrow(x1, y, x2 - 1, y)
    gate(x1 + 8, y)


# Lane labels.
s.text(C3, TOP_Y - 12, 'T1 · T2 · SIGNERS OUTSIDE THE TEAM', size=10, fill=GREY, weight=500, box=480)
s.text(C3, FAST_Y - 12, 'FAST LANE · T3 · T4 · LIGHTER PACK, NO COMMITTEE', size=10, fill=GREY, weight=500, box=480)
s.text(BAR_X + BAR_W / 2, TOP_Y - 12, 'LIVE', size=10, fill=BRICK, anchor='middle', weight=500, box=40)

# Stages 1 and 2, shared by every tier.
s.box(C1, SHARED_Y, W, H, '1 INTAKE', 'sponsor named')
s.box(C2, SHARED_Y, W, H, '2 RISK, TIER', 'sets the lane')
link(C1 + W, C2, SHARED_MID)

# Gate after stage 2, then the fork into two lanes.
FORK_X = C3 - 12
s.line(f'M{C2 + W} {SHARED_MID} L{FORK_X} {SHARED_MID}')
gate(C2 + W + 8, SHARED_MID)
s.line(f'M{FORK_X} {TOP_MID} L{FORK_X} {FAST_MID}')
s.arrow(FORK_X, TOP_MID, C3 - 1, TOP_MID)
s.arrow(FORK_X, FAST_MID, C3 - 1, FAST_MID)

# Stages 3 to 7 in both lanes: same stages, different depth.
names = ['3 DESIGN', '4 DEVELOP', '5 EVALUATE', '6 SECURITY', '7 APPROVE']
top_sub = ['design review', 'prompt lead', 'independent', '100+ or 200+', 'outside team']
fast_sub = ['documented', 'peer or self', 'peer or self', 'T3 scan + 50', 'team lead']
for i, x in enumerate(COLS):
    s.box(x, TOP_Y, W, H, names[i], top_sub[i])
    s.box(x, FAST_Y, W, H, names[i], fast_sub[i])
    if i:
        link(COLS[i - 1] + W, x, TOP_MID)
        link(COLS[i - 1] + W, x, FAST_MID)

# Both lanes meet the last gate: the tier's evidence pack, checked and signed.
s.rect(BAR_X, TOP_Y, BAR_W, FAST_Y + H - TOP_Y, fill=BRICK, stroke=BRICK)
s.arrow(COLS[-1] + W, TOP_MID, BAR_X - 1, TOP_MID)
s.arrow(COLS[-1] + W, FAST_MID, BAR_X - 1, FAST_MID)

# After go-live: stages 8 to 10.
LOW_Y = 262
LOW_MID = LOW_Y + H / 2
low = [(COLS[0], '8 OPERATE', 'monitored'), (COLS[1], '9 REVIEW', 'tier cadence'), (COLS[2], '10 RETIRE', 'archived')]
for i, (x, t, sub) in enumerate(low):
    s.box(x, LOW_Y, W, H, t, sub)
    if i:
        s.arrow(low[i - 1][0] + W, LOW_MID, x - 1, LOW_MID)
s.text(COLS[0], LOW_Y - 10, 'AFTER GO-LIVE', size=10, fill=GREY, weight=500, box=110)

# From go-live round to stage 8, entering from the left.
RET_Y = 230
s.line(f'M{BAR_X + BAR_W / 2} {FAST_Y + H} L{BAR_X + BAR_W / 2} {RET_Y} L{FORK_X - 6} {RET_Y} L{FORK_X - 6} {LOW_MID}')
s.arrow(FORK_X - 6, LOW_MID, COLS[0] - 1, LOW_MID)

# Material change: the tier is checked again at stage 2.
x9, x2 = COLS[1] + W / 2, C2 + W / 2
LOOP_Y = 334
s.line(f'M{x9} {LOW_Y + H} L{x9} {LOOP_Y} L{x2} {LOOP_Y} L{x2} {SHARED_Y + H + 10}')
s.arrow(x2, SHARED_Y + H + 10, x2, SHARED_Y + H + 1)
s.text(x2 + 12, LOOP_Y + 16, 'material change: tier checked again', size=10, fill=GREY, box=230)

# Legend.
LX = 640
gate(LX + 6, 280)
s.text(LX + 20, 284, 'gate: blocks without evidence', size=10, fill=GREY, box=200)
s.rect(LX + 3, 300, BAR_W, 22, fill=BRICK, stroke=BRICK)
s.text(LX + 20, 315, 'last gate: pack and sign-off', size=10, fill=GREY, box=200)

s.save(os.path.join(os.path.dirname(__file__), '..', '..', 'public', 'assets', 'diagrams', 'gov-09-ten-stages.svg'))
