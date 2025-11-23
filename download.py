import os
# 如果没有安装 huggingface_hub，请先运行: pip install huggingface_hub
from huggingface_hub import snapshot_download

# 1. 设置国内镜像环境变量 (确保下载顺畅)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 2. 设置下载参数
# 目标模型 ID
repo_id = "MoritzLaurer/DeBERTa-v3-small-mnli-fever-docnli-ling-2c"
# 目标本地路径
local_dir = "./model_local/DeBERTa-v3-ling-2c" 

print(f"正在从镜像站重新下载/修复模型文件 {repo_id} ...")
print(f"目标保存路径: {local_dir}")

try:
    # 3. 开始下载，使用 resume_download 确保续传和修复缺失文件
    snapshot_download(
        repo_id=repo_id,
        local_dir=local_dir,
        local_dir_use_symlinks=False,  
        resume_download=True,
        max_workers=8 # 提高下载速度
    )
    print("-------------------------------------------------")
    print("✅ 模型文件下载/修复完成！")
    
    # 最终检查 tokenizer.model 文件
    tokenizer_model_path = os.path.join(local_dir, "tokenizer.model")
    if os.path.exists(tokenizer_model_path):
        print(f"✅ 关键文件 'tokenizer.model' 已成功找到: {tokenizer_model_path}")
    else:
        print(f"❌ 警告：'tokenizer.model' 仍未找到！请检查网络或权限。")
        
except Exception as e:
    print(f"下载过程中发生错误: {e}")