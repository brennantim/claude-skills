#!/usr/bin/env python3
"""Send email using AgentMail API.

Uses only Python stdlib (urllib, json, base64). No pip install needed.
Requires AGENTMAIL_API_KEY set in environment or in a .env file.

Usage:
    python3 send_email.py "to@example.com" "Subject" "Body" [OPTIONS]

With options:
    python3 send_email.py "to@example.com" "Report" "See attached" --cc boss@co.com --attach report.pdf

HTML email:
    python3 send_email.py "to@example.com" "Newsletter" "<h1>Hello</h1>" --html
"""

import argparse
import base64
import json
import mimetypes
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

# --- Constants ---

API_BASE = "https://api.agentmail.to/v0"
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB
ENV_FILE_SEARCH_PATHS = [
    Path.cwd() / ".env",
    Path.home() / ".env",
]


def _load_env():
    """Load KEY=VALUE pairs from a .env file into os.environ.

    Searches cwd/.env then ~/.env. Only sets vars that aren't already set.
    Ignores comments and blank lines. Strips optional quotes around values.
    """
    for env_path in ENV_FILE_SEARCH_PATHS:
        if not env_path.is_file():
            continue
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("\"'")
                if key and key not in os.environ:
                    os.environ[key] = value
        break  # Use first .env found


def _get_ssl_context():
    """Create an SSL context that works on macOS with Python.org installs."""
    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except ImportError:
        pass
    return ctx


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send email via AgentMail API"
    )
    parser.add_argument("to", help="Recipient email address")
    parser.add_argument("subject", help="Email subject line")
    parser.add_argument("body", help="Email body (plain text or HTML with --html)")
    parser.add_argument(
        "--cc", action="append", default=None,
        help="CC recipient (repeatable)",
    )
    parser.add_argument(
        "--bcc", action="append", default=None,
        help="BCC recipient (repeatable)",
    )
    parser.add_argument(
        "--reply-to", default=None,
        help="Reply-to email address",
    )
    parser.add_argument(
        "--html", action="store_true",
        help="Treat body as HTML (default: plain text)",
    )
    parser.add_argument(
        "--attach", action="append", default=None,
        help="File path to attach (repeatable)",
    )
    parser.add_argument(
        "--inbox-id", default=None,
        help="AgentMail inbox ID (default: auto-discover first inbox)",
    )
    return parser.parse_args()


def get_api_key():
    _load_env()
    key = os.environ.get("AGENTMAIL_API_KEY")
    if not key:
        print(
            "Error: AGENTMAIL_API_KEY not found.\n"
            "\n"
            "Set it in your project .env file:\n"
            '  AGENTMAIL_API_KEY=your-api-key-here\n'
            "\n"
            "Or export in your shell profile (~/.zshrc):\n"
            '  export AGENTMAIL_API_KEY="your-api-key-here"\n'
            "\n"
            "Get a key at: https://console.agentmail.to",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def api_request(method, endpoint, api_key, body=None):
    """Make an HTTP request to the AgentMail API and return parsed JSON."""
    url = f"{API_BASE}{endpoint}"
    data = json.dumps(body).encode("utf-8") if body else None

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method=method,
    )

    ssl_ctx = _get_ssl_context()

    try:
        with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        if e.code == 400:
            print(
                f"Error: Bad request (HTTP 400). Check email addresses and message format.\n"
                f"Details: {err_body}",
                file=sys.stderr,
            )
        elif e.code == 403:
            print(
                f"Error: Forbidden (HTTP 403). Your API key may be invalid.\n"
                f"Details: {err_body}",
                file=sys.stderr,
            )
        elif e.code == 404:
            print(
                f"Error: Not found (HTTP 404). Inbox may not exist.\n"
                f"Details: {err_body}",
                file=sys.stderr,
            )
        elif e.code == 429:
            print(
                f"Error: Rate limited (HTTP 429).\n"
                f"Free tier: 100 emails/day, 3,000/month.\n"
                f"Details: {err_body}",
                file=sys.stderr,
            )
        else:
            print(
                f"Error: HTTP {e.code}\nDetails: {err_body}",
                file=sys.stderr,
            )
        sys.exit(1)
    except urllib.error.URLError as e:
        print(
            f"Error: Network request failed.\n"
            f"Check your internet connection.\n"
            f"Details: {e.reason}",
            file=sys.stderr,
        )
        sys.exit(1)


def discover_inbox(api_key, inbox_id=None):
    """Get inbox ID by explicit arg or auto-discover the first inbox."""
    if inbox_id:
        return inbox_id

    response = api_request("GET", "/inboxes", api_key)
    inboxes = response.get("inboxes", [])

    if not inboxes:
        print(
            "Error: No inboxes found in your AgentMail account.\n"
            "Create one at: https://console.agentmail.to\n"
            "Or use the AgentMail API to create an inbox.",
            file=sys.stderr,
        )
        sys.exit(1)

    inbox = inboxes[0]
    inbox_id = inbox.get("inbox_id")
    display = inbox.get("display_name") or inbox.get("email") or inbox_id
    print(f"Using inbox: {display}", file=sys.stderr)
    return inbox_id


def read_attachment(file_path):
    """Read a file and return an attachment dict for the API."""
    path = Path(file_path)

    if not path.exists():
        print(f"Error: Attachment not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    file_bytes = path.read_bytes()
    size_bytes = len(file_bytes)

    if size_bytes > MAX_ATTACHMENT_SIZE:
        size_mb = size_bytes / (1024 * 1024)
        print(
            f"Error: Attachment too large: {size_mb:.1f} MB (max 10 MB)\n"
            f"File: {file_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    b64_content = base64.b64encode(file_bytes).decode("utf-8")

    size_kb = size_bytes / 1024
    print(f"  Attachment: {path.name} ({size_kb:.1f} KB, {mime_type})", file=sys.stderr)

    return {
        "filename": path.name,
        "content": b64_content,
        "content_type": mime_type,
    }


def main():
    args = parse_args()
    api_key = get_api_key()

    # Discover inbox
    inbox_id = discover_inbox(api_key, args.inbox_id)

    # Build message payload
    message = {
        "to": args.to,
        "subject": args.subject,
    }

    if args.html:
        message["html"] = args.body
    else:
        message["text"] = args.body

    if args.cc:
        message["cc"] = args.cc
    if args.bcc:
        message["bcc"] = args.bcc
    if args.reply_to:
        message["reply_to"] = args.reply_to

    # Process attachments
    if args.attach:
        message["attachments"] = [read_attachment(f) for f in args.attach]

    # Send
    print(f"Sending email to {args.to}...", file=sys.stderr)
    print(f"  Subject: {args.subject[:80]}{'...' if len(args.subject) > 80 else ''}", file=sys.stderr)

    response = api_request("POST", f"/inboxes/{inbox_id}/messages/send", api_key, message)

    msg_id = response.get("message_id", "unknown")
    thread_id = response.get("thread_id", "unknown")

    print(f"Email sent.", file=sys.stderr)
    print(f"  Message ID: {msg_id}", file=sys.stderr)
    print(f"  Thread ID:  {thread_id}", file=sys.stderr)

    # Print message_id to stdout for programmatic use
    print(msg_id)


if __name__ == "__main__":
    main()
