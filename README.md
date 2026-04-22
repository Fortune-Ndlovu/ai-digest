# AI Digest

Automated daily AI news digest sourced from Hacker News. A GitHub Actions workflow runs every morning, fetches the latest AI stories, categorizes them, and commits structured markdown files — building a searchable archive of how the AI landscape evolves over time.

## How It Works

### Data Source

All stories come from the [HN Algolia API](https://hn.algolia.com/api), a free, public, no-auth-required search API over Hacker News. We query using four search terms:

- `"artificial intelligence"`
- `"AI"`
- `"LLM"`
- `"machine learning"`

### Fetch Algorithm

The script uses a tiered fallback strategy to guarantee a commit every day:

1. **Last 24 hours** (min 5 points) — the primary window, captures fresh stories
2. **Last 7 days** (min 10 points) — kicks in if the 24h window returns nothing (e.g. holidays, API downtime)
3. **Last year** (min 50 points) — final fallback, ensures there's always content to commit

Results are deduplicated across queries within the same run (by HN story ID).

### Deduplication

A persistent `data/seen_ids.json` file tracks every HN story ID that has been written to a digest. On each run:

1. Load previously seen IDs
2. Fetch stories from the API
3. Filter out any story whose ID is already in the seen set
4. Write only new stories to digest files
5. Save updated seen IDs

This prevents the same story from appearing in multiple daily digests, even if it stays trending for several days.

### Categorization

Each story is categorized by keyword matching against its title. The category with the most keyword hits wins. If no keywords match, the story defaults to `industry-and-business`.

| Category | What It Captures | Example Keywords |
|----------|-----------------|------------------|
| `models-and-research` | Papers, new models, benchmarks, training techniques | gpt, llm, transformer, arxiv, benchmark, reasoning |
| `industry-and-business` | Company news, funding, product launches, acquisitions | startup, funding, launch, microsoft, openai, nvidia |
| `policy-and-safety` | Regulation, ethics, alignment, AI governance | regulation, safety, bias, copyright, deepfake, privacy |
| `tools-and-open-source` | Frameworks, libraries, developer tools, open-source releases | github, open source, framework, huggingface, ollama, rag |

### Output

Each run produces:

- **One markdown file per category** with stories for that day (`digests/{category}/YYYY-MM-DD.md`)
- **YAML frontmatter** on each file (`date`, `category`) for machine parsing
- **Up to 15 stories per category**, sorted by points (highest first)
- **An updated `index.md`** at the repo root — a full table of contents with 3-story previews per entry

### Schedule

A GitHub Actions cron job triggers daily at **08:00 UTC**. Can also be triggered manually from the Actions tab.

## Repository Structure

```
ai-digest/
├── README.md                         # this file
├── index.md                          # auto-updated table of contents
├── scripts/
│   └── fetch_news.py                 # fetch, categorize, write, index
├── data/
│   └── seen_ids.json                 # deduplication state
├── .github/
│   └── workflows/
│       └── daily-digest.yml          # daily cron workflow
└── digests/
    ├── models-and-research/          # papers, models, benchmarks
    │   └── YYYY-MM-DD.md
    ├── industry-and-business/        # funding, launches, acquisitions
    │   └── YYYY-MM-DD.md
    ├── policy-and-safety/            # regulation, ethics, alignment
    │   └── YYYY-MM-DD.md
    └── tools-and-open-source/        # frameworks, libraries, devtools
        └── YYYY-MM-DD.md
```

## Manual Run

```bash
python scripts/fetch_news.py
```

Or trigger the workflow manually from the **Actions** tab on GitHub.

## Future Improvements

- **AI-generated summaries** — use an LLM to write a brief summary for each story instead of just listing titles and links
- **Multiple data sources** — pull from Reddit (r/MachineLearning), ArXiv, TechCrunch, The Verge, etc. to reduce HN bias
- **Smarter categorization** — replace keyword matching with an LLM classifier for more accurate sorting
- **Weekly/monthly rollups** — auto-generate weekly and monthly summary digests that highlight the biggest stories
- **Trend detection** — track recurring topics over time and flag emerging trends (e.g. "mentions of 'AI agents' up 300% this month")
- **RSS feed** — generate an RSS/Atom feed from the digests so readers can subscribe
- **Search** — add a static site (GitHub Pages) with full-text search across all digests
- **Sentiment tracking** — classify stories as positive/negative/neutral to track industry sentiment over time
- **Pruning seen_ids.json** — periodically remove IDs older than 30 days to keep the file small
