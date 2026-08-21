import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const chapters = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/chapters' }),
  schema: z.object({
    title: z.string(),
    part: z.enum(['foundations', 'I-build', 'II-judge', 'III-operate', 'IV-advanced']),
    description: z.string(),
    readingTime: z.number(),
    references: z.array(z.string()).optional(),
    cites: z.array(z.string()).optional(),
    patterns: z.array(z.string()).optional(),
    date: z.coerce.date(),
    status: z.enum(['draft', 'published']).default('published'),
  }),
});

const fieldNotes = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/fieldNotes' }),
  schema: z.object({
    id: z.string(),
    title: z.string(),
    dek: z.string(),
    description: z.string(),
    primaryChapter: z.string(),
    banner: z.string(),
    date: z.coerce.date(),
    readingTime: z.number(),
    pullQuote: z.string().optional(),
    references: z.array(z.string()).optional(),
    cites: z.array(z.string()).optional(),
    patterns: z.array(z.string()).optional(),
    spot: z.string().optional(),
    spotCaption: z.string().optional(),
    sources: z.array(z.object({
      title: z.string(),
      url: z.string().url(),
      authors: z.array(z.string()).optional(),
      year: z.number().optional(),
    })),
  }),
});

const recipes = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/recipes' }),
  schema: z.object({
    id: z.string(),
    title: z.string(),
    description: z.string(),
    chapter: z.string(),
    prerequisites: z.array(z.string()),
    estimatedMinutes: z.number(),
    verifiedOn: z.coerce.date(),
    verifiedVersions: z.record(z.string()),
    runItRepo: z.string().url(),
    gotchas: z.array(z.string()),
    references: z.array(z.string()).optional(),
    patterns: z.array(z.string()).optional(),
    spot: z.string().optional(),
    spotCaption: z.string().optional(),
  }),
});

const signal = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/signal' }),
  schema: z.object({
    id: z.string(),
    title: z.string(),
    dek: z.string(),
    description: z.string(),
    primaryChapter: z.string().optional(),
    banner: z.string(),
    date: z.coerce.date(),
    readingTime: z.number(),
    pullQuote: z.string().optional(),
    references: z.array(z.string()).optional(),
    cites: z.array(z.string()).optional(),
    patterns: z.array(z.string()).optional(),
    sources: z.array(z.object({
      title: z.string(),
      url: z.string().url(),
      authors: z.array(z.string()).optional(),
      year: z.number().optional(),
    })),
  }),
});

const projects = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/projects' }),
  schema: z.object({
    slug: z.string(),
    title: z.string(),
    tagline: z.string(),
    description: z.string(),
    architecture: z.string(),
    evalStats: z.object({
      accuracy: z.string(),
      avgCost: z.string(),
      latencyP50: z.string(),
    }),
    repoUrl: z.string().url(),
    liveDemoUrl: z.string().url().optional(),
    tryAgentTraceFile: z.string().optional(),
    caseStudyAnchor: z.string().optional(),    // e.g. '#case-study' if MDX has that heading
    failuresAnchor: z.string().optional(),     // e.g. '#failures' if MDX has that heading
    chapters: z.array(z.string()),
    references: z.array(z.string()).optional(),
  }),
});

const evidence = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/evidence' }),
  schema: z.object({
    id: z.string(),
    title: z.string(),
    description: z.string(),
    heroStats: z.array(z.object({
      value: z.string(),
      label: z.string(),
      color: z.enum(['default', 'accent']).default('default'),
    })),
    chartData: z.string().optional(),
    methodology: z.string(),
    measuredOn: z.coerce.date(),
    model: z.string().optional(),
    downloads: z.array(z.object({
      label: z.string(),
      href: z.string(),
    })),
  }),
});

const labs = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/labs' }),
  schema: z.object({
    id: z.string(),
    title: z.string(),
    description: z.string(),
    hypothesis: z.string(),
    result: z.string(),
    resultLabel: z.string(),
    date: z.coerce.date(),
    readingTime: z.number(),
    reproduceRepo: z.string().url().optional(),
    dataUrl: z.string().url().optional(),
    seed: z.number().optional(),
    references: z.array(z.string()).optional(),
    spot: z.string().optional(),
    spotCaption: z.string().optional(),
  }),
});

const patterns = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/patterns' }),
  schema: z.object({
    // The filename is the slug and joins to src/data/pattern-language.ts,
    // which owns name, kind, layer, stage, status and attribution.
    description: z.string(),
    updated: z.coerce.date(),
    readingTime: z.number(),
    forces: z.array(z.string()).min(2),
    sources: z.array(z.object({
      title: z.string(),
      url: z.string().url(),
      authors: z.array(z.string()).optional(),
      year: z.number().optional(),
    })).min(1),
    related: z.array(z.string()).optional(),
    blueprints: z.array(z.string()).optional(),
    anchors: z.array(z.object({ label: z.string(), anchor: z.string() })).min(5),
    diagram: z.string().optional(),
    spot: z.string().optional(),
    spotCaption: z.string().optional(),
  }),
});

const architecture = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/architecture' }),
  schema: z.object({
    id: z.string(),                 // arch-001
    title: z.string(),
    dek: z.string(),
    description: z.string(),
    // The three-layer spine of the section.
    layer: z.enum(['capability', 'control', 'evidence']),
    order: z.number(),              // sequence position; the section reads in order, not by date
    readingTime: z.number(),
    updated: z.coerce.date(),       // blueprints are revised, not published once
    specifies: z.string(),          // one line: what this blueprint pins down
    appliesTo: z.array(z.string()), // RAG platform, coding assistant, agent system, ...
    decisions: z.array(z.string()).optional(),          // decisions this blueprint forces
    anchors: z.array(z.object({                          // in-page nav
      label: z.string(),
      anchor: z.string(),
    })).optional(),
    spot: z.string().optional(),
    spotCaption: z.string().optional(),
    references: z.array(z.string()).optional(),
    cites: z.array(z.string()).optional(),
    patterns: z.array(z.string()).optional(),
    sources: z.array(z.object({
      title: z.string(),
      url: z.string().url(),
      authors: z.array(z.string()).optional(),
      year: z.number().optional(),
    })).optional(),
    status: z.enum(['draft', 'published']).default('published'),
  }),
});

export const collections = { chapters, fieldNotes, recipes, signal, projects, evidence, labs, patterns, architecture };
