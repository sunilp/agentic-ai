/**
 * The framework's tiering rule (ai-governance-framework v2.1.0,
 * framework/risk-classification/risk-matrix.md "Classification Criteria" and
 * genai-risk-matrix.md "Tier Override Rules"):
 *   Step 0: a prohibited use is rejected, not tiered.
 *   The highest-scoring dimension sets the tier.
 *   Overrides can raise the tier, never lower it.
 *   The approver may raise a tier with a recorded rationale. Nobody can lower it below what scoring and overrides give.
 */
export type Level = 'Low' | 'Medium' | 'High' | 'Critical';
export type Tier = 'T1' | 'T2' | 'T3' | 'T4';

export const LEVEL_TIER: Record<Level, Tier> = { Critical: 'T1', High: 'T2', Medium: 'T3', Low: 'T4' };
const RANK: Record<Tier, number> = { T1: 1, T2: 2, T3: 3, T4: 4 }; // lower is stricter

export interface Override { item: number; floor: Tier; text: string }

/** The canonical override list, numbered as in genai-risk-matrix.md. */
export const OVERRIDES: Override[] = [
  { item: 1, floor: 'T1', text: 'Makes or directly influences a regulated decision (credit, insurance underwriting or pricing, AML or sanctions, employment)' },
  { item: 2, floor: 'T1', text: 'Generates customer-facing content with no per-output human review' },
  { item: 3, floor: 'T1', text: 'Processes customer personal data through an external LLM API without all four safeguards' },
  { item: 4, floor: 'T1', text: 'Agent with write access to production systems or data stores, or authority to move money, contact customers or change access' },
  { item: 5, floor: 'T1', text: 'Biometrics, deepfake-capable synthetic media, voice cloning or medical imagery' },
  { item: 6, floor: 'T2', text: 'Any agentic system, including read-only tool use, or any multi-agent system' },
  { item: 7, floor: 'T2', text: 'Other synthetic media generation' },
  { item: 8, floor: 'T2', text: 'Processes customer personal data through an external LLM API with all four safeguards' },
  { item: 9, floor: 'T2', text: 'Personal data in visual content' },
];

/** Rows of the "what the tier changes" table: a governance-policy.json tier field and its label. */
export const TIER_ROWS = [
  ['approver', 'Approves the risk assessment'],
  ['validation', 'Independent validation'],
  ['redTeam', 'Red-team depth (GenAI systems)'],
  ['metricsReview', 'Metrics review'],
  ['reviewCadence', 'Formal governance review'],
  ['revalidation', 'Revalidation'],
] as const;

export interface TierInput {
  prohibited?: boolean;
  dimensions: { name: string; level: Level }[];
  overrides: number[];
  approverRaisedTo?: Tier;
}

export interface TierResult {
  tier: Tier | 'rejected';
  scored?: Tier;
  reasons: string[];
}

export function computeTier(input: TierInput): TierResult {
  if (input.prohibited) {
    return { tier: 'rejected', reasons: ['It matches a prohibited use, so it is rejected at Step 0, not tiered.'] };
  }
  if (input.dimensions.length === 0) throw new Error('at least one scored dimension is required');

  const top = input.dimensions.reduce((a, d) => (RANK[LEVEL_TIER[d.level]] < RANK[LEVEL_TIER[a.level]] ? d : a));
  const scored = LEVEL_TIER[top.level];
  const reasons = [`Highest dimension: ${top.name}, ${top.level}, gives ${scored}.`];
  let tier: Tier = scored;

  for (const item of input.overrides) {
    const o = OVERRIDES.find((x) => x.item === item);
    if (!o) throw new Error(`unknown override item ${item}`);
    if (RANK[o.floor] < RANK[tier]) {
      tier = o.floor;
      reasons.push(`Override ${item} raises it to ${tier}.`);
    } else {
      reasons.push(`Override ${item} applies but does not change ${tier}.`);
    }
  }

  if (input.approverRaisedTo) {
    if (RANK[input.approverRaisedTo] < RANK[tier]) {
      tier = input.approverRaisedTo;
      reasons.push(`The approver raised it to ${tier}, with a recorded rationale.`);
    } else if (RANK[input.approverRaisedTo] > RANK[tier]) {
      reasons.push(`The approver cannot lower a tier, so ${tier} stands.`);
    }
  }

  return { tier, scored, reasons };
}
