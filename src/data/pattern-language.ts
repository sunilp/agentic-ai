// The pattern language catalogue: the single source of truth for every field
// the /patterns/ index, PatternCard and llms.txt render. See
// docs/superpowers/specs/2026-08-21-agentic-pattern-language-design.md section 4
// for the authoritative tables this file transcribes.

export type Stage = 'design' | 'build' | 'evaluate' | 'operate' | 'govern';
export type Layer = 'capability' | 'control' | 'evidence';

type Attribution = { who: string; url: string; year?: number };
type Prior = { what: string; who: string; url: string };

type Common = {
  slug: string;
  name: string;
  kind: 'pattern' | 'anti-pattern';
  layer: Layer;
  primaryStage: Stage;
  alsoStages?: Stage[];
  oneLine: string;
  alsoKnownAs?: string[];
  related?: string[];
  blueprints?: string[];
  replacedBy?: string;
};

export type Entry = Common &
  (
    | { status: 'documented'; attributedTo: Attribution }
    | { status: 'restated'; nearestPrior: Prior[] }
    | { status: 'proposed' }
  );

export type Referenced = {
  slug: string;
  name: string;
  who: string;
  url: string;
  year?: number;
};

const ANTHROPIC_BUILDING_EFFECTIVE_AGENTS = 'https://www.anthropic.com/engineering/building-effective-agents';
const LIU_ET_AL = 'https://arxiv.org/abs/2405.10467';
const MICROSOFT_LEAST_PRIVILEGE =
  'https://www.microsoft.com/en-us/security/blog/2026/07/16/least-privilege-for-ai-agents-identity-access-and-tool-binding/';
const MAST = 'https://arxiv.org/abs/2503.13657';

export const ENTRIES: Entry[] = [
  // --- Capability: what the agent can do, and how it is built ---
  {
    slug: 'earn-the-complexity',
    name: 'Earn the Complexity',
    kind: 'pattern',
    layer: 'capability',
    primaryStage: 'design',
    oneLine: 'Every increment of autonomy is paid for by a measured eval delta.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Simplest-solution rule, find the simplest solution possible and only increase complexity when needed',
        who: 'Schluntz and Zhang, Anthropic',
        url: ANTHROPIC_BUILDING_EFFECTIVE_AGENTS,
      },
    ],
  },
  {
    slug: 'harness-engineering',
    name: 'Harness Engineering',
    kind: 'pattern',
    layer: 'capability',
    primaryStage: 'build',
    oneLine: 'Reliability lives in the scaffolding, not the model.',
    status: 'documented',
    attributedTo: { who: 'Sarang Sanjay Kulkarni', url: 'https://martinfowler.com/articles/reliable-llm-bayer.html', year: 2026 },
    blueprints: ['arch-008'],
  },
  {
    slug: 'tool-agent-registry',
    name: 'Tool/Agent Registry',
    kind: 'pattern',
    layer: 'capability',
    primaryStage: 'build',
    oneLine: 'The callable set is declared data, not whatever the runtime can reach.',
    status: 'documented',
    attributedTo: { who: 'Liu et al.', url: LIU_ET_AL, year: 2025 },
  },
  {
    slug: 'workflow-first',
    name: 'Workflow First',
    kind: 'pattern',
    layer: 'capability',
    primaryStage: 'design',
    oneLine: 'Default to a deterministic workflow; autonomy has to earn its place.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Workflow versus agent, predefined code paths for well-defined tasks, autonomous agents only where flexibility is required',
        who: 'Schluntz and Zhang, Anthropic',
        url: ANTHROPIC_BUILDING_EFFECTIVE_AGENTS,
      },
    ],
  },

  // --- Control: what constrains it at runtime ---
  {
    slug: 'approval-gate',
    name: 'Approval Gate',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'design',
    oneLine: 'Human authorization before an irreversible act, with defined timeout behaviour.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Human-in-the-Loop, a human approves before an agent proceeds past a checkpoint',
        who: 'Intelligence Patterns',
        url: 'https://agents.kour.me/human-in-the-loop/',
      },
      {
        what: 'Human Reflection, a human reviewer critiques the agent output before it proceeds',
        who: 'Liu et al.',
        url: LIU_ET_AL,
      },
    ],
  },
  {
    slug: 'attenuating-delegation',
    name: 'Attenuating Delegation',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'design',
    alsoStages: ['govern'],
    oneLine: 'Authority narrows at every hop and never widens.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Macaroons, attenuation by contextual caveat',
        who: 'Birgisson et al.',
        url: 'https://research.google/pubs/macaroons-cookies-with-contextual-caveats-for-decentralized-authorization-in-the-cloud/',
      },
    ],
    related: ['bounded-grant', 'authority-at-the-call-site'],
    blueprints: ['arch-005'],
  },
  {
    slug: 'authority-at-the-call-site',
    name: 'Authority at the Call Site',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'design',
    oneLine: 'The control sits where the tool call happens, not where the prompt was authored.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Complete mediation, every access to every object is checked for authority',
        who: 'Saltzer and Schroeder',
        url: 'https://doi.org/10.1109/PROC.1975.9939',
      },
      {
        what: 'Downstream authorization, the check happens at the tool call rather than at the prompt',
        who: 'Microsoft',
        url: MICROSOFT_LEAST_PRIVILEGE,
      },
    ],
  },
  {
    slug: 'bounded-grant',
    name: 'Bounded Grant',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'design',
    oneLine: 'Scope, magnitude, expiry, revocation, all four or none.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Least-privilege tool binding, a grant carries scope, magnitude and expiry rather than standing access',
        who: 'Microsoft',
        url: MICROSOFT_LEAST_PRIVILEGE,
      },
    ],
  },
  {
    slug: 'capability-gate',
    name: 'Capability Gate',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'build',
    oneLine: 'Destructive actions pass a gate the model cannot argue with.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Step-up approval for delete, export and privilege-change actions',
        who: 'Microsoft',
        url: MICROSOFT_LEAST_PRIVILEGE,
      },
      {
        what: 'Constrained Tool Use, tools are restricted by state, permission and policy',
        who: 'Intelligence Patterns',
        url: 'https://agents.kour.me/constrained-tool-use/',
      },
    ],
  },
  {
    slug: 'chokepoint-placement',
    name: 'Chokepoint Placement',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'design',
    oneLine: 'Placement sets the accuracy ceiling before you pick a model.',
    status: 'proposed',
    related: ['tiered-detection', 'verdict-composition'],
    blueprints: ['arch-001'],
  },
  {
    slug: 'escalation-path',
    name: 'Escalation Path',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'govern',
    oneLine: 'Where a blocked case goes, and who owns it when it gets there.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Escalation policies, ordered levels with per-level ownership and an acknowledgement timeout',
        who: 'PagerDuty',
        url: 'https://support.pagerduty.com/main/docs/escalation-policies',
      },
    ],
    blueprints: ['arch-005'],
  },
  {
    slug: 'fail-closed-degrade-on-exposure',
    name: 'Fail Closed, Degrade on Exposure',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'operate',
    oneLine: 'You cannot un-disclose, so degradation keys on exposure, not harm family.',
    status: 'proposed',
    blueprints: ['arch-008'],
  },
  {
    slug: 'tiered-detection',
    name: 'Tiered Detection',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'operate',
    oneLine: 'Cheap on everything, expensive on the band, subject to the escalation fraction.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Attentional cascade, cheap classifiers discard most candidates so expensive ones run on the remainder',
        who: 'Viola and Jones',
        url: 'https://doi.org/10.1109/CVPR.2001.990517',
      },
    ],
    blueprints: ['arch-008'],
  },
  {
    slug: 'verdict-composition',
    name: 'Verdict Composition',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'build',
    oneLine: 'Compose verdicts; never average scores that do not mean the same thing.',
    status: 'proposed',
    blueprints: ['arch-002'],
  },
  {
    slug: 'verifier-loop',
    name: 'Verifier Loop',
    kind: 'pattern',
    layer: 'control',
    primaryStage: 'build',
    oneLine: 'A deterministic verifier checks each step against the original task.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Planner-Checker, a checker validates each planner step against the task',
        who: 'Intelligence Patterns',
        url: 'https://agents.kour.me/planner-checker/',
      },
      {
        what: 'Evaluator-optimizer, one call generates and another evaluates against explicit criteria',
        who: 'Schluntz and Zhang, Anthropic',
        url: ANTHROPIC_BUILDING_EFFECTIVE_AGENTS,
      },
      {
        what: 'Cross-Reflection, a separate agent instance critiques the output before it is accepted',
        who: 'Liu et al.',
        url: LIU_ET_AL,
      },
    ],
  },

  // --- Evidence: what it can prove, and how it stays honest ---
  {
    slug: 'baseline-and-floor',
    name: 'Baseline and Floor',
    kind: 'pattern',
    layer: 'evidence',
    primaryStage: 'evaluate',
    oneLine: 'A gate needs both, or cumulative sub-threshold drops halve recall.',
    status: 'proposed',
    blueprints: ['arch-006'],
  },
  {
    slug: 'decision-record',
    name: 'Decision Record',
    kind: 'pattern',
    layer: 'evidence',
    primaryStage: 'build',
    oneLine: 'Every enforced action leaves a replayable record carrying its policy version.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'End-to-end action record, an audit log entry with identity, scope, resource and correlation id',
        who: 'Microsoft',
        url: MICROSOFT_LEAST_PRIVILEGE,
      },
    ],
  },
  {
    slug: 'failure-buckets',
    name: 'Failure Buckets',
    kind: 'pattern',
    layer: 'evidence',
    primaryStage: 'evaluate',
    oneLine: 'A rubric that scores without bucketing cannot tell you what to fix.',
    status: 'proposed',
  },
  {
    slug: 'shadow-before-enforce',
    name: 'Shadow Before Enforce',
    kind: 'pattern',
    layer: 'evidence',
    primaryStage: 'operate',
    oneLine: 'A control records before it is allowed to act.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Dark launching, the component does all its real work while nobody can see it doing it',
        who: 'Martin Fowler',
        url: 'https://martinfowler.com/bliki/DarkLaunching.html',
      },
    ],
    blueprints: ['arch-006'],
  },
  {
    slug: 'split-the-log',
    name: 'Split the Log',
    kind: 'pattern',
    layer: 'evidence',
    primaryStage: 'build',
    oneLine: 'Three stores, three retentions, three audiences; merging them fails both ways.',
    status: 'proposed',
    blueprints: ['arch-007'],
  },
  {
    slug: 'the-expiring-exception',
    name: 'The Expiring Exception',
    kind: 'pattern',
    layer: 'evidence',
    primaryStage: 'govern',
    oneLine: 'An exception with a mandatory expiry is a control; without one it is a hole.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Temporary access granted without an expiry date routinely becomes permanent access',
        who: 'Microsoft',
        url: MICROSOFT_LEAST_PRIVILEGE,
      },
    ],
  },

  // --- Anti-patterns ---
  {
    slug: 'hallucinated-done',
    name: 'Hallucinated Done',
    kind: 'anti-pattern',
    layer: 'evidence',
    primaryStage: 'evaluate',
    oneLine: 'The agent declares the task done with no check that it actually is.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Premature Termination, a multi-agent system stops before the task is genuinely complete',
        who: 'Cemri et al. (MAST)',
        url: MAST,
      },
    ],
    replacedBy: 'verifier-loop',
  },
  {
    slug: 'rubber-stamp-verifier',
    name: 'Rubber-Stamp Verifier',
    kind: 'anti-pattern',
    layer: 'evidence',
    primaryStage: 'evaluate',
    oneLine: 'A verifier that approves everything is not verifying anything.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Incorrect Verification, a verifier accepts an output without properly checking it against the task',
        who: 'Cemri et al. (MAST)',
        url: MAST,
      },
    ],
    replacedBy: 'verifier-loop',
  },
  {
    slug: 'silent-fail-open',
    name: 'Silent Fail Open',
    kind: 'anti-pattern',
    layer: 'control',
    primaryStage: 'operate',
    oneLine: 'When the control fails, the action goes through and nobody is told.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Not failing securely, a control that fails open instead of closed',
        who: 'MITRE, CWE-636',
        url: 'https://cwe.mitre.org/data/definitions/636.html',
      },
      {
        what: 'Fail securely, an error path must not grant access it would otherwise deny',
        who: 'OWASP',
        url: 'https://owasp.org/www-community/Fail_securely',
      },
    ],
    replacedBy: 'fail-closed-degrade-on-exposure',
  },
  {
    slug: 'the-uncalibrated-ensemble',
    name: 'The Uncalibrated Ensemble',
    kind: 'anti-pattern',
    layer: 'control',
    primaryStage: 'build',
    oneLine: 'Averaging scores that were never on the same scale manufactures false confidence.',
    status: 'proposed',
    replacedBy: 'verdict-composition',
  },
  {
    slug: 'workflow-in-an-agent-costume',
    name: 'Workflow in an Agent Costume',
    kind: 'anti-pattern',
    layer: 'capability',
    primaryStage: 'design',
    oneLine: 'A fixed sequence dressed as autonomy, buying unpredictability without earning the benefit.',
    status: 'restated',
    nearestPrior: [
      {
        what: 'Workflow versus agent, predefined code paths for well-defined tasks, autonomous agents only where flexibility is required',
        who: 'Schluntz and Zhang, Anthropic',
        url: ANTHROPIC_BUILDING_EFFECTIVE_AGENTS,
      },
    ],
    replacedBy: 'workflow-first',
  },
];

export const REFERENCED: Referenced[] = [
  { slug: 'prompt-chaining', name: 'Prompt Chaining', who: 'Schluntz and Zhang, Anthropic', url: ANTHROPIC_BUILDING_EFFECTIVE_AGENTS, year: 2024 },
  { slug: 'routing', name: 'Routing', who: 'Schluntz and Zhang, Anthropic', url: ANTHROPIC_BUILDING_EFFECTIVE_AGENTS, year: 2024 },
  { slug: 'parallelization', name: 'Parallelization', who: 'Schluntz and Zhang, Anthropic', url: ANTHROPIC_BUILDING_EFFECTIVE_AGENTS, year: 2024 },
  { slug: 'orchestrator-workers', name: 'Orchestrator-workers', who: 'Schluntz and Zhang, Anthropic', url: ANTHROPIC_BUILDING_EFFECTIVE_AGENTS, year: 2024 },
  { slug: 'evaluator-optimizer', name: 'Evaluator-optimizer', who: 'Schluntz and Zhang, Anthropic', url: ANTHROPIC_BUILDING_EFFECTIVE_AGENTS, year: 2024 },
  { slug: 'self-reflection', name: 'Self-Reflection', who: 'Liu et al.', url: LIU_ET_AL, year: 2025 },
  { slug: 'cross-reflection', name: 'Cross-Reflection', who: 'Liu et al.', url: LIU_ET_AL, year: 2025 },
  { slug: 'human-reflection', name: 'Human Reflection', who: 'Liu et al.', url: LIU_ET_AL, year: 2025 },
  { slug: 'rag', name: 'Retrieval Augmented Generation (RAG)', who: 'Subramaniam and Fowler', url: 'https://martinfowler.com/articles/gen-ai-patterns/', year: 2025 },
  { slug: 'hybrid-retriever', name: 'Hybrid Retriever', who: 'Subramaniam and Fowler', url: 'https://martinfowler.com/articles/gen-ai-patterns/', year: 2025 },
  { slug: 'query-rewriting', name: 'Query Rewriting', who: 'Subramaniam and Fowler', url: 'https://martinfowler.com/articles/gen-ai-patterns/', year: 2025 },
  { slug: 'reranker', name: 'Reranker', who: 'Subramaniam and Fowler', url: 'https://martinfowler.com/articles/gen-ai-patterns/', year: 2025 },
  { slug: 'attention-engineering', name: 'Attention Engineering', who: 'Intelligence Patterns', url: 'https://agents.kour.me/attention-engineering/' },
  { slug: 'context-editing', name: 'Context Editing', who: 'Intelligence Patterns', url: 'https://agents.kour.me/context-editing/' },
  { slug: 'filesystem-as-context', name: 'Filesystem as Context', who: 'Intelligence Patterns', url: 'https://agents.kour.me/external-memory/' },
  { slug: 'constrained-tool-use', name: 'Constrained Tool Use', who: 'Intelligence Patterns', url: 'https://agents.kour.me/constrained-tool-use/' },
];

export const RETIRED: Record<string, string> = {
  'agent-loop': '/patterns/',
  'approval-gate': '/patterns/#approval-gate',
  'cold-start-mitigation': '/patterns/',
  'earn-the-complexity': '/patterns/#earn-the-complexity',
  'escalation-path': '/patterns/#escalation-path',
  'eval-loop': '/patterns/#failure-buckets',
  'failure-buckets': '/patterns/#failure-buckets',
  'hub-and-spoke': '/patterns/#orchestrator-workers',
  'tool-registry': '/patterns/#tool-agent-registry',
  'trace-the-truth': '/patterns/#split-the-log',
  'verifier-loop': '/patterns/#verifier-loop',
  'workflow-first': '/patterns/#workflow-first',
};

export function bySlug(slug: string): Entry | undefined {
  return ENTRIES.find((e) => e.slug === slug);
}

export function byLayer(layer: Layer): Entry[] {
  return ENTRIES.filter((e) => e.layer === layer).sort((a, b) => a.name.localeCompare(b.name));
}

export function byStage(stage: Stage): Entry[] {
  return ENTRIES
    .filter((e) => e.primaryStage === stage || (e.alsoStages ?? []).includes(stage))
    .sort((a, b) => a.name.localeCompare(b.name));
}

export function counts() {
  const stages = { design: 0, build: 0, evaluate: 0, operate: 0, govern: 0 } as Record<Stage, number>;
  for (const e of ENTRIES) stages[e.primaryStage] += 1;
  return {
    total: ENTRIES.length,
    patterns: ENTRIES.filter((e) => e.kind === 'pattern').length,
    antiPatterns: ENTRIES.filter((e) => e.kind === 'anti-pattern').length,
    documented: ENTRIES.filter((e) => e.status === 'documented').length,
    restated: ENTRIES.filter((e) => e.status === 'restated').length,
    proposed: ENTRIES.filter((e) => e.status === 'proposed').length,
    stages,
  };
}
