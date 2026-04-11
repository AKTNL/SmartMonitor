import os
from openai import OpenAI

client = OpenAI(api_key='sk-4d81230dca394b809bad033affbb2014', base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "你好"},
    ],
    stream=False
)

print(response.choices[0].message.content)