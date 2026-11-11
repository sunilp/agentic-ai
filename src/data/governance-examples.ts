/**
 * The six worked examples from ai-governance-framework v2.1.0 (examples/<slug>/risk-assessment.md),
 * with the dimension scores, override items and tiers those files record. The test checks that the
 * framework's own rule reproduces every recorded tier.
 */
import type { Tier, TierInput } from '~/lib/governance-tier';

export interface WorkedExample extends TierInput {
  slug: string;
  name: string;
  matrix: 'Traditional ML' | 'GenAI';
  recordedTier: Tier;
  rationale?: string;
}

const genai = (h: string, d: string, p: string, o: string, t: string) => [
  { name: 'Hallucination severity', level: h },
  { name: 'Data exposure risk', level: d },
  { name: 'Prompt injection susceptibility', level: p },
  { name: 'Output controllability', level: o },
  { name: 'Third-party model dependency', level: t },
] as TierInput['dimensions'];

const ml = (a: string, s: string, r: string, v: string, i: string) => [
  { name: 'Decision autonomy', level: a },
  { name: 'Data sensitivity', level: s },
  { name: 'Regulatory exposure', level: r },
  { name: 'Reversibility', level: v },
  { name: 'Scale of impact', level: i },
] as TierInput['dimensions'];

export const EXAMPLES: WorkedExample[] = [
  {
    slug: 'internal-knowledge-search', name: 'Internal knowledge search', matrix: 'GenAI',
    dimensions: genai('Medium', 'Medium', 'Low', 'Low', 'Medium'), overrides: [], recordedTier: 'T3',
  },
  {
    slug: 'document-summarization', name: 'Regulatory document summarisation', matrix: 'GenAI',
    dimensions: genai('High', 'High', 'Low', 'Low', 'High'), overrides: [], recordedTier: 'T2',
  },
  {
    slug: 'customer-service-chatbot', name: 'Customer service chatbot', matrix: 'GenAI',
    dimensions: genai('High', 'Critical', 'High', 'High', 'High'), overrides: [2, 8], recordedTier: 'T1',
  },
  {
    slug: 'credit-scoring-model', name: 'Credit scoring model', matrix: 'Traditional ML',
    dimensions: ml('Critical', 'Critical', 'Critical', 'High', 'Critical'), overrides: [1], recordedTier: 'T1',
  },
  {
    slug: 'fraud-detection', name: 'Fraud detection', matrix: 'Traditional ML',
    dimensions: ml('High', 'High', 'Medium', 'Medium', 'Critical'), overrides: [], recordedTier: 'T1',
  },
  {
    slug: 'agentic-research-assistant', name: 'Agentic research assistant', matrix: 'GenAI',
    dimensions: genai('High', 'High', 'Medium', 'Medium', 'High'), overrides: [6],
    approverRaisedTo: 'T1', recordedTier: 'T1',
    rationale: 'The AI Risk Committee raised the pilot to T1: it sends confidential research data to an external vendor API, plans and runs multi-step tool use within a session, and its drafts feed research distributed under MiFID II.',
  },
];
