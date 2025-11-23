import os
import langdetect
# 确保导入 DebertaV2TokenizerFast，以解决 SentencePiece 转换问题
from transformers import AutoTokenizer, AutoModelForSequenceClassification, DebertaV2TokenizerFast 
import torch

# 1. 代理设置 (保留，这是通过网络连接 Hugging Face 的关键)
os.environ["http_proxy"] = "http://127.0.0.1:33210"
os.environ["https_proxy"] = "http://127.0.0.1:33210"
os.environ["all_proxy"] = "socks5://127.0.0.1:33211"

# 2. 模型设置
MODEL_ID = "MoritzLaurer/DeBERTa-v3-small-mnli-fever-docnli-ling-2c"
device = torch.device("cpu") # 强制使用 CPU

print(f"正在尝试从云端加载模型: {MODEL_ID}")
print(f"运行设备: {device}")

try:
    # 关键修正：直接使用 DebertaV2TokenizerFast 绕过 AutoTokenizer 的转换错误
    tokenizer = DebertaV2TokenizerFast.from_pretrained(MODEL_ID)
    
    # 模型主体仍然使用 AutoModelForSequenceClassification
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
    model.to(device)
    model.eval()
    print("模型加载成功！")

except Exception as e:
    print(f"\n致命错误：模型加载失败。请检查代理设置和网络连接。")
    print(f"详细错误: {e}")
    exit()


def model_question(text: str, threshold: float = 0.6) -> bool:
    """使用 NLI 模型判断文本是否为问题 (基于 Entailment 分数)。"""
    hypothesis = "This sentence is a question."

    inputs = tokenizer(
        text,
        hypothesis,
        return_tensors="pt",
        truncation=True,
        padding=True
    ).to(device)

    with torch.no_grad():
        logits = model(**inputs).logits

    probs = torch.softmax(logits, dim=1)[0]
    # Entailment 概率通常在索引 2
    entail_score = probs[2].item() 

    return entail_score >= threshold


def is_english(text: str) -> bool:
    """使用 langdetect 快速判断文本是否为英文。"""
    try:
        return langdetect.detect(text) == "en"
    except:
        return False


MIN_WORDS = 6

def keep(text: str) -> bool:
    """筛选文本：必须是英文、满足最小词数，且模型判断为问句。"""
    if not is_english(text):
        return False
    if len([w for w in text.split() if w.isalpha()]) < MIN_WORDS:
        return False
    return model_question(text)


def process_file(in_path, out_path):
    """处理单个文件，筛选问句并保存。"""
    if os.path.exists(out_path):
        print(f"{os.path.basename(in_path)} 已存在，跳过")
        return

    kept = []
    try:
        with open(in_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            total_lines = len(lines)
            
            print(f"正在处理 {os.path.basename(in_path)} - 共 {total_lines} 行...")
            
            for i, line in enumerate(lines):
                text = line.strip()
                if text and keep(text):
                    kept.append(text)
                
                # 打印进度，防止 CPU 运行时用户以为程序卡死
                if (i + 1) % 100 == 0:
                    print(f"  已处理 {i + 1}/{total_lines} 行...", end="\r")
            
            print(f"  处理完成。")

    except Exception as e:
        print(f"读取文件出错 {in_path}: {e}")
        return

    if not kept:
        print(f"{os.path.basename(in_path)} 无有效问句")
        return

    with open(out_path, "w", encoding="utf-8") as out:
        out.write("\n".join(kept))

    print(f"✔ 保存 {len(kept)} 条问句 → {out_path}")


def main():
    """主函数，遍历输入目录并处理文件。"""
    INPUT_DIR = "video_comment/"
    OUTPUT_DIR = "video_comment_transformer/"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(INPUT_DIR):
        print(f"错误：找不到输入文件夹 '{INPUT_DIR}'")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    print(f"发现 {len(files)} 个文件待处理...")

    for fname in files:
        process_file(
            os.path.join(INPUT_DIR, fname),
            os.path.join(OUTPUT_DIR, fname)
        )

    print("\n所有文件处理完成！")


if __name__ == "__main__":
    main()