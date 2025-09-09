import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime

# --- Conversion dictionaries ---
length_units = {
    "meter": 1, "centimeter": 100, "kilometer": 0.001,
    "inch": 39.3701, "foot": 3.28084, "yard": 1.09361, "mile": 0.000621371
}

mass_units = {
    "kilogram": 1, "gram": 1000, "milligram": 1e6,
    "pound": 2.20462, "ounce": 35.274
}

volume_units = {
    "liter": 1, "milliliter": 1000,
    "gallon (US)": 0.264172, "cup (US)": 4.22675, "fluid ounce (US)": 33.814
}

temperature_units = ["Celsius", "Fahrenheit", "Kelvin"]

# --- History store ---
history = []

# --- Conversion function ---
def convert(category, from_unit, to_unit, value):
    try:
        value = float(value)
    except:
        return "⚠️ Please enter a numeric value."
    
    result = None
    if category == "Length":
        result = value / length_units[from_unit] * length_units[to_unit]
    elif category == "Mass":
        result = value / mass_units[from_unit] * mass_units[to_unit]
    elif category == "Volume":
        result = value / volume_units[from_unit] * volume_units[to_unit]
    elif category == "Temperature":
        if from_unit == "Celsius":
            if to_unit == "Fahrenheit":
                result = (value * 9/5) + 32
            elif to_unit == "Kelvin":
                result = value + 273.15
            else:
                result = value
        elif from_unit == "Fahrenheit":
            if to_unit == "Celsius":
                result = (value - 32) * 5/9
            elif to_unit == "Kelvin":
                result = (value - 32) * 5/9 + 273.15
            else:
                result = value
        elif from_unit == "Kelvin":
            if to_unit == "Celsius":
                result = value - 273.15
            elif to_unit == "Fahrenheit":
                result = (value - 273.15) * 9/5 + 32
            else:
                result = value

    # Save history
    timestamp = datetime.now().strftime("%H:%M:%S")
    history.append([timestamp, category, f"{value} {from_unit} → {to_unit}", f"{result:.4f} {to_unit}"])
    return f"{result:.4f} {to_unit}"

# --- Helper for updating unit choices ---
def update_units(category):
    if category == "Length":
        return gr.update(choices=list(length_units.keys()), value="meter"), gr.update(choices=list(length_units.keys()), value="centimeter")
    elif category == "Mass":
        return gr.update(choices=list(mass_units.keys()), value="kilogram"), gr.update(choices=list(mass_units.keys()), value="gram")
    elif category == "Volume":
        return gr.update(choices=list(volume_units.keys()), value="liter"), gr.update(choices=list(volume_units.keys()), value="milliliter")
    elif category == "Temperature":
        return gr.update(choices=temperature_units, value="Celsius"), gr.update(choices=temperature_units, value="Fahrenheit")

# --- Generate CSV + Image ---
def gen_files():
    if not history:
        return "⚠️ No history yet.", None, None
    df = pd.DataFrame(history, columns=["Time","Category","From→To","Result"])
    csv_path = "history.csv"
    img_path = "history.png"
    df.to_csv(csv_path, index=False)

    plt.figure(figsize=(8,2))
    plt.axis("off")
    plt.table(cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center")
    plt.savefig(img_path, bbox_inches="tight")
    plt.close()
    return "✅ Files ready!", csv_path, img_path

# --- Build UI ---
with gr.Blocks(css="""
body {background-color: #121212; color: #E0E0E0;}
.card {background-color:#1E1E1E; border-radius:12px; padding:16px;}
button {background-color:#1976D2 !important; color:white !important;}
""") as app:
    gr.Markdown("## 🌐 Unit Converter (Dark Mode)")

    with gr.Row():
        with gr.Column(scale=1, elem_classes="card"):
            category = gr.Dropdown(["Length","Mass","Volume","Temperature"], label="Category", value="Length")
            from_unit = gr.Dropdown(list(length_units.keys()), label="From Unit", value="meter")
            to_unit = gr.Dropdown(list(length_units.keys()), label="To Unit", value="centimeter")
            value = gr.Number(label="Value", value=1)
            convert_btn = gr.Button("Convert")
        with gr.Column(scale=1, elem_classes="card"):
            result = gr.Textbox(label="Result", interactive=False)
    
    # History
    hist = gr.Dataframe(headers=["Time","Category","From→To","Result"], label="History", interactive=False, wrap=True)

    # Downloads
    with gr.Row():
        with gr.Column(elem_classes="card"):
            btn_csv = gr.Button("Generate CSV + Image", elem_id="csv")
            status = gr.Textbox(label="Status", interactive=False)
            file_csv = gr.File(label="Download CSV", visible=False)
            file_img = gr.File(label="Download Image", visible=False)

    # --- Logic ---
    category.change(update_units, category, [from_unit, to_unit])
    convert_btn.click(convert, [category, from_unit, to_unit, value], result)

    def update_history():
        if history:
            return pd.DataFrame(history, columns=["Time","Category","From→To","Result"])
        return pd.DataFrame(columns=["Time","Category","From→To","Result"])
    convert_btn.click(update_history, None, hist)

    def do_files():
        msg, csv, img = gen_files()
        if csv and img:
            return msg, gr.update(value=csv, visible=True), gr.update(value=img, visible=True)
        else:
            return "⚠️ No history to export", gr.update(visible=False), gr.update(visible=False)
    btn_csv.click(do_files, None, [status, file_csv, file_img])

# ✅ Entry point for Hugging Face / local run
if __name__ == "__main__":
    app.launch()
