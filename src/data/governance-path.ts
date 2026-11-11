/**
 * AI Governance, from Scratch: the path.
 *
 * Single source of truth for the guide's 22 steps. Essays live at
 * src/content/governance/<slug>.mdx and join on slug. A step with no essay
 * still appears on the hub, as text with no link.
 *
 * Spec: docs/superpowers/specs/2026-11-11-governance-guide-design.md, section 3.
 */

export type Part = 'I' | 'II' | 'III' | 'IV' | 'V' | 'VI' | 'Close';

export const PARTS: Part[] = ['I', 'II', 'III', 'IV', 'V', 'VI', 'Close'];

export const PART_LABEL: Record<Part, string> = {
  I: 'Foundations',
  II: 'People before process',
  III: 'Setting it up',
  IV: 'Responsible AI in depth',
  V: 'GenAI and agents',
  VI: 'Enterprise scale',
  Close: 'Close',
};

export interface Book {
  title: string;
  url?: string; // omitted for forthcoming books
  note: string;
}

export interface Step {
  n: number;
  slug: string;
  part: Part;
  title: string; // the instruction
  short: string; // the machine label
  checklist: { item: string; response: string };
  doneWhen: string;
  doneWhenSmall?: string;
  /** What keeps the step done after the first pass. Written with each essay. */
  keptWhen?: string;
  keptWhenSmall?: string;
  /** Who runs the working session for this step and what goes in and comes out. Written with each essay. */
  session?: { lead: string; leadSmall?: string; with: string; withSmall?: string; bring: string; leave: string };
  restsOn: number[];
  patterns: string[]; // pattern-language slugs
  deepDive: string[];
  call: string;
  kit: string[]; // framework repo paths at FRAMEWORK_TAG
  book?: Book;
  related: string[]; // architecture collection ids (filenames)
}

/** What the published steps add up to, and what comes next. Update with each release. */
export const RELEASE = {
  covers: 'your purpose, mandate, policy, register and risk tiers',
  next: 'Part II, People before process',
};

export const FRAMEWORK_REPO = 'https://github.com/sunilp/ai-governance-framework';
export const FRAMEWORK_TAG = 'v2.2.0';
export const kitUrl = (path: string) => `${FRAMEWORK_REPO}/blob/${FRAMEWORK_TAG}/${path}`;

const KIT_WORDS: Record<string, string> = {
  ai: 'AI', genai: 'GenAI', llm: 'LLM', rag: 'RAG', grc: 'GRC', eu: 'EU', iso: 'ISO', nist: 'NIST', rmf: 'RMF', coe: 'CoE', raci: 'RACI',
};
/** A readable name for a framework file: 'templates/ai-policy.md' -> 'AI policy'. */
export function kitLabel(path: string): string {
  const parts = path.split('/');
  const file = parts[parts.length - 1].replace(/\.(md|ya?ml)$/, '');
  const parent = parts.length > 1 ? parts[parts.length - 2] : '';
  // Files whose own name says little take their folder's name.
  const stem =
    file === 'README' ? (parent ? `${parent} overview` : 'framework overview')
    : file === 'START-HERE' ? 'start here'
    : file === 'governance' || file === 'governance-case-file' ? `${parent} ${file.replace('governance-', '').replace('governance', 'gate input')}`
    : /^stage-\d+-/.test(file) ? `${file.replace(/^stage-\d+-/, '')} controls`
    : file;
  const words = stem.toLowerCase().split(/[-\s]+/).filter(Boolean).map((w) => KIT_WORDS[w] ?? w);
  const text = words.join(' ').replace(/\biso (\d+)/i, 'ISO/IEC $1').replace('AI act', 'AI Act');
  return text.charAt(0).toUpperCase() + text.slice(1);
}

const AAFSE = { title: 'Agentic AI for Serious Engineers', url: 'https://www.amazon.com/dp/B0GVG6848F' };
const EVERY_STEP_BEFORE_22 = Array.from({ length: 21 }, (_, i) => i + 1);

export const STEPS: Step[] = [
  {
    n: 1, slug: '01-agree-what-governance-is-for', part: 'I',
    title: 'Agree what governance is for', short: 'Purpose',
    checklist: { item: 'PURPOSE', response: 'AGREED' },
    doneWhen: 'Your sponsor can explain, in a minute, why it makes delivery faster.',
    keptWhen: 'People who were not in the room can say who decides and what evidence they need.',
    session: {
      lead: 'Whoever is standing governance up',
      with: 'Your sponsor',
      bring: 'The name of whoever could stop a model from shipping today',
      leave: 'One agreed paragraph: decisions, owners, evidence, and why it speeds delivery',
    },
    restsOn: [], patterns: [],
    deepDive: ['decisions, owners, evidence', 'what governance is not'],
    call: 'Governance exists to make safe delivery faster.',
    kit: ['README.md', 'START-HERE.md'], related: [],
  },
  {
    n: 2, slug: '02-mandate-and-one-page-policy', part: 'I',
    title: 'Get a mandate and a one-page AI policy', short: 'Mandate and policy',
    checklist: { item: 'MANDATE, POLICY', response: 'OWNED · PUBLISHED' },
    doneWhen: 'An executive owns AI risk, and the policy is published.',
    keptWhen: 'Three engineers picked at random can quote a rule and name its owner.',
    session: {
      lead: 'You, drafting for the executive who will own AI risk',
      with: 'The CRO, the AI Risk Committee and the Board Risk Committee',
      withSmall: 'The CTO, or a founder',
      bring: "Step 1's paragraph, and any policy you have or were about to copy",
      leave: 'A named executive owner, a written risk appetite and a published one-page policy',
    },
    restsOn: [1], patterns: [],
    deepDive: ['risk appetite', 'acceptable use', 'principles you can test'],
    call: 'One page, one executive owner. A policy nobody can test is a wish.',
    kit: ['templates/ai-policy.md', 'framework/operating-model/acceptable-use.md', 'templates/ai-risk-committee-charter.md'],
    related: [],
  },
  {
    n: 3, slug: '03-list-every-ai-system', part: 'I',
    title: 'List every AI system', short: 'Register',
    checklist: { item: 'REGISTER', response: 'COMPLETE' },
    doneWhen: 'Nothing reaches production without a register entry.',
    doneWhenSmall: 'Every system is listed in one file in a repo, and no model credential is issued without an entry.',
    keptWhen: 'The quarterly check against what is running finds nothing without an entry.',
    keptWhenSmall: 'The monthly sweep of cloud accounts and SaaS settings finds nothing without an entry.',
    session: {
      lead: 'AI Risk, which owns the register',
      leadSmall: 'The team lead, who owns the file',
      with: 'Procurement, finance, security and whoever runs your cloud accounts and SaaS tools',
      bring: 'The one-page policy, and access to contracts, bills, repositories and admin consoles',
      leave: 'One entry per AI system, and a gate that issues no production credential without one',
    },
    restsOn: [2], patterns: ['tool-agent-registry'],
    deepDive: ['shadow and vendor AI', 'agents as entries', 'model lineage'],
    call: 'The register is the gate: no entry, no production credential.',
    kit: ['templates/ai-inventory-entry.yaml', 'framework/governance-operations/ai-inventory.md'],
    related: [],
  },
  {
    n: 4, slug: '04-tier-every-system', part: 'I',
    title: 'Tier every system, and say no to some', short: 'Tier',
    checklist: { item: 'TIER', response: 'SET · SOME SAID NO' },
    doneWhen: 'Each entry has a tier, and the tier changes what it must pass.',
    doneWhenSmall: 'Each entry has a tier, and the tier decides who signs it off and what it must pass.',
    keptWhen: 'Every tier is checked again at each formal review and on each material change.',
    session: {
      lead: 'The product owner, who prepares each assessment',
      leadSmall: 'The team lead, who scores each system',
      with: 'The approver for each tier, and an independent validator for T1 and T2',
      bring: 'The register, your prohibited list from Step 2 and the risk matrices',
      leave: 'A tier on every entry, with its scores, overrides and approver recorded',
    },
    restsOn: [3], patterns: ['earn-the-complexity', 'workflow-first'],
    deepDive: ['overrides', 'agentic risk', 're-tiering', 'six worked examples'],
    call: 'Govern by tier, not by project. Decide the prohibited list before the first request.',
    kit: [
      'framework/risk-classification/risk-matrix.md',
      'framework/risk-classification/genai-risk-matrix.md',
      'framework/governance-operations/when-to-say-no.md',
      'templates/genai-use-case-assessment.md',
    ],
    related: [],
  },
  {
    n: 5, slug: '05-where-engineers-route-around-you', part: 'II',
    title: 'Find where your engineers will route around you', short: 'Known shortcuts',
    checklist: { item: 'SHORTCUTS', response: 'NAMED' },
    doneWhen: 'You can name the three shortcuts your teams take most.',
    restsOn: [1], patterns: [],
    deepDive: ['present bias', 'the demo that became production', 'normalised deviance'],
    call: 'A shortcut tells you something about your process.',
    kit: ['START-HERE.md'], related: [],
  },
  {
    n: 6, slug: '06-make-the-governed-path-fastest', part: 'II',
    title: 'Make the governed path the fastest path', short: 'Paved road',
    checklist: { item: 'PAVED ROAD', response: 'FASTEST' },
    doneWhen: 'The paved road is quicker than the workaround.',
    restsOn: [3, 5], patterns: ['harness-engineering', 'shadow-before-enforce'],
    deepDive: ['forcing functions', 'guardrails not gates', 'risk budgets'],
    call: 'Make the safe way the easy way, and enforce it in the pipeline, not in a meeting.',
    kit: ['reference-implementations/README.md', 'examples/customer-service-chatbot/governance.yaml'],
    related: [],
  },
  {
    n: 7, slug: '07-a-culture-that-reports-problems', part: 'II',
    title: 'Build a culture that reports problems', short: 'Reporting culture',
    checklist: { item: 'NEAR-MISSES', response: 'REPORTED · THANKED' },
    doneWhen: 'Someone reported a near-miss and was thanked for it.',
    restsOn: [5], patterns: [],
    deepDive: ['just culture', 'blameless review', 'the brilliant rule-breaker'],
    call: 'Thank people for near-misses. A culture that hides problems defeats every control.',
    kit: ['framework/operating-model/incident-forensics.md', 'templates/incident-report-genai.md'],
    related: [],
  },
  {
    n: 8, slug: '08-owners-and-decision-rights', part: 'III',
    title: 'Name owners and decision rights', short: 'Owners',
    checklist: { item: 'OWNERS', response: 'ONE PER DECISION' },
    doneWhen: 'Every decision has one accountable person.',
    restsOn: [2, 4], patterns: ['decision-record', 'escalation-path'],
    deepDive: ['three lines', 'separation of duties', 'approvals by tier'],
    call: 'Builders never validate their own high-risk systems.',
    kit: [
      'framework/operating-model/roles-responsibilities.md',
      'framework/operating-model/roles-genai.md',
      'framework/operating-model/escalation-paths.md',
    ],
    related: ['005-ownership-and-decision-rights'],
  },
  {
    n: 9, slug: '09-gates-between-idea-and-production', part: 'III',
    title: 'Put gates between idea and production', short: 'Gates',
    checklist: { item: 'GATES', response: 'ENFORCED BY TIER' },
    doneWhen: "A system can't deploy without its tier's evidence pack.",
    restsOn: [4, 6, 8], patterns: ['approval-gate', 'capability-gate'],
    deepDive: ['the ten stages', 'fast lane', 'retroactive governance'],
    call: "A gate that can't stop a release isn't a gate.",
    kit: [
      'framework/governance-operations/governance-workflow.md',
      'framework/llm-lifecycle/deployment-gates.md',
      'framework/governance-operations/control-register.md',
    ],
    related: ['006-the-guardrail-lifecycle'],
  },
  {
    n: 10, slug: '10-evidence-that-blocks-releases', part: 'III',
    title: 'Make evidence block releases', short: 'Evidence that blocks',
    checklist: { item: 'EVIDENCE', response: 'BLOCKS RELEASES' },
    doneWhen: 'A failing evaluation has stopped a release.',
    restsOn: [9], patterns: ['baseline-and-floor', 'verifier-loop', 'rubber-stamp-verifier'],
    deepDive: ['suite sizes', 'confidence bounds', 'red-team independence'],
    call: 'A gate that has never said no has not been tested.',
    kit: [
      'framework/llm-lifecycle/evaluation-governance.md',
      'framework/ai-security/red-teaming-protocol.md',
      'templates/red-team-report.md',
    ],
    book: { ...AAFSE, note: 'Chapter 6 goes deeper on evaluation suites that can stop a release.' },
    related: ['003-measuring-detectors', '006-the-guardrail-lifecycle'],
  },
  {
    n: 11, slug: '11-run-watch-respond-review-retire', part: 'III',
    title: 'Run it: watch, respond, review, retire', short: 'Run and respond',
    checklist: { item: 'OPERATIONS', response: 'DRILLED' },
    doneWhen: 'An incident drill has run end to end.',
    restsOn: [7, 9],
    patterns: ['escalation-path', 'fail-closed-degrade-on-exposure', 'the-expiring-exception', 'silent-fail-open'],
    deepDive: ['drift', 'kill switches', 'exceptions that expire', 'retirement'],
    call: 'Every exception expires. Every system has a way to stop.',
    kit: [
      'framework/llm-lifecycle/monitoring.md',
      'templates/incident-report-template.md',
      'templates/exception-register.md',
      'framework/operating-model/review-cadence.md',
    ],
    related: ['007-telemetry-audit-and-review', '008-production-execution'],
  },
  {
    n: 12, slug: '12-turn-principles-into-tests', part: 'IV',
    title: 'Turn principles into tests', short: 'Tests',
    checklist: { item: 'PRINCIPLES', response: 'TESTED' },
    doneWhen: 'Every principle in your policy has a test and an owner.',
    restsOn: [2, 10], patterns: ['baseline-and-floor', 'failure-buckets'],
    deepDive: ['impact assessment', 'stakeholder input'],
    call: 'A principle without a test is a slogan.',
    kit: ['framework/compliance/responsible-ai-checklist.md', 'templates/impact-assessment-template.md'],
    related: [],
  },
  {
    n: 13, slug: '13-choose-your-fairness-trade-off', part: 'IV',
    title: 'Choose your fairness trade-off on purpose', short: 'Fairness',
    checklist: { item: 'FAIRNESS', response: 'CHOSEN · SIGNED' },
    doneWhen: 'The fairness metric was chosen, written down and signed.',
    restsOn: [12], patterns: [],
    deepDive: ['why the metrics conflict', 'LLM bias testing'],
    call: 'You cannot satisfy every fairness metric at once, so choose one in the open.',
    kit: ['framework/responsible-ai/bias-detection-llm.md'], related: [],
  },
  {
    n: 14, slug: '14-explain-disclose-allow-appeal', part: 'IV',
    title: 'Explain, disclose and allow appeal', short: 'Explain · appeal',
    checklist: { item: 'EXPLANATION, APPEAL', response: 'AVAILABLE' },
    doneWhen: 'An affected person can find out, and contest the outcome.',
    restsOn: [12], patterns: [],
    deepDive: ['explanations by audience', 'disclosure and marking', 'recourse'],
    call: 'If a person cannot contest it, you have not explained it.',
    kit: ['framework/responsible-ai/transparency-standards.md', 'templates/model-card-template.yaml'],
    related: [],
  },
  {
    n: 15, slug: '15-make-human-oversight-real', part: 'IV',
    title: 'Make human oversight real', short: 'Oversight',
    checklist: { item: 'OVERSIGHT', response: 'CAN OVERRULE' },
    doneWhen: 'Reviewers can, and sometimes do, overrule the system.',
    restsOn: [8, 12], patterns: ['approval-gate', 'escalation-path', 'rubber-stamp-verifier'],
    deepDive: ['automation bias', 'in, on and over the loop'],
    call: 'A human who never overrules is a rubber stamp, not oversight.',
    kit: ['framework/responsible-ai/human-in-loop-patterns.md'],
    book: { ...AAFSE, note: 'Chapter 5 covers human-in-the-loop design for agent systems in depth.' },
    related: ['004-the-decision-layer'],
  },
  {
    n: 16, slug: '16-bound-reliability-safety-privacy', part: 'IV',
    title: 'Bound reliability, safety and privacy', short: 'Safety · privacy',
    checklist: { item: 'LIMITS', response: 'TESTED PER TIER' },
    doneWhen: 'Hallucination, abuse and leak limits are tested per tier.',
    restsOn: [10, 12], patterns: ['tiered-detection', 'verdict-composition', 'the-uncalibrated-ensemble'],
    deepDive: ['hallucination policy', 'data minimisation', 'provenance'],
    call: 'Set the limit before you measure, not after.',
    kit: ['framework/responsible-ai/hallucination-policy.md', 'framework/ai-security/adversarial-robustness.md'],
    related: ['002-detector-architecture'],
  },
  {
    n: 17, slug: '17-govern-models-vendors-prompts-retrieval', part: 'V',
    title: 'Govern models, vendors, prompts and retrieval', short: 'Models · prompts · RAG',
    checklist: { item: 'MODELS, PROMPTS', response: 'VERSIONED · REVIEWED' },
    doneWhen: 'Prompts and model versions are reviewed and versioned like code.',
    restsOn: [9, 10], patterns: ['earn-the-complexity', 'workflow-in-an-agent-costume', 'hallucinated-done'],
    deepDive: ['vendor exit plans', 'RAG permissions', 'fine-tuning', 'deprecation'],
    call: 'A prompt change is a code change.',
    kit: [
      'framework/llm-lifecycle/model-selection.md',
      'framework/llm-lifecycle/prompt-engineering-standards.md',
      'framework/llm-lifecycle/rag-governance.md',
      'framework/compliance/third-party-model-risk.md',
    ],
    related: [],
  },
  {
    n: 18, slug: '18-agents-identity-and-bounded-authority', part: 'V',
    title: 'Give agents identity and bounded authority', short: 'Agent identity · authority',
    checklist: { item: 'AGENT AUTHORITY', response: 'GRANTED · BOUNDED' },
    doneWhen: "No agent can call a tool it wasn't granted.",
    restsOn: [3, 9, 15],
    patterns: ['attenuating-delegation', 'bounded-grant', 'authority-at-the-call-site', 'chokepoint-placement'],
    deepDive: ['delegation chains', 'tool authority', 'multi-agent risk'],
    call: 'Agents get identity and least authority before they get tools.',
    kit: [
      'framework/llm-lifecycle/agent-identity-and-tool-governance.md',
      'framework/llm-lifecycle/multi-agent-governance.md',
      'framework/risk-classification/agentic-ai-risk.md',
    ],
    book: { ...AAFSE, note: 'Chapter 10 covers agent authority and audit trails in depth.' },
    related: ['001-the-control-plane', '004-the-decision-layer'],
  },
  {
    n: 19, slug: '19-federate-standards-and-delivery', part: 'VI',
    title: 'Federate: central standards, local delivery', short: 'Same stack, every business unit',
    checklist: { item: 'BUSINESS UNITS', response: 'SELF-SERVE' },
    doneWhen: 'Business units run governance without queuing on the centre.',
    restsOn: [6, 8], patterns: [],
    deepDive: ['hub and spoke', 'portfolio view', 'metrics', 'the board'],
    call: 'The centre sets standards and builds the road. Teams deliver.',
    kit: [
      'framework/operating-model/ai-coe-design.md',
      'framework/operating-model/governance-metrics.md',
      'framework/operating-model/board-reporting.md',
      'framework/operating-model/ai-literacy.md',
    ],
    related: [],
  },
  {
    n: 20, slug: '20-build-governance-into-the-platform', part: 'VI',
    title: 'Build governance into the platform', short: 'Platform',
    checklist: { item: 'CONTROLS', response: 'IN THE PLATFORM' },
    doneWhen: 'Most controls run automatically on the paved road.',
    restsOn: [6, 9, 10], patterns: ['chokepoint-placement', 'split-the-log', 'decision-record'],
    deepDive: ['gateway', 'registry', 'policy as code', 'shared evals', 'architecture direction'],
    call: 'Automate the controls that repeat. Keep committees for high-risk approvals and exceptions.',
    kit: [
      'reference-implementations/README.md',
      'controls/stage-07-deployment.yaml',
      'framework/operating-model/grc-integration.md',
    ],
    book: { title: 'Designing Agentic Systems', note: 'Covers the platform architecture behind a paved road for agents.' },
    related: ['008-production-execution', '001-the-control-plane'],
  },
  {
    n: 21, slug: '21-reuse-controls-and-evidence', part: 'VI',
    title: 'Reuse one set of controls and evidence across regulators', short: 'One evidence pack, reused across regulators',
    checklist: { item: 'REGULATORS', response: 'ONE EVIDENCE PACK' },
    doneWhen: 'One evidence pack supports every obligation that applies to you, with the gaps written down.',
    restsOn: [3, 10, 11], patterns: ['decision-record', 'split-the-log'],
    deepDive: ['EU AI Act', 'ISO/IEC 42001', 'NIST AI RMF', 'SR 26-2', 'change monitoring'],
    call: 'Keep one mapping from rules to controls and reuse it. Never build a programme per regulator.',
    kit: [
      'framework/compliance/eu-ai-act-mapping.md',
      'framework/compliance/iso-42001-mapping.md',
      'framework/compliance/nist-ai-rmf-mapping.md',
      'framework/compliance/multi-jurisdictional-guide.md',
      'framework/compliance/regulatory-change-monitoring.md',
    ],
    related: ['007-telemetry-audit-and-review'],
  },
  {
    n: 22, slug: '22-walk-one-system-through-it-all', part: 'Close',
    title: 'Walk one system through it all', short: 'Walk-through',
    checklist: { item: 'ONE SYSTEM', response: 'TRACED END TO END' },
    doneWhen: 'You can trace one high-risk system through every step and show the evidence at each.',
    restsOn: EVERY_STEP_BEFORE_22, patterns: [],
    deepDive: ["the framework's T1 governance case file, start to finish"],
    call: 'Governance is proven on one real system, not on a slide.',
    kit: ['examples/customer-service-chatbot/governance-case-file.md'], related: [],
  },
];

export const stepByN = (n: number): Step | undefined => STEPS.find((s) => s.n === n);
export const stepBySlug = (slug: string): Step | undefined => STEPS.find((s) => s.slug === slug);
export const stepsInPart = (part: Part): Step[] => STEPS.filter((s) => s.part === part);
export const stepHref = (s: Step): string => `/governance/${s.slug}/`;

/** Steps that rest on n. Step 22 rests on everything by definition, so it is left out. */
export const holdsUp = (n: number): number[] =>
  STEPS.filter((s) => s.n !== 22 && s.restsOn.includes(n)).map((s) => s.n);

/** Link for a step number, or null while its essay is unwritten. */
export const writtenHref = (written: ReadonlySet<string>) => (n: number): string | null => {
  const s = stepByN(n);
  return s && written.has(s.slug) ? stepHref(s) : null;
};

export function neighbours(n: number): { prev?: Step; next?: Step } {
  return { prev: stepByN(n - 1), next: stepByN(n + 1) };
}
