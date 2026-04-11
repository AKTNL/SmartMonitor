from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是操作系统领域大神"),
    ("human", "{text}")
])

model = ChatOllama(model="qwen2.5:7b-instruct")

chain = prompt | model

result = chain.invoke({"text": "你好"})
print(result.content)
