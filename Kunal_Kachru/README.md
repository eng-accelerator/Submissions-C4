## Day 2 assignment - HuggingFace + Gradio

---
```
  https://colab.research.google.com/drive/1J2x9iJWA21HkzH_aRABvlPMhRSfbg8AW?usp=sharing
```
---

## Day 3 assignment - implement chatbot-style app using Streamlit and OpenRouter LLM

### Folder Structure
```
chatbot-app/
│
├── app.py
├── requirements.txt
├── .env
└── storage/
    └── chats.json
```
### Run steps 

```
1. Create and update the .env file with the API key
2. pip install -r requirements.txt
3. streamlit run app.py
```
---


## Day 5 class activity/assignment 
```
1. LinkedIn post generation app - https://ai.studio/apps/drive/1xGGkdzZLAgxolhe3StmapQoDbVlMdMss
2. JSON to implement the backend for this - ClassActivity_GoogleAIstudio_ui_n8n_backend.json attached above
```
---


## Day 6 and 7 class activity/assignment 
```
1. Google Drive URL - https://drive.google.com/drive/folders/1Y3FJBC39BtXbP23MfdYA0E68XqBjLB5A?usp=sharing
2. Videos showing basic and advanced rag using Gradio UI are also present at the above location.
3. All other assignments related to simple/advanced/multi- modal RAG are also present

```
---

## Day 8 class activity/assignment 

```
from transformers import AutoModelForSequenceClassification
import torch
checkpoint = "distilbert-base-uncased-finetuned-sst-2-english"
model = AutoModelForSequenceClassification.from_pretrained(checkpoint)
outputs = model(**inputs)
print("--------SHAPE OF LOGIT TENSOR--------")
print(outputs.logits.shape)
print("\n\n--------LOGIT TENSOR--------")
print(outputs.logits)
predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
predictions = torch.argmax(predictions, dim=1)
print("\n\n--------PREDICTIONS--------")
print(predictions) # os one, c++ one

print("\n\n--------SENTIMENT TO ID mapping --------")
print(model.config.id2label)
```
### console output  ###
```
Loading weights: 100%
 104/104 [00:00<00:00, 438.42it/s, Materializing param=pre_classifier.weight]
--------SHAPE OF LOGIT TENSOR--------
torch.Size([2, 2])

--------LOGIT TENSOR--------
tensor([[-4.3357,  4.6875],
        [ 4.6717, -3.7884]], grad_fn=<AddmmBackward0>)

--------PREDICTIONS--------
tensor([1, 0])

--------SENTIMENT TO ID mapping --------

{0: 'NEGATIVE', 1: 'POSITIVE'}

```
---
