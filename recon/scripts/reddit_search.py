#!/usr/bin/env python3
"""Fetch Reddit posts and comments for recon analysis.

Uses redditwarp (pip install redditwarp) for unauthenticated public access.
No API keys or credentials needed.

Usage:
    python3 reddit_search.py --subreddits python,programming --sort hot,rising,top --limit 20

Options:
    --subreddits SUB1,SUB2   Comma-separated subreddit names (required)
    --sort SORT1,SORT2       Sorting methods: hot, rising, top (default: hot,rising,top)
    --limit N                Posts per subreddit per sort (default: 20)
    --time-filter PERIOD     Time filter for top posts: hour,day,week,month,year,all (default: week)
    --deep-dive N            Fetch comments for top N posts by engagement (default: 0)
    --output FILE            Write JSON to file instead of stdout
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

def _check_redditwarp():
    """Check if redditwarp is installed, exit with instructions if not."""
    try:
        import redditwarp  # noqa: F401
        return True
    except ImportError:
        print(
            "Error: redditwarp not installed.\n"
            "\n"
            "Install it with:\n"
            "  pip install redditwarp\n"
            "\n"
            "No API keys or credentials needed — uses public unauthenticated access.",
            file=sys.stderr,
        )
        sys.exit(1)


def fetch_posts(subreddits, sorts, limit=20, time_filter="week", deep_dive=0):
    """Fetch posts from subreddits by sort method.

    Returns dict: {subreddit: {sort: [posts]}}
    """
    _check_redditwarp()
    from redditwarp.SYNC import Client

    client = Client()
    results = {}

    for sub in subreddits:
        results[sub] = {}
        for sort in sorts:
            posts = []
            try:
                print(f"Fetching r/{sub} {sort}...", file=sys.stderr)
                if sort == "hot":
                    submissions = client.p.subreddit.pull.hot(sub, amount=limit)
                elif sort == "rising":
                    submissions = client.p.subreddit.pull.rising(sub, amount=limit)
                elif sort == "top":
                    submissions = client.p.subreddit.pull.top(sub, amount=limit, time=time_filter)
                elif sort == "new":
                    submissions = client.p.subreddit.pull.new(sub, amount=limit)
                else:
                    print(f"  Skipping unknown sort: {sort}", file=sys.stderr)
                    continue

                for submission in submissions:
                    post = {
                        "title": submission.title,
                        "score": submission.score,
                        "comment_count": submission.comment_count,
                        "url": f"https://www.reddit.com/r/{sub}/comments/{submission.id36}",
                        "author": str(submission.author_display_name) if submission.author_display_name else "[deleted]",
                        "created_utc": submission.created_ut,
                    }
                    # Add body preview for text posts
                    if hasattr(submission, "body") and submission.body:
                        body = submission.body
                        post["body_preview"] = body[:500] + ("..." if len(body) > 500 else "")
                    elif hasattr(submission, "self_text") and submission.self_text:
                        body = submission.self_text
                        post["body_preview"] = body[:500] + ("..." if len(body) > 500 else "")
                    posts.append(post)

                print(f"  Found {len(posts)} posts", file=sys.stderr)

            except Exception as e:
                print(f"  Error fetching r/{sub} {sort}: {e}", file=sys.stderr)

            results[sub][sort] = posts

    # Deep dive: fetch comments for top posts by engagement
    if deep_dive > 0:
        all_posts = []
        for sub in results:
            for sort in results[sub]:
                for post in results[sub][sort]:
                    post["_sub"] = sub
                    all_posts.append(post)

        # Deduplicate by URL, sort by engagement (score + comments)
        seen = set()
        unique_posts = []
        for p in all_posts:
            if p["url"] not in seen:
                seen.add(p["url"])
                unique_posts.append(p)
        unique_posts.sort(key=lambda p: p["score"] + p["comment_count"], reverse=True)

        top_posts = unique_posts[:deep_dive]
        results["_deep_dive"] = []

        for post in top_posts:
            try:
                # Extract submission ID from URL
                parts = post["url"].split("/comments/")
                if len(parts) < 2:
                    continue
                sub_id_str = parts[1].split("/")[0]
                sub_id = int(sub_id_str, 36)

                print(f"Deep diving: {post['title'][:60]}...", file=sys.stderr)
                tree = client.p.comment_tree.fetch(sub_id, sort="top", limit=20)

                comments = []
                for node in tree.children:
                    comment = node.value
                    if hasattr(comment, "body") and comment.body:
                        comments.append({
                            "body": comment.body[:1000],
                            "score": getattr(comment, "score", 0),
                            "author": str(comment.author_display_name) if hasattr(comment, "author_display_name") and comment.author_display_name else "[deleted]",
                        })

                results["_deep_dive"].append({
                    "title": post["title"],
                    "url": post["url"],
                    "subreddit": post.get("_sub", "unknown"),
                    "score": post["score"],
                    "comment_count": post["comment_count"],
                    "top_comments": comments[:15],
                })
            except Exception as e:
                print(f"  Error deep diving: {e}", file=sys.stderr)

        # Clean up internal keys
        for sub in results:
            if sub == "_deep_dive":
                continue
            for sort in results[sub]:
                for post in results[sub][sort]:
                    post.pop("_sub", None)

    results["_metadata"] = {
        "subreddits": subreddits,
        "sorts": sorts,
        "limit": limit,
        "time_filter": time_filter,
        "deep_dive": deep_dive,
        "timestamp": datetime.now().isoformat(),
    }

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch Reddit posts for recon")
    parser.add_argument("--subreddits", required=True, help="Comma-separated subreddit names")
    parser.add_argument("--sort", default="hot,rising,top", help="Sorting methods (default: hot,rising,top)")
    parser.add_argument("--limit", type=int, default=20, help="Posts per sort per subreddit (default: 20)")
    parser.add_argument("--time-filter", default="week", help="Time filter for top (default: week)")
    parser.add_argument("--deep-dive", type=int, default=0, help="Deep dive top N posts with comments")
    parser.add_argument("--output", default=None, help="Output file path (default: stdout)")
    args = parser.parse_args()

    subreddits = [s.strip() for s in args.subreddits.split(",")]
    sorts = [s.strip() for s in args.sort.split(",")]

    results = fetch_posts(subreddits, sorts, limit=args.limit, time_filter=args.time_filter, deep_dive=args.deep_dive)

    output = json.dumps(results, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output)
        print(f"Report saved: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
