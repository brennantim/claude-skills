---
name: send-email
description: Send email via AgentMail API. Use when the user asks to send, compose, draft, email, or message someone. Supports plain text, HTML bodies, CC/BCC recipients, and file attachments.
argument-hint: [recipient] [subject] [body] [--html] [--cc addr] [--attach file]
allowed-tools: Bash(python3 ~/.claude/skills/send-email/scripts/send_email.py *)
---

# Send Email with AgentMail

Send emails by running the bundled Python script. The script uses only Python stdlib (no pip install needed). It requires the `AGENTMAIL_API_KEY` environment variable.

## Usage

```bash
python3 ~/.claude/skills/send-email/scripts/send_email.py "TO" "SUBJECT" "BODY" [OPTIONS]
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--cc EMAIL` | CC recipient (repeatable) | None |
| `--bcc EMAIL` | BCC recipient (repeatable) | None |
| `--reply-to EMAIL` | Reply-to address | None |
| `--html` | Treat body as HTML | Off (plain text) |
| `--attach PATH` | Attach file (repeatable, max 10 MB each) | None |
| `--inbox-id ID` | Use a specific inbox | Auto-discovers first inbox |

### Examples

Basic email:
```bash
python3 ~/.claude/skills/send-email/scripts/send_email.py "alice@example.com" "Quick update" "The deploy went through. All good."
```

With CC and attachment:
```bash
python3 ~/.claude/skills/send-email/scripts/send_email.py "bob@example.com" "Monthly report" "Report attached." --cc manager@example.com --attach report.pdf
```

HTML email:
```bash
python3 ~/.claude/skills/send-email/scripts/send_email.py "team@example.com" "Release notes" "<h2>v2.1</h2><ul><li>New dashboard</li><li>Bug fixes</li></ul>" --html
```

## Interpreting user requests

When the user asks you to send an email:

1. **Extract the recipient** from their request. If they say a name without an email address, ask for the address.

2. **Extract the subject.** If not explicitly stated, compose a concise subject from the message context.

3. **Compose the body.** Use the user's words as the starting point. Write in a natural, professional tone unless they specify otherwise. Keep it plain text by default.

4. **Detect HTML vs plain text:**
   - Use `--html` only if the user explicitly asks for HTML formatting, or the content genuinely requires it (tables, styled layouts, rich formatting).
   - Default to plain text. Most emails should be plain text.

5. **Handle CC/BCC:**
   - Look for "CC", "copy", "also send to", "loop in" to detect CC recipients.
   - Look for "BCC", "blind copy" to detect BCC recipients.

6. **Handle attachments:**
   - If the user mentions "attach", "include the file", "send the PDF", or references a specific file path, use `--attach` with the absolute path to the file.

7. **Run the script** and report whether the email was sent. Include the recipient and subject in your confirmation.

8. **If the script fails**, read the error output and explain the issue clearly. Common fixes:
   - Missing API key: tell them to set AGENTMAIL_API_KEY
   - Rate limit: free tier allows 100 emails/day
   - Bad address: check the recipient email format

## Environment setup

The script loads `AGENTMAIL_API_KEY` from the project `.env` file (or `~/.env` as fallback). If not found in any `.env` or the environment, the script exits with setup instructions.
