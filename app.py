# app.py — Dark Themed Premium Unit Converter (with conditional downloads)
import os
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import gradio as gr

# ========== Units ==========
UNITS = {
    "Length": {
        "meter (m)": 1.0,
        "centimeter (cm)": 0.01,
        "kilometer (km)": 1000.0,
        "inch (in)": 0.0254,
        "foot (ft)": 0.3048,
        "yard (yd)": 0.9144,
        "mile (mi)": 1609.344
    },
    "Mass": {
        "kilogram (kg)": 1.0,
        "gram (g)": 0.001,
        "milligram (mg)": 1e-6,
        "pound (lb)": 0.45359237,
        "ounce (oz)": 0.028349523125
    },
    "Volume": {
        "liter (L)": 1.0,
        "milliliter (mL)": 0.001,
        "gallon (US)": 3.785411784,
        "cup (US)": 0.2365882365,
        "fluid ounce (US)": 0.0295735295625
    },
    "Temperature": {
        "Celsius (°C)": "C",
        "Fahrenheit (°F)": "F",
        "Kelvin (K)": "K"
    }
}

# ========== Conversion ==========
def _fmt(x, d=6):
    try:
        v = float(x)
    except:
        return str(x)
    s = f"{v:.{d}f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s

def convert_temp(val, fu, tu):
    v = float(val)
    fc, tc = UNITS["Temperature"][fu], UNITS["Temperature"][tu]
    if fc == tc:
        return _fmt(v)

    def to_c(x, c):
        return x if c == "C" else (x - 32) * 5/9 if c == "F" else x - 273.15

    def from_c(c, c2):
        return c if c2 == "C" else c * 9/5 + 32 if c2 == "F" else c + 273.15

    return _fmt(from_c(to_c(v, fc), tc))

def convert_val(cat, val, fu, tu):
    try:
        v = float(val)
    except:
        return "❗ Enter a number"
    if fu == tu:
        return _fmt(v)
    if cat == "Temperature":
        return convert_temp(v, fu, tu)
    f1, f2 = UNITS[cat].get(fu), UNITS[cat].get(tu)
    if not f1 or not f2:
        return "❗ Invalid units"
    return _fmt(v * f1 / f2)

# ========== History ==========
HISTORY, MAXH = [], 30
def add_hist(cat, val, fu, tu, res):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    HISTORY.append([ts, cat, f"{val} {fu}", f"{res} {tu}"])
    if len(HISTORY) > MAXH:
        HISTORY.pop(0)

def get_hist():
    if not HISTORY:
        return []
    return pd.DataFrame(HISTORY[::-1], columns=["Time","Category","From","Result"])

# ========== CSV + Image ==========
def gen_files():
    if not HISTORY:
        return "⚠️ No history", None, None
    df = get_hist()
    csv_path = "history.csv"
    img_path = "history.png"
    df.to_csv(csv_path, index=False)

    # Generate table image
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axis("off")
    tbl = ax.table(cellText=df.values, colLabels=df.columns, loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1.2, 1.2)
    plt.savefig(img_path, bbox_inches="tight", dpi=150)
    plt.close(fig)

    return f"✅ Files ready ({len(df)} rows)", csv_path, img_path

# ========== Dark CSS ==========
CSS = """
body { background-color: #0f172a; color: #e5e7eb; }
.gradio-container { font-family: 'Inter', sans-serif; }
.card { background: #1e293b; border-radius: 12px; padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4); }
h1,h2,h3 { color: #10b981; }
.gr-button { border-radius:8px; padding:10px 14px; font-weight:600; }
#convert { background: #3b82f6; color: white; border:none; }
#swap { background: #10b981; color:white; border:none; }
#csv { background: #10b981; color:white; border:none; }
.gr-textbox textarea { font-size:18px; color: #e5e7eb; background:#0f172a; }
"""

# ========== Gradio UI ==========
with gr.Blocks(css=CSS, title="Dark Unit Converter") as app:
    gr.Markdown("## 🌙 Premium Dark Unit Converter", elem_classes="card")

    # Input + Result
    with gr.Column(scale=2, elem_classes="card"):
        category = gr.Dropdown(list(UNITS.keys()), label="Category", value="Length")
        f_unit = gr.Dropdown(list(UNITS["Length"].keys()), label="From", value="meter (m)")
        t_unit = gr.Dropdown(list(UNITS["Length"].keys()), label="To", value="centimeter (cm)")
        value = gr.Number(label="Value", value=1)
        with gr.Row():
            btn_convert = gr.Button("Convert", elem_id="convert")
            btn_swap = gr.Button("Swap", elem_id="swap")
        result = gr.Textbox(label="Result", interactive=False)

    # History directly under result
    with gr.Column(elem_classes="card"):
        hist = gr.Dataframe(
            value=get_hist(),
            headers=["Time","Category","From","Result"],
            label="History",
            interactive=False,
            row_count=10
        )

    # Downloads (hidden until generated)
    with gr.Row():
        with gr.Column(elem_classes="card"):
            btn_csv = gr.Button("Generate CSV + Image", elem_id="csv")
            status = gr.Textbox(label="Status", interactive=False)
            file_csv = gr.DownloadButton(label="⬇️ Download CSV", visible=False)
            file_img = gr.DownloadButton(label="⬇️ Download Image", visible=False)

    # Logic
    def update_units(cat):
        opts = list(UNITS[cat].keys())
        return (
            gr.update(choices=opts, value=opts[0]),
            gr.update(choices=opts, value=opts[1] if len(opts) > 1 else opts[0])
        )
    category.change(update_units, category, [f_unit, t_unit])

    def do_convert(c, v, fu, tu):
        res = convert_val(c, v, fu, tu)
        if res.startswith("❗"):
            return res, get_hist()
        add_hist(c, v, fu, tu, res)
        return f"{res} {tu}", get_hist()
    btn_convert.click(do_convert, [category, value, f_unit, t_unit], [result, hist])

    btn_swap.click(lambda fu, tu: (tu, fu), [f_unit, t_unit], [f_unit, t_unit])

    def do_files():
        msg, csv, img = gen_files()
        if csv and img:
            return msg, gr.update(value=csv, visible=True), gr.update(value=img, visible=True)
        else:
            return "⚠️ No history to export", gr.update(visible=False), gr.update(visible=False)

    btn_csv.click(do_files, None, [status, file_csv, file_img])

if __name__ == "__main__":
    app.launch()
