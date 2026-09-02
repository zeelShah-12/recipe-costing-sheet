<div align="center">

# Recipe Costing Sheet

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&duration=2600&pause=900&color=0D9488&center=true&vCenter=true&width=560&lines=Photograph+a+recipe.+AI+reads+it.;Scan+%E2%86%92+Review+%E2%86%92+Price%2C+in+minutes;Real+ingredient+costs%2C+not+a+guess)](https://git.io/typing-svg)

[![Python](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Groq](https://img.shields.io/badge/Vision-Groq%20%2F%20qwen3.6--27b-F55036)](https://console.groq.com/)
[![Excel](https://img.shields.io/badge/export-Excel-217346?logo=microsoftexcel&logoColor=white)](https://openpyxl.readthedocs.io/)

</div>

Home bakers and cloud kitchens usually price a dish by gut feeling — "₹300 sounds about
right" — because working out the exact ingredient cost by hand is tedious. **Recipe
Costing Sheet** does the math:

- Photograph a handwritten (or printed) recipe — AI reads every ingredient, normalizes
  quantities to grams/millilitres/pieces, and even suggests a realistic starting price per
  kg/litre/piece so you're not starting from a blank sheet.
- Review and correct quantities, units, and prices before saving (AI-suggested prices are a
  starting point, not gospel — local prices vary).
- Every recipe is saved to a persistent **recipe book** — build up a costing library over
  time, revisit and reprice any dish as ingredient costs change.
- Pick a target profit margin (10–70%) and get the exact **suggested selling price** per
  serving and per batch.
- Export any recipe's full costing sheet to Excel (ingredients + cost breakdown + summary).

**Who pays:** Home bakers, cloud kitchens, small restaurants, tiffin services —
₹199–499/month.

## Demo

A real run: photograph a handwritten "Choco Chip Cookies" recipe card, the AI reads all 7
ingredients (with unit-normalized quantities and starting prices), review/save it, then set
a margin and get the exact selling price per serving and per batch.

![Demo](.github/assets/demo.gif)

<details>
<summary>Full costing sheet screenshot</summary>

![Screenshot](.github/assets/screenshot.png)

</details>

## Stack

- **Streamlit** — recipe-book list + live costing sheet detail view
- **Groq** (`qwen/qwen3.6-27b`) — recipe photo → structured ingredient list with unit
  normalization and starting price suggestions
- **Pandas + openpyxl** — editable pricing table + Excel export

## Local setup

```bash
cd "12 project"
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY (free at console.groq.com)
streamlit run app.py
```

Runs on `http://localhost:8501`.

## Project structure

```
12 project/
├── app.py               Streamlit UI — scan panel, recipe book, costing sheet
├── vision.py              Groq Vision call + prompt/schema for recipe OCR
├── storage.py              Flat JSON persistence for the recipe book
├── data/                   recipes.json lives here (created on first save)
├── sample_images/          (drop a demo recipe photo here for testing)
├── requirements.txt
└── .env.example
```

## Notes for the portfolio writeup

- Ingredient quantities are normalized to one of three base units (grams, millilitres,
  pieces) at extraction time, so cost math is always `(quantity / 1000) × price-per-kg-or-L`
  or `quantity × price-per-piece` — no unit-conversion edge cases scattered through the UI.
- The AI's `typical_price_per_unit` guess exists purely to save typing — it's clearly a
  starting default the user is expected to correct, not a live price feed.
- The pricing table is directly editable and changes save immediately (no separate "save"
  step), since adjusting a price is the core interaction, not an edge case.
