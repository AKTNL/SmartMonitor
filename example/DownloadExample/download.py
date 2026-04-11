from transformers import AutoTokenizer, AutoModel
import os

# 创建模型缓存目录
cache_dir = "./model_cache"
os.makedirs(cache_dir, exist_ok=True)

# 下载模型和tokenizer到指定目录
model_name = "BAAI/bge-small-zh-v1.5"
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
model = AutoModel.from_pretrained(model_name, cache_dir=cache_dir)

print(f"模型已下载到: {cache_dir}")
