---
name: create-skill
description: Create a new Claude Code skill from a description. Use when the user asks to create, build, or make a skill, command, or capability for Claude Code.
disable-model-invocation: true
---

# Skill Creator

Create Claude Code skills that follow established patterns and best practices.

## Process

### 1. Clarify Requirements

Ask the user:
- What should the skill do? (core functionality)
- When should it trigger? (description keywords)
- What inputs does it need? (arguments, files, environment variables)
- What outputs does it produce? (files, terminal output, side effects)

If the user's request is clear enough, skip unnecessary questions.

### 2. Research (if needed)

If the skill involves external APIs, libraries, or unfamiliar domains:
- Use WebSearch to find current documentation and approaches
- Favor recent sources (last 2-3 months)
- Look for Python stdlib solutions before adding dependencies

### 3. Design the Skill

Determine the skill structure:

**Name**: lowercase, hyphenated (e.g., `generate-report`, `sync-notes`)

**Description**: The trigger mechanism. Include:
- What the skill does
- Keywords that should activate it
- When to use it

**Invocation mode**:
- `disable-model-invocation: true` for skills with side effects (sending, deploying, deleting)
- Default (both user and model) for reference/utility skills

**Tools needed** (`allowed-tools`):
- Only grant what's necessary
- Use patterns like `Bash(python3 ~/.claude/skills/SKILL_NAME/scripts/*.py *)`

**Script vs instructions**:
- Use scripts for: API calls, file manipulation, deterministic operations
- Use instructions for: decision-making, interpretation, flexible workflows

### 4. Create Files

Create the skill at `~/.claude/skills/{skill-name}/`:

**SKILL.md** (required):
```yaml
---
name: skill-name
description: Clear description including trigger keywords and when to use.
argument-hint: [arg1] [--flag value]
allowed-tools: Bash(python3 ~/.claude/skills/skill-name/scripts/*.py *)
disable-model-invocation: true  # if has side effects
---

# Skill Title

Brief overview of what this skill does.

## Usage

How to use the skill with example commands.

## Options

| Flag | Description | Default |
|------|-------------|---------|
| `--flag` | What it does | Default value |

## Examples

Concrete examples showing common use cases.

## Interpreting user requests

How to translate natural language into skill invocations:
1. Extract key information from the request
2. Map to appropriate flags/arguments
3. Handle edge cases

## Environment setup

Any required environment variables or configuration.
```

**scripts/** (if needed):
- Python scripts using only stdlib when possible
- No pip install required
- Load API keys from environment or .env files
- Clear error messages with setup instructions

**references/** (if needed):
- Additional documentation Claude should reference
- Keep SKILL.md lean, put details in references

### 5. Test the Skill

After creating the skill:
1. Verify the skill appears in available skills
2. Test invocation with a simple case
3. Confirm outputs match expectations

## Reference

See [skill-patterns.md](references/skill-patterns.md) for:
- Frontmatter field reference
- Established patterns from existing skills
- Best practices from official docs
