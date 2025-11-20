from openai import OpenAI

def main():
    client = OpenAI()
    while True:
        try:
            user_msg = input("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        if not user_msg.strip():
            continue
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_msg}
            ]
        )
        print("Assistant:", completion.choices[0].message.content)  

if __name__ == "__main__":
    main()