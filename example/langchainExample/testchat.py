from langchain_ollama import ChatOllama

llm = ChatOllama(model="qwen2.5:7b-instruct")

result = llm.invoke([("human", "你好")])
print(result.content)
