
import json
import uuid
from openai import OpenAI, OpenAIError

if __name__ == "__main__":
    import os, sys
    from pathlib import Path
    sys.path.append(os.getcwd())
    print(sys.path)

from lib.config import *

def openai_request(client, prompt, save_chat: bool = True):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = completion.choices[0].message.content

        if save_chat:
            path = CHATS_DIR / f"openai-chat-{NOW()}-{uuid.uuid4()}.json"
            json.dump({
                "prompt": prompt,
                "answer": answer
            }, open(path, "w", encoding="utf8"), indent=2)

        return answer
        # output = ""
        # for chunk in stream:
        #     if chunk.choices[0].delta.content is not None:
        #         print(chunk.choices[0].delta.content, end="")

    except OpenAIError as e:
        print(f"Error (status code {e.status_code}):")
        print(f'Message: "{e.message}"')


if __name__ == "__main__":
    openai_client = OpenAI()
    prompt = "Please write a romantic poem in German in the style of the 19th century that features nostalgia and grief. The poem should have 3x4 verses and crossed rhymes."
    print(openai_request(openai_client, prompt))