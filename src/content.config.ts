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
    reproduceRepo: z.string().url(),
    dataUrl: z.string().url(),
    seed: z.number().optional(),
    references: z.array(z.string()).optional(),
  }),
});

const patterns = defineCollection({
  loader: glob({ pattern: '**/*.mdx', base: './src/content/patterns' }),
  schema: z.object({
    slug: z.string(),
    name: z.string(),
    oneLine: z.string(),
    whenToUse: z.string(),
    whenNotToUse: z.string(),
    antiPattern: z.string().optional(),
    diagram: z.string().optional(),
  }),
});

export const collections = { chapters, fieldNotes, recipes, projects, evidence, labs, patterns };
