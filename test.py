import openai

# Configure client to use your wrapper
client = openai.OpenAI(
    api_key="sk-wrapper-key-1",
    base_url="http://localhost:8000/v1"
)

# Test chat completion
response = client.chat.completions.create(
    model="claude-4-sonnet",
    messages=[
        {"role": "user", "content": "siapa presiden indonesia sekarang"}
    ],
    max_tokens=200
)

print("🤖 Response:", response.choices[0].message.content)
print("📊 Tokens used:", response.usage.total_tokens)
