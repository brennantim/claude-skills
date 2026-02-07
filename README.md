# Claude Code Skills

A collection of personal skills for [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Skills

| Skill | Description |
|-------|-------------|
| [generate-image](./generate-image/) | Generate and edit images using Google's Gemini API (Nano Banana Pro) |
| [send-email](./send-email/) | Send emails via AgentMail API |
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
# Add to ~/.zshrc or ~/.bashrc
export GEMINI_API_KEY="your-api-key"
```

### send-email

Requires an [AgentMail API key](https://agentmail.to).

```bash
# Add to ~/.zshrc or ~/.bashrc
export AGENTMAIL_API_KEY="your-api-key"

# Or add to .env in your project root
echo 'AGENTMAIL_API_KEY="your-api-key"' >> .env
```

## Usage

Once installed, skills are available in Claude Code:

```
# Generate an image
/generate-image a sunset over mountains --ratio 16:9

# Send an email
/send-email alice@example.com "Quick update" "The deploy went through."

# Create a new skill
/create-skill
```

Or just describe what you want and Claude will use the appropriate skill automatically.

## Contributing

These are personal skills I use daily. Feel free to fork and adapt for your own workflows.

## License

MIT
