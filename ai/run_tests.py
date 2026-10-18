import os
import sys
import time
from datetime import date

# Lets this file import code from the project root: python ai/run_tests.py
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
from ai.classify import classify_issue  # noqa: E402

IMAGE_DIR = os.path.join(ROOT_DIR, "ai", "sample-images")
OUTPUT_FILE = os.path.join(ROOT_DIR, "ai", "test-results.md")
IMAGE_TYPES = (".jpg", ".jpeg", ".png")


def clean(text):
    # Keeps text safe inside a markdown table cell
    return str(text).replace("|", "/").replace("\n", " ")


def main():
    if not os.path.isdir(IMAGE_DIR):
        print("Folder ai/sample-images not found.")
        return

    files = sorted(f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(IMAGE_TYPES))
    if not files:
        print("No photos found in ai/sample-images. Add some and run again.")
        return

    lines = [
        "# Classification test results",
        "",
        f"Run date: {date.today().isoformat()}",
        "",
        "Output of `classify_issue()` for every photo in `ai/sample-images/`.",
        "The last column is filled in by hand after checking each result against the photo.",
        "",
        "| Photo | Category | Urgency | Description | Correct? |",
        "|---|---|---|---|---|",
    ]

    for name in files:
        print("Testing " + name + " ...")
        try:
            result = classify_issue(os.path.join(IMAGE_DIR, name))
            row = [name, result["category"], result["urgency"], result.get("description", "")]
        except Exception as error:
            row = [name, "ERROR", "-", str(error)[:120]]
        lines.append("| " + " | ".join(clean(cell) for cell in row) + " | |")
        time.sleep(2)  # stay under the free-tier rate limit

    lines += [
        "",
        "## Findings",
        "",
        "(Write 3 or 4 lines by hand: what worked, what went wrong, what to improve.)",
        "",
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Done. Results saved to ai/test-results.md")


if __name__ == "__main__":
    main()