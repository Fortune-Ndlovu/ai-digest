# AI Digest

Automated daily AI news digest sourced from Hacker News. Updated every morning at 8:00 AM UTC via GitHub Actions.

## Structure

```
digests/
├── models-and-research/      # Papers, models, benchmarks
├── industry-and-business/    # Funding, launches, acquisitions
├── policy-and-safety/        # Regulation, ethics, alignment
└── tools-and-open-source/    # Frameworks, libraries, devtools
```

Each file is named by date (`YYYY-MM-DD.md`) and includes YAML frontmatter for easy parsing.

## Browse

See [index.md](index.md) for the full table of contents.

## Manual Run

```bash
python scripts/fetch_news.py
```

Or trigger the workflow manually from the Actions tab on GitHub.
