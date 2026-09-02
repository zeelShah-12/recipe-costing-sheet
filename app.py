import io
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from storage import load_recipes, save_recipes
from vision import extract_recipe

load_dotenv()

st.set_page_config(
    page_title="Recipe Costing Sheet",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}

    .block-container {
        padding-top: 1.75rem;
        padding-bottom: 3rem;
        max-width: 1300px;
    }

    /* dark-to-teal gradient hero fading into the white body, per inspo */
    .hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(160deg, #0a0f0d 0%, #0f3d34 45%, #0d9488 85%, #2dd4bf 100%);
        border-radius: 16px;
        padding: 2rem 2.25rem 2.5rem 2.25rem;
        margin-bottom: 1.5rem;
        color: #f0fdfa;
    }
    .hero h1 { margin: 0 0 0.4rem 0; font-size: 2.1rem; color: #ffffff; max-width: 560px; }
    .hero p { margin: 0; opacity: 0.88; font-size: 0.98rem; max-width: 560px; }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 100px;
        padding: 0.2rem 0.7rem;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #ccfbf1;
        background: rgba(255,255,255,0.08);
        margin-bottom: 0.7rem;
    }

    .stat-row { display: flex; gap: 2.5rem; margin-top: 1.5rem; }
    .stat-num { font-size: 1.8rem; font-weight: 800; color: #ffffff; line-height: 1; }
    .stat-label { font-size: 0.78rem; color: #ccfbf1; opacity: 0.85; margin-top: 0.25rem; }

    /* icon-square feature cards, per inspo's colored-badge cards */
    .feature-card {
        border: 1px solid rgba(17,24,39,0.08);
        border-radius: 12px;
        padding: 1rem 1.1rem 1.15rem 1.1rem;
        height: 100%;
        background: #fafafa;
    }
    .icon-square {
        width: 34px; height: 34px;
        border-radius: 9px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.8rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.6rem;
    }
    .feature-card h4 { margin: 0 0 0.3rem 0; font-size: 0.98rem; color: #111827; }
    .feature-card p { margin: 0; font-size: 0.85rem; color: #6b7280; line-height: 1.4; }

    div[data-testid="stMetric"] {
        background: var(--secondary-background-color);
        border: 1px solid rgba(17,24,39,0.1);
        border-radius: 12px;
        padding: 0.9rem 1rem 0.7rem 1rem;
    }
    div[data-testid="stMetricLabel"] { font-size: 0.85rem; opacity: 0.75; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem; overflow: visible; white-space: nowrap; }

    .upload-card, .empty-state {
        border: 1px dashed rgba(17,24,39,0.2);
        border-radius: 14px;
        padding: 1.5rem;
        text-align: center;
        opacity: 0.8;
    }

    section[data-testid="stFileUploaderDropzone"] { border-radius: 12px; }
    div[data-testid="stButton"] > button {
        text-align: left;
        justify-content: flex-start;
        border-radius: 10px;
        font-weight: 500;
        border: 1px solid rgba(17,24,39,0.12);
    }
    .stButton > button[kind="primary"] {
        background: #0d9488;
        border: 1px solid #0d9488;
    }
    .stButton > button[kind="primary"]:hover {
        background: #0f766e;
        border: 1px solid #0f766e;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "recipes" not in st.session_state:
    st.session_state.recipes = load_recipes()
if "selected_recipe" not in st.session_state:
    st.session_state.selected_recipe = None
if "pending_recipe" not in st.session_state:
    st.session_state.pending_recipe = None

recipe_count = len(st.session_state.recipes)
ingredient_count = sum(len(r.get("ingredients", [])) for r in st.session_state.recipes.values())

st.markdown(
    f"""
    <div class="hero">
        <span class="eyebrow">&#9670; AI-POWERED COSTING</span>
        <h1>Recipe Costing Sheet</h1>
        <p>Photograph a handwritten recipe — AI reads the ingredients and suggests starting
        prices. You confirm the prices, set your margin, and get an exact selling price.</p>
        <div class="stat-row">
            <div><div class="stat-num">{recipe_count}</div><div class="stat-label">Recipes saved</div></div>
            <div><div class="stat-num">{ingredient_count}</div><div class="stat-label">Ingredients tracked</div></div>
            <div><div class="stat-num">10-70%</div><div class="stat-label">Margin range</div></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

f1, f2, f3 = st.columns(3, gap="medium")
for col, color, num, title, desc in [
    (f1, "#ec4899", "01", "Scan", "Photograph a handwritten or printed recipe."),
    (f2, "#0d9488", "02", "Review", "Fix quantities, units, or suggested prices before saving."),
    (f3, "#8b5cf6", "03", "Price", "Set your margin, get the exact selling price per serving."),
]:
    col.markdown(
        f"""
        <div class="feature-card">
            <div class="icon-square" style="background:{color};">{num}</div>
            <h4>{title}</h4>
            <p>{desc}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)


def ingredient_cost(quantity: float, base_unit: str, price_per_unit: float) -> float:
    if base_unit in ("g", "ml"):
        return (quantity / 1000.0) * price_per_unit
    return quantity * price_per_unit


with st.sidebar:
    st.markdown(
        "**Who this is for**\n\n"
        "Home bakers, cloud kitchens, small restaurants, and tiffin services who need to "
        "know the exact cost of a dish before pricing it — not a guess."
    )
    st.markdown("---")
    st.caption(f"{len(st.session_state.recipes)} recipe(s) in your book.")

# ------------------------------------------------------------ scan panel ---

with st.expander("Scan a recipe photo", expanded=not st.session_state.recipes):
    uploaded_file = st.file_uploader(
        "Photo of a handwritten or printed recipe", type=["jpg", "jpeg", "png", "webp"]
    )

    if uploaded_file:
        col_img, col_action = st.columns([1, 1])
        with col_img:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, use_container_width=True)
        with col_action:
            if st.button("Extract recipe", type="primary", use_container_width=True):
                with st.spinner("Reading recipe..."):
                    try:
                        st.session_state.pending_recipe = extract_recipe(image)
                    except Exception as exc:
                        st.error(f"Extraction failed: {exc}")

    if st.session_state.pending_recipe is not None:
        pending = st.session_state.pending_recipe
        st.markdown("**Review before saving** — fix quantities, units, or prices:")

        c1, c2 = st.columns([2, 1])
        recipe_name = c1.text_input("Recipe name", value=pending.get("recipe_name", "Untitled Recipe"))
        servings = c2.number_input(
            "Servings", min_value=1, value=int(pending.get("servings") or 1), step=1
        )

        ing_df = pd.DataFrame(pending.get("ingredients", []))
        if ing_df.empty:
            st.info("No ingredients were detected in this photo.")
        else:
            ing_df = ing_df.rename(
                columns={
                    "name": "Ingredient",
                    "quantity": "Quantity",
                    "base_unit": "Unit",
                    "typical_price_per_unit": "Price per kg/L/pc (₹)",
                }
            )
            edited = st.data_editor(
                ing_df,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                column_config={
                    "Ingredient": st.column_config.TextColumn(width="medium"),
                    "Quantity": st.column_config.NumberColumn(format="%.1f"),
                    "Unit": st.column_config.SelectboxColumn(options=["g", "ml", "pcs"]),
                    "Price per kg/L/pc (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                },
                key="pending_ing_editor",
            )

            b1, b2 = st.columns(2)
            if b1.button("Save recipe", type="primary", use_container_width=True):
                ingredients = []
                for row in edited.to_dict("records"):
                    if not row.get("Ingredient"):
                        continue
                    ingredients.append(
                        {
                            "name": str(row["Ingredient"]).strip(),
                            "quantity": float(row.get("Quantity") or 0),
                            "base_unit": row.get("Unit") or "g",
                            "price_per_unit": float(row.get("Price per kg/L/pc (₹)") or 0),
                        }
                    )
                recipe_id = str(uuid.uuid4())
                st.session_state.recipes[recipe_id] = {
                    "name": recipe_name.strip() or "Untitled Recipe",
                    "servings": int(servings),
                    "ingredients": ingredients,
                    "margin_pct": 35,
                    "created_at": datetime.now().isoformat(),
                }
                save_recipes(st.session_state.recipes)
                st.session_state.pending_recipe = None
                st.session_state.selected_recipe = recipe_id
                st.success(f"Saved '{recipe_name}' with {len(ingredients)} ingredients.")
                st.rerun()
            if b2.button("Discard", use_container_width=True):
                st.session_state.pending_recipe = None
                st.rerun()

st.markdown("---")

# --------------------------------------------------------------- layout ----

left, right = st.columns([1, 1.7], gap="large")

with left:
    st.markdown("#### Recipe book")
    if not st.session_state.recipes:
        st.markdown(
            '<div class="empty-state">No recipes yet.<br>Scan a recipe photo above '
            "to get started.</div>",
            unsafe_allow_html=True,
        )
    else:
        for rid, r in sorted(
            st.session_state.recipes.items(), key=lambda kv: kv[1]["name"].lower()
        ):
            total = sum(
                ingredient_cost(i["quantity"], i["base_unit"], i["price_per_unit"])
                for i in r["ingredients"]
            )
            label = f"{r['name']} — ₹{total:,.0f} total"
            if st.button(label, key=f"recipe_{rid}", use_container_width=True):
                st.session_state.selected_recipe = rid

        st.markdown("---")
        if st.session_state.selected_recipe and st.button(
            "Delete this recipe", use_container_width=True
        ):
            st.session_state.recipes.pop(st.session_state.selected_recipe, None)
            save_recipes(st.session_state.recipes)
            st.session_state.selected_recipe = None
            st.rerun()

with right:
    st.markdown("#### Costing")

    sel_id = st.session_state.selected_recipe
    if not st.session_state.recipes:
        st.markdown(
            '<div class="empty-state">Your recipe book is empty.<br>'
            "Scan a recipe to add your first costing sheet.</div>",
            unsafe_allow_html=True,
        )
    elif not sel_id or sel_id not in st.session_state.recipes:
        st.markdown(
            '<div class="empty-state">Select a recipe from your book to view '
            "its costing sheet.</div>",
            unsafe_allow_html=True,
        )
    else:
        recipe = st.session_state.recipes[sel_id]
        st.markdown(f"**{recipe['name']}** · {recipe['servings']} servings")

        price_df = pd.DataFrame(recipe["ingredients"]).rename(
            columns={
                "name": "Ingredient",
                "quantity": "Quantity",
                "base_unit": "Unit",
                "price_per_unit": "Price per kg/L/pc (₹)",
            }
        )
        edited_prices = st.data_editor(
            price_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "Ingredient": st.column_config.TextColumn(width="medium"),
                "Quantity": st.column_config.NumberColumn(format="%.1f"),
                "Unit": st.column_config.SelectboxColumn(options=["g", "ml", "pcs"]),
                "Price per kg/L/pc (₹)": st.column_config.NumberColumn(format="₹%.2f"),
            },
            key=f"price_editor_{sel_id}",
        )

        updated_ingredients = [
            {
                "name": row["Ingredient"],
                "quantity": float(row["Quantity"] or 0),
                "base_unit": row["Unit"],
                "price_per_unit": float(row["Price per kg/L/pc (₹)"] or 0),
            }
            for row in edited_prices.to_dict("records")
            if row.get("Ingredient")
        ]

        if updated_ingredients != recipe["ingredients"]:
            recipe["ingredients"] = updated_ingredients
            st.session_state.recipes[sel_id] = recipe
            save_recipes(st.session_state.recipes)

        total_cost = sum(
            ingredient_cost(i["quantity"], i["base_unit"], i["price_per_unit"])
            for i in recipe["ingredients"]
        )
        cost_per_serving = total_cost / max(recipe["servings"], 1)

        margin = st.slider(
            "Target profit margin (%)",
            min_value=10,
            max_value=70,
            value=int(recipe.get("margin_pct", 35)),
            step=5,
        )
        if margin != recipe.get("margin_pct"):
            recipe["margin_pct"] = margin
            st.session_state.recipes[sel_id] = recipe
            save_recipes(st.session_state.recipes)

        suggested_price_serving = (
            cost_per_serving / (1 - margin / 100) if margin < 100 else float("inf")
        )
        suggested_price_batch = suggested_price_serving * recipe["servings"]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total cost", f"₹{total_cost:,.0f}")
        m2.metric("Cost / serving", f"₹{cost_per_serving:,.2f}")
        m3.metric(
            "Price",
            f"₹{suggested_price_serving:,.2f}",
            help="Suggested selling price per serving at your chosen margin",
        )
        m4.metric(
            "Batch",
            f"₹{suggested_price_batch:,.0f}",
            help="Suggested selling price for the whole batch",
        )

        st.caption(
            f"At a {margin}% margin, selling each serving for "
            f"₹{suggested_price_serving:,.2f} covers your ₹{cost_per_serving:,.2f} "
            "ingredient cost and leaves the rest as profit."
        )

        export_df = pd.DataFrame(recipe["ingredients"]).rename(
            columns={
                "name": "Ingredient",
                "quantity": "Quantity",
                "base_unit": "Unit",
                "price_per_unit": "Price per kg/L/pc",
            }
        )
        export_df["Cost (₹)"] = [
            round(ingredient_cost(i["quantity"], i["base_unit"], i["price_per_unit"]), 2)
            for i in recipe["ingredients"]
        ]

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Ingredients")
            summary_df = pd.DataFrame(
                [
                    {"Metric": "Total cost", "Value": round(total_cost, 2)},
                    {"Metric": "Cost per serving", "Value": round(cost_per_serving, 2)},
                    {"Metric": "Margin %", "Value": margin},
                    {"Metric": "Suggested price per serving", "Value": round(suggested_price_serving, 2)},
                    {"Metric": "Suggested batch price", "Value": round(suggested_price_batch, 2)},
                ]
            )
            summary_df.to_excel(writer, index=False, sheet_name="Summary")
        excel_buffer.seek(0)

        st.download_button(
            "⬇️ Download costing sheet (Excel)",
            excel_buffer,
            file_name=f"{recipe['name'].replace(' ', '_')}_costing.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
