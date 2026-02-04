import gradio as gr
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
# 1. Manually Load Model and Tokenizer 
# This bypasses the 'pipeline' command which was causing the KeyError on your machine.
models = ['sshleifer/distilbart-cnn-12-6', 'facebook/bart-large-cnn', 
          'csebuetnlp/mT5_multilingual_XLSum', 'Falconsai/text_summarization', 'google/pegasus-xsum']

lengths = ['100', '90', '80', '70', '60', '50', '40', '30', '20', '10']

# 2. Function to handle summarization and CSV export
def summarize_and_export(text, model_name, summary_length):
    try:
        print("Loading model and tokenizer... This may take a moment.")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        print("Success: Model loaded!")
    except Exception as e:
        print(f"Failed to load model: {e}")

    if not text or len(text.strip()) < 10:
        return "Please enter at least 10 characters to summarize.", None
    
    try:
        # Tokenize the input text
        inputs = tokenizer(text, max_length=1024, truncation=True, return_tensors="pt")
        
        # Generate summary using the model directly
        summary_ids = model.generate(
            inputs["input_ids"], 
            max_length=int(summary_length), 
            min_length=30, 
            length_penalty=2.0, 
            num_beams=4, 
            early_stopping=True
        )
        
        # Convert tokens back to readable text
        summary_text = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        # Export to txt
        export_file = "summary_data.txt"
        df = pd.DataFrame([{"Original": text, "Summary": summary_text}])
        df.to_string(export_file, index=False)
        
        return summary_text, export_file
    
        # Function that does something with the selected model
        def select_model(model_name):
            return f"You selected {model_name}"
    
    except Exception as e:
        return f"Processing Error: {str(e)}", None
    
# 3. Create the UI with gr.Blocks
# with gr.Blocks(title="AI Summarizer") as demo:
with gr.Blocks(theme=gr.themes.Ocean()) as app:
    gr.Markdown("# 📝 AI Text Summarizer (Task-Independent Version)")
    gr.Markdown("This version uses manual loading to avoid errors with the 'summarization' task registry.")

    # Simple Theme Toggle via JavaScript
    toggle_btn = gr.Button("🌓 Switch Dark/Light Mode")
    toggle_btn.click(None, None, None, js="() => document.body.classList.toggle('dark')")

    # ✅ Model Selection Dropdown
    model_dropdown = gr.Dropdown(
        choices=models,
        value=models[0],  # default selection
        label="Select Model"
    )
    max_len_dropdown = gr.Dropdown(
        choices=lengths,
        value=lengths[0],  # default selection
        label="Select Max Length"
    )

    with gr.Row():
        with gr.Column():
            input_box = gr.Textbox(label="Paste Text Here", lines=10)
            submit_btn = gr.Button("Summarize & Export", variant="primary")
        
        with gr.Column():
            output_box = gr.Textbox(label="AI Summary", lines=8)
            file_output = gr.File(label="Download result as a text file")
    # Connect the UI to the function
    submit_btn.click(
        fn=summarize_and_export,
        inputs=[input_box, model_dropdown, max_len_dropdown],
        outputs=[output_box, file_output]
    )
if __name__ == "__main__":
    app.launch(share=True)

