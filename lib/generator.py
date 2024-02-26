
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


launch_queue = []

PPTX_TEMPLATES = []


def generate_presentations(speaker_names: list[str],
                           topic_pool: list[str],
                           language: str,
                           images: bool = True,
                           launch_first: bool = False,
                           launch_all: bool = False):
    openai_client = OpenAI()

    random.shuffle(speaker_names)

    print("Generating prompts ...")
    presentations: list[Presentation]
    presentations = generate_prompts(openai_client,
                                     speaker_names=speaker_names,
                                     topic_pool=topic_pool,
                                     language=language)
    
    print(f"Generated prompts for {len(presentations)} presentation(s).")

    for i, presentation in enumerate(presentations):
        
        print(f"Presentation #{i+1} ({presentation.speaker}): Accessing OpenAI ...")
        # OpenAI request
        presentation.markdown = openai_request(openai_client, presentation.prompt)

        # Parse markdown
        _topic, contents = parse_md_outline(presentation.markdown)

        # Image search
        presentation.images = []
        if images:
            for j, slide in enumerate(contents):
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
                    "slide": j + 1,
                    "image": img,
                    "search": {
                        "query": query,
                        "parameters": parameters,
                        "results": res
                    },
                    "all_images": imgs
                })
        
        # Select random template
        template_files = [f.name for f in os.scandir(PPTX_TEMPLATE_DIR) if f.is_file()]
        presentation.pptx_template_path = PPTX_TEMPLATE_DIR / random.choice(template_files)

        # Generate pptx file
        pptx_path = make_pptx(pptx=presentation.pptx_template_path,
                              topic=presentation.topic,
                              speaker=presentation.speaker,
                              contents=contents)
        presentation.pptx_path = pptx_path
        print(f"Saved .pptx file to {pptx_path}.")

        launch_queue.append(presentation)

        # When first presentation is ready, start slideshows in separate thread.
        # This way, the remaining presentations are generated in the background.
        if i == 0 and (launch_first or launch_all):
            launch_thread = Thread(target=launch_presentations, kwargs={
                "presentations": presentations,
                "launch_all": launch_all
            })
            launch_thread.start()
    

def launch_presentations(presentations: list[Presentation], launch_all: bool):
    ppt_exe = Path(os.environ.get('POWERPOINT_EXE_PATH'))

    for i, presentation in enumerate(presentations):
        # Launch slideshow in PowerPoint app
        assert presentation.pptx_path is not None, f"Presentation #{i + 1} ({presentation.speaker}) cannot be launched."
        cmd = f"{ppt_exe} /s \"{presentation.pptx_path}\""
        print(f"Launching presentation #{i + 1} (Speaker: {presentation.speaker}) ...")
        subprocess.run((cmd))

        if not launch_all:
            break


