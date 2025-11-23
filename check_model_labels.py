from transformers import AutoModelForSequenceClassification
import os

# 设置代理，确保可以访问Hugging Face
os.environ["http_proxy"] = "http://127.0.0.1:33210"
os.environ["https_proxy"] = "http://127.0.0.1:33210"
os.environ["all_proxy"] = "socks5://127.0.0.1:33211"

MODEL_ID = "nlpodyssey/bert-multilingual-uncased-geo-countries-headlines"
HF_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN", "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")

try:
    print(f"正在加载模型配置: {MODEL_ID}")
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID, token=HF_TOKEN)
    
    if hasattr(model.config, "id2label"):
        print("\n模型的标签 (id2label) 如下:")
        print(model.config.id2label)
    else:
        print("\n此模型配置中没有 'id2label' 映射。")
        
except Exception as e:
    print(f"\n发生错误: {e}")
