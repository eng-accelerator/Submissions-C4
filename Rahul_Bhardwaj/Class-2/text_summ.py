import gradio as gr
from transformers import T5Tokenizer, T5ForConditionalGeneration

# Load T5 model directly
try:
    model_name = "t5-small"
    tokenizer = T5Tokenizer.from_pretrained(model_name)
    model = T5ForConditionalGeneration.from_pretrained(model_name)
    MODEL_LOADED = True
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error: {e}")
    MODEL_LOADED = False

def summarize_text(text, max_len=130):
    if not MODEL_LOADED:
        return "Error: Model not loaded"
    if not text.strip():
        return "Please enter text"
    try:
        input_text = "summarize: " + text
        inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)
        outputs = model.generate(inputs, max_length=max_len, min_length=30, length_penalty=2.0, num_beams=4)
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return summary
    except Exception as e:
        return f"Error: {e}"

def export_summary(original, summary):
    if not summary.strip():
        return "No summary to export"
    filename = "summary.txt"
    with open(filename, 'w') as f:
        f.write(f"ORIGINAL:\n{original}\n\nSUMMARY:\n{summary}")
    return f"Saved to {filename}"

# Custom CSS for theme toggle
css = """
.dark-theme {
    background: #0b0f19 !important;
    color: #ffffff !important;
}
"""

with gr.Blocks(css=css) as demo:
    gr.Markdown("# 📝 Text Summarization")
    
    # Theme toggle
    theme_btn = gr.Button("🌙 Toggle Theme", size="sm")
    
    with gr.Row():
        input_box = gr.Textbox(label="Input Text", lines=8, placeholder="Enter text to summarize...")
        output_box = gr.Textbox(label="Summary", lines=8)
    
    max_length = gr.Slider(50, 200, value=130, label="Max Summary Length")
    
    with gr.Row():
        summarize_btn = gr.Button("Summarize", variant="primary")
        export_btn = gr.Button("Export")
    
    status = gr.Textbox(label="Status", interactive=False)
    
    summarize_btn.click(summarize_text, [input_box, max_length], output_box)
    export_btn.click(export_summary, [input_box, output_box], status)
    
    # Better theme toggle JS
    theme_btn.click(
        None, 
        None, 
        None,
        js="""
        function() {
            const body = document.body;
            const app = document.querySelector('gradio-app');
            if (app) {
                if (body.classList.contains('dark')) {
                    body.classList.remove('dark');
                    body.style.colorScheme = 'light';
                    app.style.colorScheme = 'light';
                } else {
                    body.classList.add('dark');
                    body.style.colorScheme = 'dark';
                    app.style.colorScheme = 'dark';
                }
            }
            return [];
        }
        """
    )

demo.launch()

