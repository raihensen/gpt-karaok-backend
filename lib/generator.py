
import json
import math
import subprocess
from pathlib import Path
from threading import Thread

from openai import OpenAI
import requests
from tqdm import tqdm

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


def generate_presentations(player_names: list[str],
                           language: str,
                           players: list[dict] = None,  # Player data as received from API
                           topic_pool: list[str] = None,  # One pool for all topics (incl. wrong ones)
                           topic_groups: list[list[str]] = None,  # Groups of three to assign to random players. Don't assign to the author (index based)
                           images: bool = True,
                           launch_first: bool = False,
                           launch_all: bool = False):
    openai_client = OpenAI()

    print("Assigning topics ...")
    presentations = assign_topics(player_names=player_names, players=players, topic_pool=topic_pool, topic_groups=topic_groups)
    # for p in presentations:
    #     print(p.player)
    # print([p.player.get("isSpeaker", None) for p in presentations])
    # return
    if players:
        presentations = [p for p in presentations if p.player.get("isSpeaker", True)]

    print("Generating prompts ...")
    generate_prompts(presentations=presentations,
                     language=language)
    
    print(f"Generated prompts for {len(presentations)} presentation(s).")

    if players:
        print(f"Accessing OpenAI for speaker instructions ...")
        num_instructions_per_player = 3  # including one hard-coded
        k = num_instructions_per_player - 1
        num_instructions = math.ceil((k + 0.5) * len(presentations))
        INSTRUCTION_PROMPT = {
            "de": f'Wir spielen Powerpoint-Karaoke, d.h. der Vortragende hat die Folien noch nie gesehen. Ich suche kreative Ideen für Anweisungen an den Vortragenden bzgl. Vortragsstil oder überraschenden Aktionen während des Vortrags. Bitte gib {num_instructions} Ideen für solche Anweisungen. Antworte ausschließlich in Form einer JSON-Liste.'
        }
        OR = {"de": "ODER", "en": "OR"}
        instruction_pool = json.loads(openai_request(openai_client, INSTRUCTION_PROMPT[language], save_chat=True, name="instructions"))
        print(type(instruction_pool), instruction_pool)
        if isinstance(instruction_pool, dict):
            print("Converting response from dict to list ...")
            instruction_pool = list(instruction_pool.values())
        instruction_pool = random.sample(list(instruction_pool), k * len(presentations))

        # Send speaker instructions to API
        print("Sending speaker instructions ...")
        for i, (player, presentation) in tqdm(enumerate(zip(players, presentations))):
            player_instruction_choice = instruction_pool[i * k:(i + 1) * k]
            player_instruction_choice += [presentation.speaker_instruction] if presentation.speaker_instruction else []
            presentation.speaker_instruction = f" [{OR[language]}] ".join(player_instruction_choice)
            url = f"{os.getenv('FRONTEND_URL')}/api/session/{player['sessionId']}/player/{player['id']}/setStyleInstruction"
            res = requests.post(url, data={"styleInstruction": presentation.speaker_instruction} if presentation.speaker_instruction else {})
            if not res.ok:
                res_data = res.json()
                if "error" in res_data:
                    print(f"Error {res.status_code}: {res_data['error']['message']}")
    else:
        print("Speaker style instructions are disbaled without API access.")
    
    # for p in presentations:
    #     print(p.speaker, p.topic)
    #     print("Instructions: {p.speaker_instruction}")
    #     print("-----\n" + p.prompt + "-----\n")
    #     print()
        
    # Sample random template
    template_files = [f.name for f in os.scandir(PPTX_TEMPLATE_DIR) if f.is_file()]
    templates = sample_minimal_repitions(template_files, len(presentations))
    for template, presentation in zip(templates, presentations):
        presentation.pptx_template_path = PPTX_TEMPLATE_DIR / template

    for i, presentation in enumerate(presentations):
        
        print(f"Presentation #{i+1} ({presentation.speaker}): Accessing OpenAI ...")
        # OpenAI request
        presentation.markdown = openai_request(openai_client, presentation.prompt, save_chat=True, name="presentation")

        # Parse markdown
        _topic, contents = parse_md_outline(presentation.markdown)

        # Image search
        presentation.images = []
        if images:
            print("Accessing google images and downloading images ...")
            for j, slide in tqdm(enumerate(contents)):
                query = f"{presentation.topic} {slide['title']}"
                if presentation.image_query_suffix:
                    query += " " + presentation.image_query_suffix
                query = preprocess_query(query, language)
                imgs, res, parameters = google_image_search(query=query, imgSize=None, safe="active", num_downloads=1)
                
                if "error" in res and res["error"]["code"] == 429:
                    print("Quota for google search exceeded. Disabling image search.")
                    images = False
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

        # Generate pptx file
        pptx_path = make_pptx(pptx_template_path=presentation.pptx_template_path,
                              topic=presentation.topic,
                              speaker=presentation.speaker,
                              contents=contents)
        presentation.pptx_path = pptx_path
        print(f"Saved .pptx file.")
        # print(f"Saved .pptx file to {pptx_path}.")

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
    for i, presentation in enumerate(presentations):
        # Launch slideshow in PowerPoint app
        assert presentation.pptx_path is not None, f"Presentation #{i + 1} ({presentation.speaker}) cannot be launched."
        print(f"Launching presentation #{i + 1} (Speaker: {presentation.speaker}) ...")
        show_presentation_blocking(presentation.pptx_path)
        if not launch_all:
            break


def assign_topics(player_names: list[str],
                  players: list[dict] = None,
                  topic_pool: list[str] = None,  # One pool for all topics (incl. wrong ones)
                  topic_groups: list[list[str]] = None):
    
    num_presentations = len(player_names)
    num_wrong_topics = 2
        
    m = 1 + num_wrong_topics

    if topic_groups:
        if any(len(g) < m for g in topic_groups):
            raise ValueError(f"assign_topics: There are too small topic groups (need {m} topics per player)")
        # Shuffle the topic groups s.t. nobody gets their own topics.
        topic_group_sample = random_derangement(topic_groups)
        # Shuffle and limit the topics within the groups
        topic_group_sample = [random.sample(g, m) for g in topic_group_sample]

        topics = [g[0] for g in topic_group_sample]
        wrong_topicss = [g[1:] for g in topic_group_sample]
    
    elif topic_pool:
        # Shuffle the topics individually s.t. nobody gets their own topics.
        topic_sample = random_chunk_derangement(topic_pool, m)
        topics = [t for i, t in enumerate(topic_sample) if i % m == 0]
        wrong_topicss = [topic_sample[i * m + 1:(i + 1) * m] if num_wrong_topics else [] for i in range(num_presentations)]

    presentations = [Presentation(speaker=speaker,
                                  topic=topic,
                                  wrong_topics=wrong_topics) for speaker, topic, wrong_topics in zip(player_names, topics, wrong_topicss)]
    if players:
        for player, presentation in zip(players, presentations):
            presentation.player = player
            presentation.player_id = player["id"]
            presentation.session_id = player["sessionId"]
    
    # Shuffle speakers
    random.shuffle(presentations)
    return presentations


if __name__ == "__main__":
    
    # Test assign_topics()
    speakers = ["A", "B", "C", "D"]
    topic_groups = [[f"{p}{i}" for i in range(1, 4)] for p in speakers]
    topic_pool = None

    presentations = assign_topics(player_names=speakers, topic_pool=topic_pool, topic_groups=topic_groups)
    for p in presentations:
        print(p.speaker, p.topic, p.wrong_topics)
