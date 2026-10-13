
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Find the project root and load its .env file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=True)

MODEL = "gemini-3.8-flash"

CATEGORIES = [
    "road_damage",
    "water_drainage",
    "electricity",
    "sanitation",
    "mosquito_breeding",
    "streetlight",
]

URGENCY_LEVELS = ["low", "medium", "high"]

PROMPT = f"""
You are a civic issue classifier for a village and city
complaint system.

Analyze the provided image and return JSON only with exactly
these keys:
- category: one of {CATEGORIES}, or "unknown" if no category fits
- urgency: one of {URGENCY_LEVELS}
- description: one short sentence describing the visible problem

Urgency guidelines:
- high: immediate danger to life or health, such as exposed
  electrical wires, an open manhole, or sewage overflow
- medium: a problem that is worsening or affects public use
- low: a minor problem without immediate danger

Do not invent details that are not visible in the image.
"""


def classify_issue(image_path):
    # Check whether the expected environment file exists
    if not ENV_FILE.is_file():
        raise RuntimeError(
            f".env file not found at: {ENV_FILE}"
        )

    # Read the API key without displaying it
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or not api_key.strip():
        raise RuntimeError(
            "GEMINI_API_KEY is missing or empty. "
            "Check the .env file in your project root."
        )

    # Resolve and validate the image path
    image_file = Path(image_path).resolve()

    if not image_file.is_file():
        raise FileNotFoundError(
            f"Image not found: {image_file}"
        )

    # Identify supported image formats
    extension = image_file.suffix.lower()

    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    mime_type = mime_types.get(extension)

    if mime_type is None:
        raise ValueError(
            "Unsupported image format. Use PNG, JPG, JPEG, or WEBP."
        )

    # Read the image
    image_bytes = image_file.read_bytes()

    if not image_bytes:
        raise ValueError("The image file is empty.")

    # Send the image to Gemini
    client = genai.Client(api_key=api_key.strip())

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            ),
            PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    # Parse the JSON response
    result = json.loads(response.text)

    if not isinstance(result, dict):
        raise ValueError("Gemini returned an unexpected response.")

    # Validate AI output
    category = result.get("category")
    urgency = result.get("urgency")
    description = result.get("description")

    if category not in CATEGORIES and category != "unknown":
        category = "unknown"

    if urgency not in URGENCY_LEVELS:
        urgency = "medium"

    if not isinstance(description, str) or not description.strip():
        description = "No description provided."

    return {
        "category": category,
        "urgency": urgency,
        "description": description.strip(),
    }


if __name__ == "__main__":
    default_image = (
        PROJECT_ROOT / "ai" / "sample-images" / "pothole.jpg"
    )

    image_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else default_image
    )

    try:
        result = classify_issue(image_path)
        print(json.dumps(result, indent=2))

    except Exception as error:
        print(f"Classification failed: {error}", file=sys.stderr)
        sys.exit(1)