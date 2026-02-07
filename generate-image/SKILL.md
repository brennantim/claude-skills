---
name: generate-image
description: Generate or edit images using Google's Gemini API. Use this skill when the user asks to create, generate, draw, or make an image, picture, illustration, photo, graphic, icon, logo, or visual. Also use when the user asks to edit, modify, change, or transform an existing image. Supports aspect ratios, sizes up to 4K, and image editing with an input image.
argument-hint: [prompt] [--ratio 16:9] [--size 2K] [--output path.png] [--input image.png] [--fast]
allowed-tools: Bash(python3 ~/.claude/skills/generate-image/scripts/generate_image.py *), Bash(open *)
---

# Image Generation & Editing with Gemini

Generate or edit images by running the bundled Python script. The script uses only Python stdlib (no pip install needed). It requires the `GEMINI_API_KEY` environment variable.

## Usage

```bash
python3 ~/.claude/skills/generate-image/scripts/generate_image.py "PROMPT" [OPTIONS]
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--ratio RATIO` | Aspect ratio: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9 | 1:1 |
| `--size SIZE` | Resolution: 1K, 2K, 4K (4K only with default model) | 2K |
| `--output PATH` | Output file path (auto-adds .png if needed) | Auto-generated timestamped name in cwd |
| `--input PATH` | Input image for editing mode | None (text-to-image) |
| `--fast` | Use gemini-2.5-flash-image (faster, cheaper, max 2K) | Off (uses gemini-3-pro-image-preview) |
| `--no-open` | Do not open the image after generation | Off (opens by default) |

### Examples

Basic generation:
```bash
python3 ~/.claude/skills/generate-image/scripts/generate_image.py "a watercolor painting of a mountain lake at sunset"
```

With options:
```bash
python3 ~/.claude/skills/generate-image/scripts/generate_image.py "product photo of a coffee mug" --ratio 4:3 --size 4K --output mug.png
```

Fast model:
```bash
python3 ~/.claude/skills/generate-image/scripts/generate_image.py "simple icon of a house" --fast --ratio 1:1 --size 1K
```

Image editing:
```bash
python3 ~/.claude/skills/generate-image/scripts/generate_image.py "remove the background and replace with a beach scene" --input photo.png
```

## Interpreting user requests

When the user asks you to generate or edit an image:

1. **Extract the prompt** from their request. Use their description as-is when it's detailed. Enhance vague requests with reasonable artistic details.

2. **Detect generate vs edit mode:**
   - If the user references an existing image file, use `--input` with that file path.
   - If they say "edit", "modify", "change", "update", "fix", or "transform" an image, use `--input`.
   - Otherwise, it's a text-to-image generation.

3. **Choose aspect ratio** based on context:
   - Portrait/vertical/phone/story: `9:16`
   - Landscape/wide/desktop/banner: `16:9`
   - Ultra-wide/cinematic: `21:9`
   - Square/social media/icon/avatar: `1:1`
   - Standard photo: `4:3` or `3:2`
   - Tall/poster/pin: `2:3` or `3:4`

4. **Choose size:**
   - Default to `2K` for most requests.
   - Use `4K` if they ask for high-res, print-quality, or detailed output.
   - Use `1K` for quick drafts, icons, or thumbnails.

5. **Choose output path:**
   - If they specify a filename or location, use `--output`.
   - Otherwise let it auto-generate a timestamped filename in the current directory.

6. **Run the script** and report the output path and file size to the user.

7. **If the script fails**, read the error output and explain the issue clearly. Common fixes:
   - Missing API key: tell them to set GEMINI_API_KEY
   - Safety filter: suggest rephrasing the prompt
   - Rate limit: suggest waiting or using --fast

## Environment setup

The `GEMINI_API_KEY` environment variable must be set. If missing, the script exits with setup instructions.
