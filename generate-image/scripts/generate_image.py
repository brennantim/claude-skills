#!/usr/bin/env python3
"""Generate or edit images using Google's Gemini API.

Uses only Python stdlib (urllib, json, base64). No pip install needed.
Requires GEMINI_API_KEY environment variable.

Usage:
    python3 generate_image.py "prompt" [OPTIONS]

Text-to-image:
    python3 generate_image.py "a watercolor sunset" --ratio 16:9 --size 2K

Image editing:
    python3 generate_image.py "remove the background" --input photo.png
"""

import argparse
import base64
import json
import mimetypes
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# --- Constants ---

DEFAULT_MODEL = "gemini-3-pro-image-preview"
FAST_MODEL = "gemini-2.5-flash-image"
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

VALID_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3",
    "4:5", "5:4", "9:16", "16:9", "21:9",
]
VALID_SIZES = ["1K", "2K", "4K"]
SUPPORTED_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _get_ssl_context():
    """Create an SSL context that works on macOS with Python.org installs.

    macOS Python from python.org doesn't use the system certificate store.
    This tries certifi first (commonly available), then falls back to defaults.
    """
    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except ImportError:
        pass  # Use default certs — may work if Install Certificates.command was run
    return ctx


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate or edit images with Google Gemini API"
    )
    parser.add_argument("prompt", help="Text description of the image to generate or edit instruction")
    parser.add_argument(
        "--ratio",
        default="1:1",
        choices=VALID_RATIOS,
        help="Aspect ratio (default: 1:1)",
    )
    parser.add_argument(
        "--size",
        default="2K",
        choices=VALID_SIZES,
        help="Image resolution (default: 2K). 4K only available with default model.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: auto-generated timestamped name in cwd)",
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Path to an existing image for editing. The prompt becomes the edit instruction.",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use gemini-2.5-flash-image (faster/cheaper, max 2K)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Do not open the image after saving",
    )
    return parser.parse_args()


def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print(
            "Error: GEMINI_API_KEY environment variable is not set.\n"
            "\n"
            "To set it, add to your shell profile (~/.zshrc or ~/.bashrc):\n"
            '  export GEMINI_API_KEY="your-api-key-here"\n'
            "\n"
            "Get a key at: https://aistudio.google.com/apikey",
            file=sys.stderr,
        )
        sys.exit(1)
    return key


def read_input_image(image_path):
    """Read an image file and return (base64_data, mime_type)."""
    path = Path(image_path)

    if not path.exists():
        print(f"Error: Input image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    if path.suffix.lower() not in SUPPORTED_IMAGE_TYPES:
        print(
            f"Error: Unsupported image format '{path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_IMAGE_TYPES))}",
            file=sys.stderr,
        )
        sys.exit(1)

    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    image_bytes = path.read_bytes()
    b64_data = base64.b64encode(image_bytes).decode("utf-8")

    size_kb = len(image_bytes) / 1024
    print(f"  Input image: {path.name} ({size_kb:.1f} KB, {mime_type})", file=sys.stderr)

    return b64_data, mime_type


def build_request_body(prompt, ratio, size, input_image=None):
    """Build the JSON request body for generateContent."""
    parts = []

    # Add text prompt
    parts.append({"text": prompt})

    # Add input image if provided (for editing)
    if input_image:
        b64_data, mime_type = input_image
        parts.append({
            "inlineData": {
                "mimeType": mime_type,
                "data": b64_data,
            }
        })

    return {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": ratio,
                "imageSize": size,
            },
        },
    }


def call_gemini_api(api_key, model, request_body):
    """Make the HTTP request to the Gemini API and return parsed JSON response."""
    url = f"{API_BASE}/{model}:generateContent?key={api_key}"
    data = json.dumps(request_body).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    ssl_ctx = _get_ssl_context()

    try:
        with urllib.request.urlopen(req, timeout=120, context=ssl_ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 429:
            print(
                f"Error: Rate limited (HTTP 429). The API is busy.\n"
                f"Try again in a moment, or use --fast for the lighter model.\n"
                f"Details: {body}",
                file=sys.stderr,
            )
        elif e.code == 400:
            print(
                f"Error: Bad request (HTTP 400). The prompt may have been rejected "
                f"by safety filters, or the parameters are invalid.\n"
                f"Details: {body}",
                file=sys.stderr,
            )
        elif e.code == 403:
            print(
                f"Error: Forbidden (HTTP 403). Your API key may be invalid or "
                f"lack permissions for this model.\n"
                f"Details: {body}",
                file=sys.stderr,
            )
        else:
            print(
                f"Error: HTTP {e.code}\nDetails: {body}",
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


def extract_image_data(response):
    """Extract base64 image data and any text from the API response.

    Returns (image_bytes, mime_type, response_text).
    """
    candidates = response.get("candidates", [])
    if not candidates:
        feedback = response.get("promptFeedback", {})
        block_reason = feedback.get("blockReason", "")
        if block_reason:
            print(
                f"Error: Prompt was blocked by safety filters.\n"
                f"Reason: {block_reason}\n"
                f"Try rephrasing your prompt.",
                file=sys.stderr,
            )
        else:
            print(
                "Error: No candidates in API response.\n"
                f"Full response: {json.dumps(response, indent=2)[:500]}",
                file=sys.stderr,
            )
        sys.exit(1)

    parts = candidates[0].get("content", {}).get("parts", [])

    image_bytes = None
    mime_type = "image/png"
    response_text = ""

    for part in parts:
        if "inlineData" in part:
            inline = part["inlineData"]
            image_bytes = base64.b64decode(inline["data"])
            mime_type = inline.get("mimeType", "image/png")
        elif "text" in part:
            response_text = part["text"]

    if image_bytes is None:
        finish_reason = candidates[0].get("finishReason", "")
        print(
            f"Error: No image was generated. The model returned text only.\n"
            f"Finish reason: {finish_reason}\n"
            f"Model response: {response_text[:300]}\n"
            f"This can happen if the prompt triggers safety filters or is ambiguous.\n"
            f"Try rephrasing your prompt to be more specific about the visual output.",
            file=sys.stderr,
        )
        sys.exit(1)

    return image_bytes, mime_type, response_text


def determine_output_path(output_arg, mime_type):
    """Determine the output file path."""
    if output_arg:
        path = Path(output_arg)
        if mime_type == "image/jpeg" and path.suffix.lower() not in (".jpg", ".jpeg"):
            path = path.with_suffix(".jpg")
        elif mime_type == "image/png" and path.suffix.lower() != ".png":
            path = path.with_suffix(".png")
        return path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = ".jpg" if mime_type == "image/jpeg" else ".png"
    return Path(f"generated_{timestamp}{ext}")


def open_image(path):
    """Open the image using macOS open command."""
    try:
        subprocess.run(["open", str(path)], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass


def main():
    args = parse_args()
    api_key = get_api_key()

    # Select model
    model = FAST_MODEL if args.fast else DEFAULT_MODEL

    # Validate: 4K only on the pro model
    if args.size == "4K" and args.fast:
        print(
            "Warning: 4K size is not available with --fast (gemini-2.5-flash-image). "
            "Falling back to 2K.",
            file=sys.stderr,
        )
        args.size = "2K"

    # Read input image if provided
    input_image = None
    if args.input:
        input_image = read_input_image(args.input)

    # Build and send request
    body = build_request_body(args.prompt, args.ratio, args.size, input_image)

    mode = "Editing image" if args.input else "Generating image"
    print(f"{mode} with {model}...", file=sys.stderr)
    print(f"  Prompt: {args.prompt[:100]}{'...' if len(args.prompt) > 100 else ''}", file=sys.stderr)
    print(f"  Ratio: {args.ratio}  Size: {args.size}", file=sys.stderr)

    response = call_gemini_api(api_key, model, body)

    # Extract image
    image_bytes, mime_type, response_text = extract_image_data(response)

    # Save
    output_path = determine_output_path(args.output, mime_type)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)

    file_size_kb = len(image_bytes) / 1024
    print(f"Image saved: {output_path.resolve()} ({file_size_kb:.1f} KB)", file=sys.stderr)

    if response_text:
        print(f"Model note: {response_text[:200]}", file=sys.stderr)

    # Print the absolute path to stdout for programmatic use
    print(str(output_path.resolve()))

    # Open the image
    if not args.no_open:
        open_image(output_path.resolve())


if __name__ == "__main__":
    main()
