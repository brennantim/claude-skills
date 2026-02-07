# Skill Patterns Reference

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Display name, becomes `/slash-command`. Defaults to directory name. Lowercase, hyphens only. |
| `description` | Yes | What the skill does and when to use it. This is the trigger mechanism. |
| `argument-hint` | No | Hint shown during autocomplete: `[issue-number]`, `[filename] [--flag]` |
| `disable-model-invocation` | No | `true` = only user can invoke. Use for side effects (send, deploy, delete). |
| `user-invocable` | No | `false` = hidden from `/` menu. Use for background knowledge. |
| `allowed-tools` | No | Tools Claude can use without permission when skill is active. |
| `model` | No | Model to use when skill is active. |
| `context` | No | `fork` = run in isolated subagent context. |
| `agent` | No | Subagent type when `context: fork` is set (`Explore`, `Plan`, `general-purpose`). |

## Established Patterns

### Script-Based Skills (generate-image, send-email)

Structure:
```
skill-name/
├── SKILL.md
└── scripts/
    └── main_script.py
```

SKILL.md pattern:
```yaml
---
name: skill-name
description: Clear description with trigger keywords.
argument-hint: [required] [--optional value]
allowed-tools: Bash(python3 ~/.claude/skills/skill-name/scripts/*.py *)
---

# Skill Title

Brief overview.

## Usage

\`\`\`bash
python3 ~/.claude/skills/skill-name/scripts/script.py "ARG" [OPTIONS]
\`\`\`

## Options

| Flag | Description | Default |
|------|-------------|---------|

## Examples

Concrete examples.

## Interpreting user requests

1. Extract key info
2. Map to flags
3. Handle edge cases

## Environment setup

Required environment variables.
```

Python script pattern:
- Use only stdlib (no pip install)
- Load API keys from environment or .env
- Clear error messages with setup instructions
- Exit with informative status

### Instruction-Only Skills

For skills that don't need scripts:
```yaml
---
name: code-review
description: Review code for issues and improvements.
---

When reviewing code:
1. Check for bugs
2. Suggest improvements
3. Note style issues
```

### Reference-Heavy Skills

When SKILL.md would be too long:
```
skill-name/
├── SKILL.md (overview + navigation)
└── references/
    ├── api-docs.md
    └── examples.md
```

Reference in SKILL.md:
```markdown
## Additional resources
- For API details, see [api-docs.md](references/api-docs.md)
- For examples, see [examples.md](references/examples.md)
```

## Best Practices

1. **Concise is key** - Claude is smart, only add context it doesn't have
2. **Description is the trigger** - Make it specific about when to use
3. **Progressive disclosure** - Keep SKILL.md lean, use references for details
4. **Scripts for reliability** - Use scripts for deterministic operations
5. **Instructions for flexibility** - Use text for decision-making

## String Substitutions

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed to skill |
| `$ARGUMENTS[N]` or `$N` | Specific argument by index (0-based) |
| `${CLAUDE_SESSION_ID}` | Current session ID |

## Dynamic Context

Inject live data with `!`command``:
```markdown
Current branch: !`git branch --show-current`
Staged files: !`git diff --cached --name-only`
```

Commands run before Claude sees the content.
