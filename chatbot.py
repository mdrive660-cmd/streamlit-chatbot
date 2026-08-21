import os

from groq import Groq

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "capital of india ? only in 10 words maximum.",
        }
    ],
    model="groq/compound",
)

print(chat_completion.choices[0].message.content)
