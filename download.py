import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_ID = "nlpodyssey/bert-multilingual-uncased-geo-countries-headlines"
HF_TOKEN = "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"  # 建议改为放环境变量
# 若需安全: HF_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN", HF_TOKEN)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=HF_TOKEN)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, token=HF_TOKEN)

def classify(texts):
    if isinstance(texts, str):
        texts = [texts]
    enc = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    outputs = model(**enc)
    probs = outputs.logits.softmax(dim=-1)
    return probs.detach().cpu().tolist()

if __name__ == "__main__":
    samples = [
        "Where is Germany?",
        "This video is amazing",
    ]
    print(classify(samples))