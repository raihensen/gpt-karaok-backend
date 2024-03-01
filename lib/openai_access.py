
from dataclasses import dataclass
import json
import uuid
import base64
from openai import OpenAI, OpenAIError

from lib.config import *

def openai_request(client, prompt, save_chat: bool = True, name: str = None):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = completion.choices[0].message.content

        if save_chat:
            path = CHATS_DIR / f"openai-chat-{NOW()}{'-' + name if name else ''}-{uuid.uuid4()}.json"
            json.dump({
                "prompt": prompt,
                "answer": answer,
                "usage": completion.usage.dict()
            }, open(path, "w", encoding="utf8"), indent=2)

        return answer

    except OpenAIError as e:
        print(f"Error (status code {e.status_code}):")
        print(f'Message: "{e.message}"')


@dataclass
class OpenAiImage:
    width: int
    height: int
    local_path: Path


def openai_image_request(client: OpenAI, topic: str, prompt: str, save_chat: bool = True, name: str = None):
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="b64_json",
        )

        img_path = IMG_DIR / f"openai-img-{datetime.now().strftime(STRFTIME_FULL)}-{str(uuid.uuid4())[:4]}-{ESCAPE_PATH(topic)}.png"
        image_data = base64.b64decode(response.data[0].b64_json)
        with open(img_path, mode="wb") as png:
            png.write(image_data)

        if save_chat:
            path = CHATS_DIR / f"openai-chat-{NOW()}{'-' + name if name else ''}-image-{uuid.uuid4()}.json"
            json.dump({
                "prompt": prompt,
                "revised_prompt": response.data[0].revised_prompt,
                "local_path": str(img_path)
            }, open(path, "w", encoding="utf8"), indent=2)

        return OpenAiImage(local_path=img_path, width=1024, height=1024)

    except OpenAIError as e:
        print(f"Error (status code {e.status_code}):")
        print(f'Message: "{e.message}"')


if __name__ == "__main__":
    openai_client = OpenAI()
    prompt = "Please write a romantic poem in German in the style of the 19th century that features nostalgia and grief. The poem should have 3x4 verses and crossed rhymes."
    print(openai_request(openai_client, prompt))