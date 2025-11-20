from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
      {"role": "developer", "content": "You are a helpful assistant."},
      {"role": "user", "content": "why is the sky blue?"},
      {"role": "assistant", "content": "The sky appears blue due to the scattering of sunlight by the atmosphere."},
      {"role": "user", "content": "explain it like I'm five years old."}
    ]
)

print(completion.choices[0].message)