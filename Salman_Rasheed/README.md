Assignment-1 - day-2- 03-02-2025

!pip install -q transformers sentencepiece torch gradio

import torch
import gradio as gr
import tempfile
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ---------------- MODEL ----------------
model_name = "google/flan-t5-small"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# ------------- SUMMARIZATION -------------
def summarize_text(input_text, max_tokens):
    if not input_text.strip():
        return "Please enter text."

    prompt = (
        "Summarize the following text clearly and concisely. "
        "Focus only on key information.\n\n" + input_text
    )

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=int(max_tokens),
            min_length=30,
            num_beams=4,
            length_penalty=2.0,
            repetition_penalty=1.5,
            no_repeat_ngram_size=3,
            early_stopping=True
        )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# ------------- EXPORT FILE -------------
def export_summary(summary_text):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8")
    temp_file.write(summary_text)
    temp_file.close()
    return temp_file.name

# ------------- THEME BLENDING -------------
def blend(a, b, t):
    return int(a + (b - a) * t)

def generate_css(percent):
    t = percent / 100.0
    bg = f"rgb({blend(255,40,t)}, {blend(255,45,t)}, {blend(255,55,t)})"
    text = f"rgb({blend(0,230,t)}, {blend(0,230,t)}, {blend(0,230,t)})"
    box = f"rgb({blend(245,70,t)}, {blend(245,75,t)}, {blend(245,85,t)})"

    return f"""
    <style>
    .gradio-container {{
        background: {bg} !important;
        color: {text} !important;
    }}
    textarea, input {{
        background: {box} !important;
        color: {text} !important;
        font-size: 14px !important;
    }}
    </style>
    """

# ---------------- UI ----------------
with gr.Blocks(title="AI Text Summarizer") as demo:
    gr.Markdown("## 📝 AI Text Summarizer")

    theme_slider = gr.Slider(0, 100, value=0, label="Theme (Light → Dark)")
    style_block = gr.HTML(generate_css(0))

    input_text = gr.Textbox(label="Input Text", lines=8)
    max_tokens = gr.Slider(64, 256, value=120, step=16, label="Summary Length")

    summarize_btn = gr.Button("Summarize")
    summary_output = gr.Textbox(label="Summary", lines=5, show_copy_button=True)

    download_btn = gr.Button("Download Summary as .txt")
    file_output = gr.File()

    summarize_btn.click(summarize_text, [input_text, max_tokens], summary_output)
    download_btn.click(export_summary, summary_output, file_output)

    theme_slider.change(lambda v: generate_css(v), theme_slider, style_block)

demo.launch()
