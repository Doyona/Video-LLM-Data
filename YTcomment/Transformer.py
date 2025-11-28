import os
import torch
import langdetect
from transformers import pipeline  # 1. 导入 pipeline

# 2. 设置代理 (如果需要)
os.environ["http_proxy"] = "http://127.0.0.1:33210"
os.environ["https_proxy"] = "http://127.0.0.1:33210"
os.environ["all_proxy"] = "socks5://127.0.0.1:33211"

# 3. 使用更合适的零样本分类模型
MODEL_ID = "facebook/bart-large-mnli"
# HF_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN", "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") # pipeline不需要token

input_folder = "YTcomment/video_comment/"
output_folder = "YTcomment/video_comment_transformer/"

# 创建输出目录
os.makedirs(output_folder, exist_ok=True)

# GPU 设置
USE_GPU = torch.cuda.is_available()
if USE_GPU:
    print(f"检测到 GPU: {torch.cuda.get_device_name(0)}")
else:
    print("未检测到 GPU，使用 CPU")

# 4. 载入零样本分类 pipeline (使用 GPU / float16 加速)
print(f"正在加载模型: {MODEL_ID}...")
try:
    classifier = pipeline(
        "zero-shot-classification",
        model=MODEL_ID,
        device=0 if USE_GPU else -1,
        torch_dtype=torch.float16 if USE_GPU else torch.float32
    )
    print("模型加载成功！")
except Exception as e:
    print(f"模型加载失败: {e}")
    print("回退 CPU 加载...")
    classifier = pipeline("zero-shot-classification", model=MODEL_ID)
    print("模型已在 CPU 上加载。")

BATCH_SIZE = 16  # 批量推理大小

# 移除启发式规则，只使用分类器

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
        # 5. 批量处理以提高效率
        lines = [line.strip() for line in f if line.strip() and is_english(line.strip())]
        
        if not lines:
            print(f"{filename}: 无有效英文评论，跳过")
            continue

        print(f"正在处理 {filename} 中的 {len(lines)} 条英文评论...")
        
        # 使用 pipeline 进行批量预测
        candidate_labels = ["question", "statement"]
        results = classifier(lines, candidate_labels, multi_label=False, batch_size=BATCH_SIZE)

        for i, text in enumerate(lines):
            model_is_question = results[i]['labels'][0] == 'question' and results[i]['scores'][0] > 0.8 # 设置一个置信度阈值
            
            # 只使用分类器判断
            if model_is_question:
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