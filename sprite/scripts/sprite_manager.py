#!/usr/bin/env python3
"""Sprite environment manager — thin wrapper around the sprite CLI."""

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import time

SPRITE_CLI = shutil.which("sprite") or str(pathlib.Path.home() / ".local" / "bin" / "sprite")


def check_cli():
    """Verify the sprite CLI is available."""
    if not shutil.which("sprite") and not shutil.which(SPRITE_CLI):
        print("Error: sprite CLI not found. Install from https://sprites.app", file=sys.stderr)
        sys.exit(1)


def run(args, *, timeout=300, stream=False, check=True):
    """Run a sprite CLI command. Returns CompletedProcess or streams output."""
    if stream:
        return subprocess.run(args)
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        if check and result.returncode != 0:
            stderr = result.stderr.strip()
            if "not authenticated" in stderr.lower() or "login" in stderr.lower():
                print("Error: Not authenticated. Run 'sprite login' first.", file=sys.stderr)
            elif "not found" in stderr.lower():
                print("Error: Sprite not found.", file=sys.stderr)
            else:
                print(f"Error: {stderr}", file=sys.stderr)
            sys.exit(result.returncode)
        return result
    except subprocess.TimeoutExpired:
        print(f"Error: Command timed out after {timeout}s", file=sys.stderr)
        sys.exit(1)


def wait_for_ready(name, max_retries=10):
    """Wait for a sprite to be ready for exec commands.

    After create or wake, the sprite may need a moment before it accepts
    websocket connections. This retries a simple exec until it succeeds.
    """
    for i in range(max_retries):
        result = run(
            [SPRITE_CLI, "exec", "-s", name, "echo", "ready"],
            check=False, timeout=30,
        )
        if result.returncode == 0 and "ready" in result.stdout:
            return True
        # Websocket handshake failures or 502s mean the sprite is still booting
        time.sleep(1 + i * 0.5)
    print("Error: Sprite did not become ready in time.", file=sys.stderr)
    sys.exit(1)


def get_sprite_status(name):
    """Get sprite status via the API. Returns dict or None."""
    result = run(
        [SPRITE_CLI, "api", f"/", "-s", name],
        check=False, timeout=15,
    )
    if result.returncode == 0 and result.stdout.strip():
        try:
            return json.loads(result.stdout.strip().split("\n")[-1])
        except (json.JSONDecodeError, IndexError):
            pass
    return None


def sprite_exists(name):
    """Check if a sprite with the given name exists."""
    result = run([SPRITE_CLI, "list"], check=False)
    if result.returncode == 0:
        return name in result.stdout.split()
    return False


def cmd_create(args):
    """Create a sprite, boot it, and make its URL public."""
    name = args.name

    if sprite_exists(name):
        print(f"Sprite '{name}' already exists.")
        if not args.quiet:
            result = run([SPRITE_CLI, "url", "-s", name])
            print(result.stdout.strip())
        return

    print(f"Creating sprite '{name}'...")
    run([SPRITE_CLI, "create", name, "-skip-console"])

    # Force the sprite to boot — create -skip-console doesn't always start it
    print("Waiting for sprite to boot...")
    wait_for_ready(name)

    print("Setting URL to public...")
    run([SPRITE_CLI, "url", "update", "--auth", "public", "-s", name])

    result = run([SPRITE_CLI, "url", "-s", name])
    url = result.stdout.strip()
    print(f"\nSprite '{name}' is ready!")
    print(f"{url}")


def cmd_list(args):
    """List all sprites."""
    result = run([SPRITE_CLI, "list"])
    output = result.stdout.strip()
    if output:
        print(output)
    else:
        print("No sprites found.")


def cmd_url(args):
    """Print the public URL for a sprite."""
    result = run([SPRITE_CLI, "url", "-s", args.name])
    print(result.stdout.strip())


def cmd_exec(args):
    """Execute a command inside a sprite (streams output).

    If the sprite is sleeping, wakes it first with retries.
    """
    name = args.name
    cmd = [SPRITE_CLI, "exec", "-s", name] + args.command

    # First attempt
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode == 0 or "websocket" not in result.stderr.lower():
        # Worked, or failed for a non-wake reason — re-run with streaming
        if result.returncode == 0:
            # Print captured output, then we're done
            if result.stdout:
                print(result.stdout, end="")
            return
        # Non-websocket error — stream it so user sees the real error
        result = run(cmd, stream=True)
        sys.exit(result.returncode)

    # Websocket failure likely means sprite is waking — wait and retry with streaming
    print(f"Sprite '{name}' is waking up...", file=sys.stderr)
    wait_for_ready(name)
    result = run(cmd, stream=True)
    sys.exit(result.returncode)


def cmd_destroy(args):
    """Destroy a sprite."""
    run([SPRITE_CLI, "destroy", "--force", "-s", args.name])
    print(f"Sprite '{args.name}' destroyed.")


def cmd_status(args):
    """Show detailed status for a sprite."""
    name = args.name
    info = get_sprite_status(name)
    if not info:
        print(f"Could not get status for '{name}'.", file=sys.stderr)
        sys.exit(1)

    print(f"Name:    {info.get('name', 'unknown')}")
    print(f"Status:  {info.get('status', 'unknown')}")
    print(f"URL:     {info.get('url', 'none')}")
    auth = info.get("url_settings", {}).get("auth", "default")
    print(f"Auth:    {auth}")
    created = info.get("created_at", "unknown")
    print(f"Created: {created}")

    # Show services if sprite is warm/running
    if info.get("status") in ("warm", "running"):
        svc_result = run(
            [SPRITE_CLI, "exec", "-s", name, "sprite-env", "services", "list"],
            check=False,
        )
        if svc_result.returncode == 0 and svc_result.stdout.strip():
            print(f"\nServices:\n{svc_result.stdout.strip()}")


def main():
    parser = argparse.ArgumentParser(description="Manage Fly.io Sprites")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a new sprite")
    p_create.add_argument("name", help="Sprite name")
    p_create.add_argument("-q", "--quiet", action="store_true", help="Minimal output")
    p_create.set_defaults(func=cmd_create)

    p_list = sub.add_parser("list", help="List all sprites")
    p_list.set_defaults(func=cmd_list)

    p_url = sub.add_parser("url", help="Get sprite public URL")
    p_url.add_argument("name", help="Sprite name")
    p_url.set_defaults(func=cmd_url)

    p_exec = sub.add_parser("exec", help="Run a command in a sprite")
    p_exec.add_argument("name", help="Sprite name")
    p_exec.add_argument("command", nargs=argparse.REMAINDER, help="Command to run")
    p_exec.set_defaults(func=cmd_exec)

    p_destroy = sub.add_parser("destroy", help="Destroy a sprite")
    p_destroy.add_argument("name", help="Sprite name")
    p_destroy.set_defaults(func=cmd_destroy)

    p_status = sub.add_parser("status", help="Show detailed sprite status")
    p_status.add_argument("name", help="Sprite name")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    check_cli()
    args.func(args)


if __name__ == "__main__":
    main()
