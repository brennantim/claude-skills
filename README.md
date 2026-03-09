# Claude Code Skills

A collection of personal skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Skills

| Skill | Description |
|-------|-------------|
| [generate-image](./generate-image/) | Generate and edit images using Google's Gemini API |
| [send-email](./send-email/) | Send emails via AgentMail API |
| [recon](./recon/) | Multi-source reconnaissance: X trends, Reddit communities, web search, synthesized brief |
| [sprite](./sprite/) | Manage Fly.io Sprites (persistent Linux VMs with Claude Code) |
| [create-skill](./create-skill/) | Create new Claude Code skills following best practices |

## Installation

```bash
# Clone the repo
git clone https://github.com/brennantim/claude-skills.git

# Copy skills to your Claude Code skills directory
cp -r claude-skills/*/ ~/.claude/skills/
```

Or install individual skills:

```bash
cp -r claude-skills/generate-image ~/.claude/skills/
```

## Setup

### generate-image

Requires a [Google AI Studio API key](https://aistudio.google.com/apikey).

```bash
export GEMINI_API_KEY="your-api-key"
```

### send-email

Requires an [AgentMail API key](https://agentmail.to).

```bash
export AGENTMAIL_API_KEY="your-api-key"
```

### recon

X source requires an [X.ai API key](https://console.x.ai). Reddit and web sources work without keys.

```bash
# Python dependencies (one-time)
pip install xai-sdk redditwarp

# X source only — skip if you only need Reddit + web
export XAI_API_KEY="your-api-key"
```

After installing, create a `recon-config.json` in your project root to configure domains, subreddits, X queries, and web search categories. See [recon/references/config-guide.md](./recon/references/config-guide.md) for the schema and examples.

## Usage

Once installed, skills are available as slash commands in Claude Code:

```
/generate-image a sunset over mountains --ratio 16:9
/send-email alice@example.com "Quick update" "The deploy went through."
/recon AI coding assistants
/recon --sources reddit,web
/create-skill
```

Or just describe what you want and Claude will use the appropriate skill automatically.

## Installing a Single Skill

To install just one skill (e.g., `recon`):

```bash
# Clone and copy the skill
git clone https://github.com/brennantim/claude-skills.git /tmp/claude-skills
mkdir -p ~/.claude/skills
cp -r /tmp/claude-skills/recon ~/.claude/skills/
rm -rf /tmp/claude-skills

# Install Python dependencies (for recon)
pip install xai-sdk redditwarp
```

Then create a `recon-config.json` in your project root. See [recon/references/config-guide.md](./recon/references/config-guide.md) for schema and domain examples (Tolkien, AI/tech, SaaS, hobbyist communities).

## License

MIT
