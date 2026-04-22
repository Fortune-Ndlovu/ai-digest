#!/usr/bin/env python3
"""Fetch daily AI news from HN Algolia API and write categorized markdown digests."""

import json
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime, timezone

CATEGORIES = {
    "models-and-research": {
        "title": "Models & Research",
        "keywords": [
            "gpt", "llm", "model", "paper", "benchmark", "training",
            "fine-tune", "finetune", "transformer", "diffusion", "neural",
            "parameter", "weights", "pretraining", "foundational",
            "multimodal", "vision", "language model", "claude", "gemini",
            "llama", "mistral", "phi", "deepseek", "research", "arxiv",
            "dataset", "token", "inference", "reasoning", "chain-of-thought",
            "rl", "reinforcement", "alignment technique", "rlhf", "dpo",
        ],
    },
    "industry-and-business": {
        "title": "Industry & Business",
        "keywords": [
            "funding", "acquisition", "startup", "valuation", "ipo",
            "revenue", "launch", "announces", "partnership", "series a",
            "series b", "series c", "raised", "billion", "million",
            "microsoft", "google", "meta", "amazon", "apple", "nvidia",
            "openai", "anthropic", "company", "enterprise", "business",
            "market", "stock", "investor", "venture", "hire", "layoff",
            "ceo", "product", "platform", "saas",
        ],
    },
    "policy-and-safety": {
        "title": "Policy & Safety",
        "keywords": [
            "regulation", "law", "policy", "safety", "ethics", "bias",
            "alignment", "risk", "govern", "legislation", "ban",
            "restrict", "compliance", "audit", "eu ai act", "executive order",
            "congress", "senate", "copyright", "deepfake", "misuse",
            "surveillance", "privacy", "responsible", "guardrail",
            "existential", "x-risk", "doom", "pause", "moratorium",
        ],
    },
    "tools-and-open-source": {
        "title": "Tools & Open Source",
        "keywords": [
            "github", "open source", "opensource", "framework", "library",
            "tool", "api", "sdk", "plugin", "extension", "release",
            "v2", "v3", "v4", "update", "cli", "langchain", "llamaindex",
            "huggingface", "hugging face", "vllm", "ollama", "pytorch",
            "tensorflow", "jax", "ggml", "gguf", "mlx", "developer",
            "devtool", "self-host", "local", "agent", "rag",
        ],
    },
}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIGESTS_DIR = os.path.join(REPO_ROOT, "digests")
INDEX_PATH = os.path.join(REPO_ROOT, "index.md")


def fetch_stories_for_window(queries, seconds_ago, min_points):
    """Fetch AI stories from HN Algolia posted within the given time window."""
    now = int(datetime.now(timezone.utc).timestamp())
    cutoff = now - seconds_ago
    seen_ids = set()
    stories = []

    for query in queries:
        url = (
            "https://hn.algolia.com/api/v1/search_by_date?"
            + urllib.parse.urlencode({
                "query": query,
                "tags": "story",
                "numericFilters": f"created_at_i>{cutoff},points>{min_points}",
                "hitsPerPage": 50,
            })
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ai-digest-bot/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"Warning: failed to fetch query '{query}': {e}")
            continue

        for hit in data.get("hits", []):
            story_id = hit.get("objectID")
            if story_id in seen_ids:
                continue
            seen_ids.add(story_id)
            stories.append({
                "title": hit.get("title", "Untitled"),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                "points": hit.get("points", 0),
                "comments": hit.get("num_comments", 0),
                "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
            })

    stories.sort(key=lambda s: s["points"], reverse=True)
    return stories


def fetch_stories():
    """Fetch AI stories, trying last 24h first, then widening if needed."""
    queries = ["artificial intelligence", "AI", "LLM", "machine learning"]

    # Try last 24 hours with low point threshold
    stories = fetch_stories_for_window(queries, seconds_ago=86400, min_points=5)
    if stories:
        print(f"Found {len(stories)} stories from the last 24 hours")
        return stories

    # Fallback: last 7 days
    print("No stories in last 24h, falling back to last 7 days...")
    stories = fetch_stories_for_window(queries, seconds_ago=604800, min_points=10)
    if stories:
        print(f"Found {len(stories)} stories from the last 7 days")
        return stories

    # Final fallback: top stories all-time (guarantees a commit)
    print("No stories in last 7 days either, falling back to top stories...")
    stories = fetch_stories_for_window(queries, seconds_ago=31536000, min_points=50)
    print(f"Fallback found {len(stories)} stories")
    return stories


def categorize(story):
    """Return the best matching category for a story based on keyword hits."""
    title_lower = story["title"].lower()
    scores = {}
    for cat, info in CATEGORIES.items():
        score = sum(1 for kw in info["keywords"] if kw in title_lower)
        if score > 0:
            scores[cat] = score

    if not scores:
        return "industry-and-business"

    return max(scores, key=scores.get)


def write_digest(date_str, categorized):
    """Write one markdown file per category that has stories."""
    written_files = []
    for cat, stories in categorized.items():
        if not stories:
            continue

        cat_dir = os.path.join(DIGESTS_DIR, cat)
        os.makedirs(cat_dir, exist_ok=True)
        filepath = os.path.join(cat_dir, f"{date_str}.md")

        title = CATEGORIES[cat]["title"]
        date_display = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")

        lines = [
            "---",
            f"date: {date_str}",
            f"category: {cat}",
            "---",
            "",
            f"# {title} - {date_display}",
            "",
        ]

        for story in stories[:15]:
            lines.append(f"## {story['title']}")
            lines.append(f"- **Source:** {story['url']}")
            lines.append(f"- **HN Discussion:** {story['hn_url']}")
            lines.append(f"- **Points:** {story['points']} | **Comments:** {story['comments']}")
            lines.append("")

        with open(filepath, "w") as f:
            f.write("\n".join(lines))

        written_files.append((cat, filepath, stories))
        print(f"Wrote {filepath} ({len(stories)} stories)")

    return written_files


def update_index(date_str, written_files):
    """Rebuild index.md from all existing digest files."""
    all_entries = {}
    for cat in CATEGORIES:
        all_entries[cat] = []
        cat_dir = os.path.join(DIGESTS_DIR, cat)
        if not os.path.isdir(cat_dir):
            continue
        for fname in sorted(os.listdir(cat_dir), reverse=True):
            if not fname.endswith(".md"):
                continue
            fdate = fname.replace(".md", "")
            filepath = os.path.join(cat_dir, fname)

            first_stories = []
            with open(filepath) as f:
                for line in f:
                    if line.startswith("## "):
                        first_stories.append(line.strip("# \n"))
                        if len(first_stories) >= 3:
                            break

            preview = ", ".join(first_stories) if first_stories else "digest"
            rel_path = f"digests/{cat}/{fname}"
            all_entries[cat].append(f"- [{fdate}]({rel_path}) - {preview}")

    lines = [
        "# AI Digest Index",
        "",
        "Daily AI news digest, auto-updated from Hacker News.",
        "",
    ]

    for cat, info in CATEGORIES.items():
        entries = all_entries.get(cat, [])
        lines.append(f"## {info['title']}")
        lines.append("")
        if entries:
            lines.extend(entries)
        else:
            lines.append("*No entries yet.*")
        lines.append("")

    with open(INDEX_PATH, "w") as f:
        f.write("\n".join(lines))

    print(f"Updated {INDEX_PATH}")


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Fetching AI news for {today}...")

    stories = fetch_stories()
    print(f"Found {len(stories)} stories")

    if not stories:
        print("No stories found. Writing empty marker to ensure commit.")
        cat_dir = os.path.join(DIGESTS_DIR, "industry-and-business")
        os.makedirs(cat_dir, exist_ok=True)
        filepath = os.path.join(cat_dir, f"{today}.md")
        with open(filepath, "w") as f:
            f.write(f"---\ndate: {today}\ncategory: industry-and-business\n---\n\n# Industry & Business - {today}\n\nNo AI stories found today.\n")
        update_index(today, [])
        return

    categorized = {cat: [] for cat in CATEGORIES}
    for story in stories:
        cat = categorize(story)
        categorized[cat].append(story)

    written = write_digest(today, categorized)
    update_index(today, written)
    print("Done!")


if __name__ == "__main__":
    main()
