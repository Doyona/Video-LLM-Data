import os
import torch
import langdetect
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_ID = "nlpodyssey/bert-multilingual-uncased-geo-countries-headlines"
HF_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN", "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")  # 建议改为仅用环境变量

input_folder = "sample/"
output_folder = "sample_out/"

# 创建输出目录
os.makedirs(output_folder, exist_ok=True)

# 载入远程模型 (自动下载缓存)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=HF_TOKEN)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, token=HF_TOKEN)
model.eval()

QUESTION_WORDS = {"who","what","when","where","why","how","which","whom","whose"}
QUESTION_PATTERNS = ["i wonder", "could you", "can you", "can anyone", "does anyone", "any idea", "do you know", "can someone"]

def heuristic_is_question(text: str) -> bool:
    t = text.strip().lower()
    if not t:
        return False
    if t.endswith("?"):
        return True
    first = t.split(maxsplit=1)[0]
    if first in QUESTION_WORDS:
        return True
    for p in QUESTION_PATTERNS:
        if t.startswith(p):
            return True
    # 中间有问号也算
    if "?" in t:
        return True
    return False

def is_english(text):
    try:
        return langdetect.detect(text) == "en"
    except:
        return False

for filename in os.listdir(input_folder):
    input_path = os.path.join(input_folder, filename)
    # 跳过不是文件的路径
    if not os.path.isfile(input_path):
        continue
    output_path = os.path.join(output_folder, filename)
    # 新增：如果输出文件已存在则跳过
    if os.path.exists(output_path):
        print(f"{filename}: 输出文件已存在，跳过")
        continue
    question_sentences = []

    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            if not is_english(text):
                continue
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
            with torch.no_grad():
                logits = model(**inputs).logits
            pred = torch.argmax(logits, dim=1).item()
            label_map = getattr(model.config, "id2label", None)
            label_text = "" if not label_map else (label_map.get(pred, "") if isinstance(label_map, dict) else "")
            # 放宽：模型标签里含 question / 询问词启发式 任一满足即可
            if "question" in label_text.lower() or heuristic_is_question(text):
                question_sentences.append(text)
    # 新增：如果无问句则不创建文件
    if not question_sentences:
        print(f"{filename}: 无英文问句，跳过创建文件")
        continue
    with open(output_path, "w", encoding="utf-8") as out:
        for q in question_sentences:
            out.write(q + "\n")
    print(f"{filename}: 找到 {len(question_sentences)} 个英文问句 → 已保存到 {output_path}")

print("全部处理完成！")