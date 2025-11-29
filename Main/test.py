from transformers import AutoTokenizer, AutoModelForSequenceClassification

tokenizer = AutoTokenizer.from_pretrained("./Model", local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained("./Model", local_files_only=True)
print("模型加载成功")
