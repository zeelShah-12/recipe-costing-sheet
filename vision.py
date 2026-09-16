import base64
import io
import json
import os

from groq import Groq
from PIL import Image

# Groq's current vision-capable model (multimodal, text + image input)
MODEL_NAME = "qwen/qwen3.8-27b"

PROMPT = """You are helping a home baker or small kitchen digitize a handwritten recipe card
into a costing sheet.

Look at this recipe photo and extract:
- recipe_name: the dish name if visible, else a reasonable guess from the ingredients, else
  "Untitled Recipe"
- servings: number of servings/pieces this recipe yields if stated, else null
- ingredients: a list of every ingredient, each with:
    - name: ingredient name, cleaned up
    - quantity: a NUMBER, converted to one of three base units (do the conversion yourself):
        * weight ingredients -> grams (e.g. "1 kg atta" -> quantity 1000, base_unit "g")
        * volume ingredients -> millilitres (e.g. "1 cup milk" -> quantity 240, base_unit "ml";
          1 tsp = 5 ml, 1 tbsp = 15 ml, 1 cup = 240 ml, 1 litre = 1000 ml)
        * countable ingredients -> pieces (e.g. "2 eggs" -> quantity 2, base_unit "pcs";
          "1 dozen" -> 12 pcs)
    - base_unit: exactly one of "g", "ml", "pcs"
    - typical_price_per_unit: your best estimate of the current typical Indian retail price,
      in INR, per **kg** (for base_unit "g"), per **litre** (for base_unit "ml"), or per
      **piece** (for base_unit "pcs"). This is just a helpful starting default the user will
      correct — make a reasonable guess, don't leave it null.

Respond with ONLY valid JSON, no markdown fences:
{
  "recipe_name": str,
  "servings": number | null,
  "ingredients": [
    {"name": str, "quantity": number, "base_unit": "g" | "ml" | "pcs", "typical_price_per_unit": number}
  ]
}
"""


def _get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return Groq(api_key=api_key)


def _image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def extract_recipe(image: Image.Image) -> dict:
    client = _get_client()
    data_url = _image_to_data_url(image)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        response_format={"type": "json_object"},
        reasoning_effort="none",
        temperature=0.2,
    )

    return json.loads(response.choices[0].message.content)
