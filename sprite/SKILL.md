---
name: sprite
description: Manage Fly.io Sprites — persistent Linux VMs with Claude Code pre-installed. Use when the user asks to create, deploy, manage, or destroy sprites, remote dev environments, or deploy web apps to sprites.
disable-model-invocation: true
argument-hint: <command> [name] [options]
allowed-tools: Bash(python3 ~/.claude/skills/sprite/scripts/sprite_manager.py *), Bash(sprite *)
---

# Sprite Manager

Manage Fly.io Sprites — persistent, hardware-isolated Linux VMs that boot in ~2 seconds, auto-sleep after 30s of inactivity, and auto-wake on HTTP request. Each sprite comes with Claude Code, Node.js, Python, Go, and more pre-installed. Public URL at `https://<name>-<id>.sprites.app` on port 8080.

## How Sprites Work (important context)

- **Sleep**: Sprites auto-sleep after ~30s of inactivity. Running processes and in-memory data are lost. Filesystem persists.
- **Wake**: An HTTP request to the sprite's URL triggers a wake (boot). All registered services auto-restart on boot.
- **Services**: Use `sprite-env services create` inside the sprite to register persistent services. Services auto-restart on every boot (wake). The `--http-port 8080` flag is critical — it tells the proxy to route HTTP traffic to that service and auto-start it on incoming requests.
- **Processes started via `sprite exec` or `sprite console` do NOT survive sleep.** Only registered services persist.

## Simple Commands

Delegate these to `sprite_manager.py`:

| Command | Action |
|---------|--------|
| `/sprite create <name>` | Create sprite, boot it, set URL public |
| `/sprite list` | List all sprites |
| `/sprite url <name>` | Print public URL |
| `/sprite exec <name> <cmd...>` | Run command in sprite (auto-wakes if sleeping) |
| `/sprite destroy <name>` | Destroy sprite |
| `/sprite status <name>` | Show status, URL, auth, and services |

### Examples

```bash
python3 ~/.claude/skills/sprite/scripts/sprite_manager.py create my-app
python3 ~/.claude/skills/sprite/scripts/sprite_manager.py list
python3 ~/.claude/skills/sprite/scripts/sprite_manager.py url my-app
python3 ~/.claude/skills/sprite/scripts/sprite_manager.py exec my-app -- ls -la
python3 ~/.claude/skills/sprite/scripts/sprite_manager.py status my-app
python3 ~/.claude/skills/sprite/scripts/sprite_manager.py destroy my-app
```

## Deploy Workflow

When the user says `/sprite deploy <name> "<description>"` or asks to build/deploy a web app on a sprite, follow this multi-step flow. **You orchestrate this directly** because you need to construct prompts and determine the right service command.

### Step 1: Create the sprite (if needed)

```bash
python3 ~/.claude/skills/sprite/scripts/sprite_manager.py create <name>
```

This handles creation, boot verification, and setting the URL public. If the sprite already exists it's a no-op.

### Step 2: Build the app

You have two options depending on complexity:

**Option A — Simple apps (recommended for quick deploys):**
Build the app directly with `sprite exec` commands. Write files, install deps, etc:

```bash
sprite exec -s <name> bash -c 'mkdir -p /home/user/app && cd /home/user/app && npm init -y && npm install express'
sprite exec -s <name> bash -c 'cat > /home/user/app/server.js << '\''EOF'\''
// ... app code ...
EOF'
```

**Option B — Complex apps (use Claude Code inside the sprite):**

```bash
sprite exec -s <name> claude --dangerously-skip-permissions -p "<augmented prompt>"
```

When constructing the prompt, always append these constraints:

```
IMPORTANT CONSTRAINTS:
- The app MUST listen on port 8080 (the only publicly exposed port)
- Use a simple tech stack: plain HTML/CSS/JS, Node.js with Express, or Python with Flask
- All files go in /home/user/app
- After building, verify the server starts successfully, then exit
```

Shell-escape the prompt carefully. Prefer single quotes and escape inner single quotes.

**Note**: Claude Code inside the sprite requires authentication. If it fails with "not logged in", fall back to Option A.

### Step 3: Register the service (critical for sleep/wake)

**Always include `--http-port 8080`** — this ensures the proxy auto-starts the service on incoming HTTP requests after the sprite wakes from sleep.

Use `--dir` to set the working directory so the service runs from the right place:

```bash
sprite exec -s <name> sprite-env services create web --cmd node --args server.js --dir /home/user/app --http-port 8080
```

Common patterns:
- **Node.js**: `--cmd node --args server.js --dir /home/user/app --http-port 8080`
- **Python**: `--cmd python3 --args app.py --dir /home/user/app --http-port 8080`
- **Static (npx serve)**: `--cmd npx --args serve,-s,public,-l,8080 --dir /home/user/app --http-port 8080`

If a `web` service already exists, delete it first:
```bash
sprite exec -s <name> sprite-env services delete web
```

### Step 4: Verify and report

```bash
# Verify the service is running
sprite exec -s <name> sprite-env services list

# Get the URL
sprite url -s <name>
```

Report to the user:
- The public URL
- What was built
- That it auto-sleeps after 30s of inactivity and auto-wakes on the next HTTP request
- That the service is registered and will persist across sleep/wake cycles

## Updating a Deployed App

When the user wants to modify an app on an existing sprite:

1. Make changes via `sprite exec` (edit files, install deps, etc.)
2. Restart the service: `sprite exec -s <name> sprite-env services restart web`
3. If the start command changed, delete and recreate the service with the new `--cmd`/`--args`

## Interpreting User Requests

- "create a sprite" / "spin up a VM" / "make a dev environment" → `create`
- "show my sprites" / "what sprites do I have" → `list`
- "get the URL for X" / "where is X running" → `url`
- "run X in the sprite" / "execute X on Y" → `exec`
- "delete/remove/tear down X" → `destroy`
- "what's the status of X" / "is X running" → `status`
- "deploy X" / "build X on a sprite" / "make a web app" → deploy workflow
- "deploy a landing page" / "build me a todo app" → deploy workflow (infer name if not given)
- "update the app on X" / "change X to..." → update workflow

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 502 on the public URL | Service not registered or not using `--http-port` | Register service with `--http-port 8080` |
| Websocket handshake error on exec | Sprite is sleeping/waking | Script auto-retries; wait a few seconds |
| App works then stops after ~30s | Process started via exec, not as a service | Register with `sprite-env services create` |
| Service crashes on wake | Wrong `--dir` or missing deps | Check logs: `sprite exec -s <name> cat /.sprite/logs/services/web.log` |
| "Not logged in" from Claude Code | Claude Code not authenticated inside sprite | Fall back to building with direct exec commands |

## Notes

- Sprites cost ~$0.07/CPU-hour and are practically free when sleeping
- The `sprite` CLI should be on your PATH (install from https://sprites.app)
- Claude Code is pre-installed in every sprite (but may need auth)
- Only one service can have `--http-port` at a time
- Services auto-restart with exponential backoff (1s → 60s cap) on crash
- Use `sprite exec -s <name> sprite-env services list` to inspect running services
- Service logs: `sprite exec -s <name> cat /.sprite/logs/services/web.log`
