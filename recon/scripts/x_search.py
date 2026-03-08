#!/usr/bin/env python3
"""Search X/Twitter trends using X.ai Grok API with x_search.

Uses xai-sdk (pip install xai-sdk) for clean API access.
Requires XAI_API_KEY set in environment or .env file.

Usage:
    python3 x_search.py --query "AI coding assistants" [OPTIONS]

Options:
    --query TEXT         Search query (required)
    --handles h1,h2     Comma-separated X handles to filter
    --days N             Look back N days (default: 7)
    --max-sources N      Max sources to analyze (default: 30)
    --output FILE        Write report to file instead of stdout
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# --- .env loading (stdlib only) ---

def _load_env():
    """Load KEY=VALUE pairs from .env files into os.environ."""
    for env_path in [Path.cwd() / ".env", Path.home() / ".env"]:
        if not env_path.is_file():
            continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
        break


# --- Cache ---

def _cache_dir():
    """Get cache directory in $TMPDIR/recon-cache/."""
    base = os.environ.get("TMPDIR", tempfile.gettempdir())
    d = Path(base) / "recon-cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_key(query, handles, days):
    """Generate MD5 cache key from query parameters."""
    parts = [query, ",".join(sorted(handles or [])), str(days), datetime.now().strftime("%Y-%m-%d")]
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def _get_cached(key):
    """Return cached result if fresh (24hr TTL)."""
    cache_file = _cache_dir() / f"{key}.json"
    if not cache_file.exists():
        return None
    age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
    if age > timedelta(hours=24):
        return None
    try:
        return json.loads(cache_file.read_text())
    except Exception:
        return None


def _set_cached(key, data):
    """Save result to cache."""
    cache_file = _cache_dir() / f"{key}.json"
    try:
        cache_file.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


# --- Search ---

def search_x(query, handles=None, days=7, max_sources=30):
    """Search X using xai-sdk with Grok + x_search tool.

    Returns dict with 'analysis' (raw Grok text) and metadata.
    """
    try:
        from xai_sdk import Client
        from xai_sdk.chat import user
        from xai_sdk.tools import x_search
    except ImportError:
        print(
            "Error: xai-sdk not installed.\n"
            "\n"
            "Install it with:\n"
            "  pip install xai-sdk\n"
            "\n"
            "Then set XAI_API_KEY in your environment or .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    _load_env()
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        print(
            "Error: XAI_API_KEY not found.\n"
            "\n"
            "Set it in your project .env file:\n"
            '  XAI_API_KEY=your-api-key-here\n'
            "\n"
            "Or export in your shell:\n"
            '  export XAI_API_KEY="your-api-key-here"\n'
            "\n"
            "Get a key at: https://console.x.ai",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check cache
    key = _cache_key(query, handles, days)
    cached = _get_cached(key)
    if cached:
        print("Using cached results (less than 24h old)", file=sys.stderr)
        return cached

    # Configure x_search tool parameters
    from_date = datetime.now() - timedelta(days=days)
    tool_params = {"from_date": from_date}
    if handles:
        tool_params["allowed_x_handles"] = handles[:10]

    # Create chat with x_search
    client = Client(api_key=api_key)
    chat = client.chat.create(
        model="grok-4-fast",
        tools=[x_search(**tool_params)],
    )

    prompt = f"""{query}

Please analyze recent X posts and provide:

1. **Top Trending Topics** (5-7 topics): What are people most discussing?
2. **Key Posts**: 3-5 influential or viral posts with context
3. **Emerging Questions**: What questions are people asking?
4. **Content Gaps**: Popular topics not deeply explored yet
5. **Notable Debates**: Active disagreements or differing viewpoints

Focus on substantive discussions with depth, not just reactions."""

    chat.append(user(prompt))

    print(f"Searching X for: {query[:80]}... (last {days} days)", file=sys.stderr)

    try:
        response = chat.sample()
    except Exception as e:
        print(f"Error calling X.ai API: {e}", file=sys.stderr)
        print("This may be a network/DNS issue. Try running outside the sandbox.", file=sys.stderr)
        sys.exit(1)

    result = {
        "analysis": response.content,
        "query": query,
        "handles": handles,
        "days": days,
        "timestamp": datetime.now().isoformat(),
    }

    _set_cached(key, result)
    return result


def main():
    parser = argparse.ArgumentParser(description="Search X/Twitter trends via Grok")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--handles", default=None, help="Comma-separated X handles to filter")
    parser.add_argument("--days", type=int, default=7, help="Look back N days (default: 7)")
    parser.add_argument("--max-sources", type=int, default=30, help="Max sources (default: 30)")
    parser.add_argument("--output", default=None, help="Output file path (default: stdout)")
    args = parser.parse_args()

    handles = [h.strip().lstrip("@") for h in args.handles.split(",")] if args.handles else None

    result = search_x(args.query, handles=handles, days=args.days, max_sources=args.max_sources)

    output = result.get("analysis", "")
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output)
        print(f"Report saved: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
