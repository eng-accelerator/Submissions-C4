import gradio as gr
from transformers import  AutoTokenizer, AutoModelForSeq2SeqLM
import tempfile


# Initialize the summarization pipeline once to avoid reloading it on every call.


#summarizer = pipeline("summarization", model="Falconsai/text_summarization")

tokenizer = AutoTokenizer.from_pretrained("suriya7/bart-finetuned-text-summarization")
model = AutoModelForSeq2SeqLM.from_pretrained("suriya7/bart-finetuned-text-summarization")



def summarize(text: str) -> str:
    inputs = tokenizer([text], max_length=1024, return_tensors='pt', truncation=True)
    summary_ids = model.generate(inputs['input_ids'], max_new_tokens=100, do_sample=False)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def export_summary(summary_text: str) -> str:
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".txt",
        mode="w",
        encoding="utf-8"
    )
    temp_file.write(summary_text)
    temp_file.close()
    return temp_file.name
  

with gr.Blocks() as demo:
     gr.Markdown("# Outskill Assignment Test Summarizer")
     gr.Markdown("Paste the text you want to summarize below. Also export the summary to a text file.")
     
     with gr.Row():
         with gr.Column():
             input_text = gr.Textbox(lines=10, placeholder="Add text to summarize", label="Input Text")
             summarize_button = gr.Button("Summarize")
             export_button = gr.Button("Export Summary")
             file_output = gr.File(label="Download File")
         with gr.Column():
             output_text = gr.Textbox(label="Summary")
     
     summarize_button.click(fn=summarize, inputs=input_text, outputs=output_text)
     export_button.click(fn=export_summary, inputs=output_text, outputs=file_output)

""" demo = gr.Interface(
    fn=summarize,
    inputs=gr.Textbox(lines=10, placeholder="Add text to summarize", label="Input Text"),
    outputs=gr.Textbox(label="Summary"),
    title="Gist Summarizer",
    description="Summarize long text using a Hugging Face summarization pipeline."
) """

demo.launch(share=True)





