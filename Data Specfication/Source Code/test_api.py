import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

raw_key = os.getenv("OPENAI_API_KEY", "")
key = raw_key.strip().strip('"').strip("'")

print(f"Key detected: {bool(key)}")
print(f"Key prefix: {key[:15]}... (Length: {len(key)})")

try:
    client = OpenAI(api_key=key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Reply with 'API is working 100%'"}],
        max_tokens=20
    )
    print("\n[RESULT]: SUCCESS!")
    print("AI Response:", response.choices[0].message.content)
except Exception as e:
    print("\n[RESULT]: FAILED!")
    print("Error Details:", str(e))
