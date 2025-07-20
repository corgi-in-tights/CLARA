import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

app = FastAPI()

# model + tokenizer load 
model_path = "./intent_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.eval()


with open(f"{model_path}/label2id.json", "r") as f:
    label2id = json.load(f)
id2label = {v: k for k, v in label2id.items()}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ WebSocket connected")

    try:
        while True:
            text = await websocket.receive_text()

            # Tokenize and predict
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                logits = model(**inputs).logits
                pred_id = torch.argmax(logits, dim=1).item()

            response = id2label[pred_id]

            await websocket.send_text(response)

    except WebSocketDisconnect:
        print("❌ WebSocket disconnected")
        