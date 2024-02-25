
import json
import subprocess
from pathlib import Path
from threading import Thread

from openai import OpenAI

from lib.presentation import Presentation
from lib.prompts import generate_prompts
from lib.openai_access import openai_request
from lib.markdown import parse_md_outline
from lib.google_images import google_image_search, preprocess_query
from lib.pptx_factory import make_pptx
from lib.utils import *
from lib.config import *


def generate_presentations(speaker_names: list[str],
                           topic_pool: list[str],
                           language: str,
                           images: bool = True,
                           launch: bool = False):
    openai_client = OpenAI()

    random.shuffle(speaker_names)

    print("Generating prompts ...")
    presentations: list[Presentation]
    presentations = generate_prompts(openai_client,
                                     speaker_names=speaker_names,
                                     topic_pool=topic_pool,
                                     language=language)

    for i, presentation in enumerate(presentations):
        
        print(f"Presentation #{i+1} ({presentation.speaker}): Accessing OpenAI ...")
        # OpenAI request
        presentation.markdown = openai_request(openai_client, presentation.prompt)

        # Parse markdown
        _topic, contents = parse_md_outline(presentation.markdown)

        # Image search
        presentation.images = []
        if images:
            for i, slide in enumerate(contents):
                query = preprocess_query(f"{presentation.topic} {slide['title']}", language)
                imgs, res, parameters = google_image_search(query=query, imgSize=None, safe="active", num_downloads=1)
                
                if "error" in res and res["error"]["code"] == 429:
                    print("Quota for google search exceeded. Disabling image search.")
                    break
                if not imgs:
                    # No search results, slide stays without image
                    continue
                img = imgs[0]
                slide["img"] = img
                presentation.images.append({
                    "slide": i + 1,
                    "image": img,
                    "search": {
                        "query": query,
                        "parameters": parameters,
                        "results": res
                    },
                    "all_images": imgs
                })

        # Generate pptx file
        pptx_path = make_pptx(pptx=PPTX_TEMPLATE_DIR / "template-white-16-9.pptx",
                              topic=presentation.topic,
                              speaker=presentation.speaker,
                              contents=contents)
        presentation.pptx_path = pptx_path
        print(f"Saved .pptx file to {pptx_path}.")

        # When first presentation is ready, start slideshows in separate thread.
        # This way, the remaining presentations are generated in the background.
        if launch and i == 0:
            launch_thread = Thread(target=launch_presentations, args=(presentations))
            launch_thread.run()
    


