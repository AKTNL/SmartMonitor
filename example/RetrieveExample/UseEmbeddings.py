import torch
import json
from transformers import AutoTokenizer, AutoModel
import torch.nn.functional as F

# 加载模型（用于句子编码）
tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-zh-v1.5")
model = AutoModel.from_pretrained("BAAI/bge-small-zh-v1.5")

def encode(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    emb = outputs.last_hidden_state.mean(dim=1)
    return F.normalize(emb, p=2, dim=1)  # shape (1,dim)

# 加载预计算关键词 embedding
KEYWORD_EMBEDS = torch.load("../../keyword_embeds.pt")     # shape (N, dim)

with open("../../keyword_index.json", "r", encoding="utf-8") as f:
    KEYWORD_INDEX = json.load(f)


def find_best_keyword_fast(sentence):
    sent_emb = encode(sentence)  # (1,dim)

    # (1,dim) @ (dim,N) -> (1,N)
    scores = (sent_emb @ KEYWORD_EMBEDS.T).squeeze(0)

    best_idx = torch.argmax(scores).item()
    best_score = scores[best_idx].item()

    best_item = KEYWORD_INDEX[best_idx]
    return best_item["category"], best_item["word"], best_score

sentence = "大文件路径与字节数"

cat, word, score = find_best_keyword_fast(sentence)

print("类别:", cat)
print("命中关键词:", word)
print("相似度:", score)
