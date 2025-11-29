import os
import torch
import langdetect
import socks
import socket
from transformers import pipeline
from pathlib import Path

# ================================
# SOCKS5 代理设置
# ================================
SOCKS_HOST = "127.0.0.1"
SOCKS_PORT = 7897

# patch 全局 socket
socks.set_default_proxy(socks.SOCKS5, SOCKS_HOST, SOCKS_PORT)
socket.socket = socks.socksocket

# ================================
# 文件夹配置
# ================================
MODEL_ID = "facebook/bart-large-mnli"
input_folder = Path("./Video_comment/")
output_folder = Path("./Video_comment_transformer/")
output_folder.mkdir(exist_ok=True)

# ================================
# Device 兼容 Mac M1/M2
# ================================
if torch.backends.mps.is_available():
    device = "mps"
elif torch.cuda.is_available():
    device = 0
else:
    device = -1

print(f"正在加载模型: {MODEL_ID} ...")
classifier = pipeline("zero-shot-classification", model=MODEL_ID, device=device)
print("模型加载成功！")

# ================================
# 英文检测
# ================================
def is_english(text):
    try:
        return langdetect.detect(text) == "en"
    except:
        return False

# ================================
# 批量处理
# ================================
for input_path in input_folder.iterdir():
    if not input_path.is_file():
        continue
    output_path = output_folder / input_path.name
    if output_path.exists():
        print(f"{input_path.name}: 输出文件已存在，跳过")
        continue

    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f if line.strip() and is_english(line.strip())]

    if not lines:
        print(f"{input_path.name}: 无有效英文评论，跳过")
        continue

    print(f"正在处理 {input_path.name} 中的 {len(lines)} 条英文评论...")
    question_sentences = []

    batch_size = 32
    candidate_labels = ["question", "statement"]

    for i in range(0, len(lines), batch_size):
        batch = lines[i:i+batch_size]
        results = classifier(batch, candidate_labels, multi_label=False)
        for j, text in enumerate(batch):
            if results[j]['labels'][0] == 'question' and results[j]['scores'][0] > 0.8:
                question_sentences.append(text)

    if question_sentences:
        with open(output_path, "w", encoding="utf-8") as out:
            for q in question_sentences:
                out.write(q + "\n")
        print(f"{input_path.name}: 找到 {len(question_sentences)} 个英文问句 → 已保存")
    else:
        print(f"{input_path.name}: 无英文问句，跳过创建文件")

print("全部处理完成！")
