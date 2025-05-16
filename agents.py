import os
from dotenv import load_dotenv
from groq import Groq

# Загружаем переменные из .env файла
load_dotenv()

# Получаем API-ключ из переменной окружения
api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

# Выполняем запрос
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": "Расскажи стих",
        }
    ]
)

# Печатаем ответ
print(response.choices[0].message.content)
