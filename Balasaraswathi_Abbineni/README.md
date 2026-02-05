Link for Day 2 Assignment 1: https://colab.research.google.com/drive/1jKpFdwRihN8ZRuhfbp9XLI4KZQUpgtE1

# Code here
import gradio as gr
import transformers
import torch
import tempfile
import os

# -----------------------------
# Load model + pipeline
# -----------------------------
model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"

pipeline = transformers.pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device_map="auto",
)

# -----------------------------
# Summarization function
# -----------------------------
def summarize_text(input_text, max_tokens):
    messages = [
        {
            "role": "system",
            "content": "You are an expert assistant that summarizes text clearly and concisely."
        },
        {
            "role": "user",
            "content": f"Summarize the following text:\n\n{input_text}"
        }
    ]

    outputs = pipeline(
        messages,
        max_new_tokens=max_tokens,
        temperature=0.3,
    )

    summary = outputs[0]["generated_text"][-1]["content"]
    return summary


# -----------------------------
# Export summary as .txt
# -----------------------------
def export_summary(summary_text):
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".txt",
        mode="w",
        encoding="utf-8"
    )
    temp_file.write(summary_text)
    temp_file.close()
    return temp_file.name


# -----------------------------
# Gradio UI
# -----------------------------
with gr.Blocks(title="Text Summarizer (LLaMA 3.1)") as demo:
    gr.Markdown("## 📝 LLaMA-3.1 Text Summarizer")
    gr.Markdown("Paste your text, generate a summary, and export it as a `.txt` file.")

    with gr.Row():
        input_text = gr.Textbox(
            label="Input Text",
            placeholder="Paste long text here...",
            lines=12
        )

    max_tokens = gr.Slider(
        minimum=64,
        maximum=512,
        value=256,
        step=32,
        label="Max Summary Tokens"
    )

    summarize_btn = gr.Button("Summarize")

    summary_output = gr.Textbox(
        label="Summary",
        lines=8
    )

    download_btn = gr.Button("Download Summary as .txt")
    file_output = gr.File(label="Download File")

    summarize_btn.click(
        fn=summarize_text,
        inputs=[input_text, max_tokens],
        outputs=summary_output
    )

    download_btn.click(
        fn=export_summary,
        inputs=summary_output,
        outputs=file_output
    )

demo.launch()
