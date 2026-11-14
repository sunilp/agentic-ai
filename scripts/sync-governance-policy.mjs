#!/usr/bin/env node
// Snapshot the framework's tier policy and file list at a tag into
// src/data/governance-policy.json. Run by hand when the framework is re-tagged:
//   node scripts/sync-governance-policy.mjs [path-to-framework-repo] [tag]
// Never run it in CI: the build must not depend on a second repository.
import { execFileSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { parse } from 'yaml';

const repo = process.argv[2] ?? '../ai-governance-framework';
const tag = process.argv[3] ?? 'v2.4.0';
const gitBin = process.env.GIT_BIN ?? '/usr/bin/git';
const git = (...args) => execFileSync(gitBin, ['-C', repo, ...args], { encoding: 'utf8' });

const policy = parse(git('show', `${tag}:policy/tiers.yaml`));
const tiers = {};
for (const [id, t] of Object.entries(policy.tiers)) {
  tiers[id] = {
    name: t.name,
    approver: t.approvers.risk_assessment.text,
    validation: t.approvers.validation.text,
    reviewCadence: t.review_cadence.text,
    metricsReview: t.metrics_review,
    revalidation: t.independent_revalidation.text,
    redTeam: t.red_team.depth,
  };
}
const manifest = git('ls-tree', '-r', '--name-only', tag).split('\n').filter(Boolean).sort();
const out = { source: `ai-governance-framework@${tag}`, tiers, manifest };
writeFileSync('src/data/governance-policy.json', `${JSON.stringify(out, null, 2)}\n`);
console.log(`wrote ${Object.keys(tiers).length} tiers and ${manifest.length} paths from ${tag}`);
