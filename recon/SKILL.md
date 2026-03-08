---
name: recon
description: Multi-source reconnaissance combining X/Twitter trends, Reddit community analysis, and web search into a synthesized intelligence brief. Use when asked to research trends, analyze communities, scan discussions, gather intelligence, or run recon on any topic.
argument-hint: [topic] [--sources x,reddit,web] [--days 7]
allowed-tools: Bash(python3 ~/.claude/skills/recon/scripts/*.py *), Bash(pip install *), Bash(pip3 install *)
---

# Multi-Source Recon

Run domain-specific reconnaissance across X/Twitter, Reddit, and web search, then synthesize findings into an actionable intelligence brief.

## Quick Start

Config-driven (recommended):
1. Create `recon-config.json` in your project root (see [config guide](references/config-guide.md) for schema and examples)
2. Run `/recon`

Ad-hoc (no config needed):
- `/recon AI coding assistants` — auto-generates queries from the topic
- `/recon --sources reddit,web` — specific sources only

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `$ARGUMENTS` (positional) | Ad-hoc topic to research | Uses config queries |
| `--sources x,reddit,web` | Which sources to run | All enabled in config |
| `--days N` | Override lookback period | Config value or 7 |

## Scripts

### X Search (`scripts/x_search.py`)

```bash
python3 ~/.claude/skills/recon/scripts/x_search.py --query "QUERY" [--handles h1,h2] [--days 7] [--output FILE]
```

Requires: `pip install xai-sdk` + `XAI_API_KEY` env var. Results cached 24h in `$TMPDIR/recon-cache/`.

**Sandbox note:** X API calls may need `dangerouslyDisableSandbox: true` on the Bash command due to DNS resolution in sandboxed environments.

### Reddit Search (`scripts/reddit_search.py`)

```bash
python3 ~/.claude/skills/recon/scripts/reddit_search.py --subreddits SUB1,SUB2 --sort hot,rising,top --limit 20 [--deep-dive 5] [--output FILE]
```

Requires: `pip install redditwarp`. No API keys needed (unauthenticated public access). Outputs structured JSON.

## Workflow

### 1. Load Configuration

Read `recon-config.json` from project root. If it doesn't exist:
- If `$ARGUMENTS` has a topic: auto-generate queries for that topic (skip config)
- If no topic: offer to create a config interactively using [config-guide.md](references/config-guide.md)

### 2. Determine Sources

Check which sources to run:
1. Start with config `sources.*.enabled` flags
2. Override with `--sources` flag if provided
3. Check availability:
   - **X**: Try `import xai_sdk`. If missing, print "Skipping X (run: pip install xai-sdk)" and skip.
   - **Reddit**: Try `import redditwarp`. If missing, print "Skipping Reddit (run: pip install redditwarp)" and skip.
   - **Web**: Always available (uses WebSearch tool).

If no sources are available, tell the user what to install and exit.

### 3. Create Output Directory

```python
from datetime import datetime
import os
output_dir = f"recon/{datetime.now().strftime('%Y-%m-%d')}"
os.makedirs(output_dir, exist_ok=True)
```

### 4. Run Sources in Parallel

Launch enabled sources using the Agent tool. Run all available sources in parallel (single message, multiple Agent calls).

**For X source** — launch Agent:
```
subagent_type: general-purpose
prompt: |
  Run X/Twitter trend analysis.

  Script: python3 ~/.claude/skills/recon/scripts/x_search.py

  Config queries: {config.sources.x.queries}
  Handles: {config.sources.x.handles}
  Days: {config.sources.x.days}

  For each query in config, run the script and collect output.
  If there are multiple queries, run them sequentially and combine results.

  Write a structured report to: {output_dir}/x_trends_report.md

  Report format:
  # X/Twitter Trends Report
  **Date:** {date}

  ## Top Trending Topics
  ## Key Posts
  ## Emerging Questions
  ## Notable Debates
  ## Key Insights

  IMPORTANT: The Bash command running x_search.py may need dangerouslyDisableSandbox: true
  if you get DNS or network errors in the sandbox.
```

**For Reddit source** — launch Agent:
```
subagent_type: general-purpose
prompt: |
  Run Reddit community analysis.

  Script: python3 ~/.claude/skills/recon/scripts/reddit_search.py

  Subreddits: {config.sources.reddit.subreddits}
  Sort: {config.sources.reddit.sort}
  Limit: {config.sources.reddit.limit}
  Deep dive: {config.sources.reddit.deep_dive}

  Run the script and parse the JSON output. Then write an analysis report.

  Save to: {output_dir}/reddit_report.md

  Report format:
  # Reddit Community Report
  **Date:** {date}

  ## Hot Topics by Subreddit
  (For each subreddit: top posts with title, score, comments, brief analysis)

  ## Rising Discussions
  (Early signals gaining traction)

  ## Top Weekly Posts
  (What resonated most)

  ## Recurring Questions
  (Questions appearing across communities)

  ## Active Debates
  (Disagreements driving engagement)

  ## Deep Dive Highlights
  (Key insights from comment threads)

  ## Key Insights
  (Cross-subreddit patterns, engagement signals)
```

**For Web source** — launch Agent:
```
subagent_type: general-purpose
prompt: |
  Run web research analysis. Read the instructions at:
  ~/.claude/skills/recon/references/web-agent.md

  Config: {paste relevant config.sources.web section}
  Domain: {config.domain}
  Description: {config.description}

  Save report to: {output_dir}/web_report.md
```

### 5. Run Synthesis

After all source agents complete, launch the synthesis agent:

```
subagent_type: general-purpose
prompt: |
  Synthesize recon findings. Read the instructions at:
  ~/.claude/skills/recon/references/synthesis-agent.md

  Read all reports in: {output_dir}/
  Config domain: {config.domain}
  Config description: {config.description}
  Synthesis focus: {config.synthesis.focus}

  Save synthesis to: {output_dir}/synthesis.md
```

### 6. Display Summary

After synthesis completes, read `{output_dir}/synthesis.md` and display the executive summary to the user:

```
Recon Complete — {config.domain} — {date}

Sources: {list of sources that ran}
Output: {output_dir}/

{Paste executive summary from synthesis.md}

Key recommendations:
1. {First recommendation}
2. {Second recommendation}
3. {Third recommendation}

Full reports:
- {output_dir}/synthesis.md (cross-source analysis)
- {output_dir}/x_trends_report.md
- {output_dir}/reddit_report.md
- {output_dir}/web_report.md
```

## Ad-Hoc Topic Mode

When `$ARGUMENTS` contains a topic (not a flag):

1. Use the topic as the domain context
2. Auto-generate appropriate queries:
   - X: "What are people discussing about {topic}? Trends, debates, questions."
   - Reddit: Infer 2-3 relevant subreddits from the topic
   - Web: Generate 3-4 search queries like "{topic} trends {year}", "{topic} community discussion", "{topic} latest developments"
3. Set synthesis focus to "trend_monitoring"
4. Run the standard workflow

## Environment Setup

### Required for X source
```bash
pip install xai-sdk
export XAI_API_KEY="your-key-here"  # Get at https://console.x.ai
```

### Required for Reddit source
```bash
pip install redditwarp
# No API keys needed — uses public unauthenticated access
```

### Web source
No setup needed — uses Claude's built-in WebSearch tool.

### Install everything at once
```bash
pip install xai-sdk redditwarp
```
