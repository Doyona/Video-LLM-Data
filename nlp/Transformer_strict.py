import os
import torch
import langdetect
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 放宽筛选：移除 strict_question 与双重条件，仅需模型预测为 question 或简单启发式
MODEL_ID = "nlpodyssey/bert-multilingual-uncased-geo-countries-headlines"
HF_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN", "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")  # 建议用环境变量

INPUT_DIR = "video_comment_NLP/"  # 可以换成原始目录
OUTPUT_DIR = "comment_transformer_strict/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=HF_TOKEN)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, token=HF_TOKEN)
model.eval()

QUESTION_WORDS = {"who","what","when","where","why","how","which","whom","whose"}
QUESTION_PATTERNS = ["i wonder", "could you", "can you", "can anyone", "does anyone", "any idea", "do you know", "can someone"]

def is_english(text: str) -> bool:
    try:
        return langdetect.detect(text) == "en"
    except:
        return False

def heuristic_question(text: str) -> bool:
    t = text.strip().lower()
    if not t:
        return False
    if t.endswith('?') or '?' in t:
        return True
    first = t.split(maxsplit=1)[0]
    if first in QUESTION_WORDS:
        return True
    for p in QUESTION_PATTERNS:
        if t.startswith(p):
            return True
    return False

def model_question(text: str) -> bool:
    # 使用模型 logits 判断（假设 label 名里含 question 才算）
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    pred = torch.argmax(logits, dim=1).item()
    id2label = getattr(model.config, "id2label", {})
    label = id2label.get(pred, "").lower()
    return "question" in label

def keep(text: str) -> bool:
    if not is_english(text):
        return False
    # 放宽：模型或启发式任一判定为问句即可
    return model_question(text) or heuristic_question(text)

def process_file(in_path: str, out_path: str):
    if os.path.exists(out_path):
        print(f"{os.path.basename(in_path)} 已存在，跳过")
        return
    kept = []
    with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            if keep(text):
                kept.append(text)
    if not kept:
        print(f"{os.path.basename(in_path)} 无问句，未创建文件")
        return
    with open(out_path, "w", encoding="utf-8") as out:
        for k in kept:
            out.write(k + "\n")
    print(f"{os.path.basename(in_path)} 保存 {len(kept)} 条问句 → {out_path}")

def main():
    if not os.path.isdir(INPUT_DIR):
        print(f"输入目录不存在: {INPUT_DIR}")
        return
    for fname in os.listdir(INPUT_DIR):
        if not fname.endswith('.txt'):
            continue
        in_path = os.path.join(INPUT_DIR, fname)
        if not os.path.isfile(in_path):
            continue
        out_path = os.path.join(OUTPUT_DIR, fname)
        process_file(in_path, out_path)
    print("完成严格筛选。")

if __name__ == '__main__':
    main()
