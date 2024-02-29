

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any
import requests
import time

from lib.generator import assign_topics, generate_presentations
from lib.google_images import GoogleImage, google_image_search
from lib.markdown import parse_md_outline
from lib.pptx_factory import make_pptx
from lib.utils import *
from lib.config import *
from lib.types import *

import argparse


def backend_mainloop(session_id: str):
    if not re.match(r"^[A-Za-z0-9\-]+$", session_id):
        raise ValueError("Invalid session ID.")
    
    url = f"{os.getenv('FRONTEND_URL')}/api/session/{session_id}"

    while True:
        res = requests.get(url)
        res_data = res.json()
        if not res.ok:
            if "error" in res_data:
                print(f"Error {res.status_code}: {res_data['error']['message']}")
            raise ValueError(f"Request failed (status code {res.status_code})")
        session = res_data["session"]
        session_state = [s for s in SessionState if session["state"] == s.value][0]

        # session = {camel_case(k): v for k, v in session.items()}

        print(f"Session state: {session_state.name}")
        if session_state == SessionState.CLOSED:
            generate_from_api(session)
            break
        
        time.sleep(3)


def generate_from_api(session: dict):
    
    players = [p for p in session["players"] if p["topics"]]
    player_names = [p["name"] for p in players]
    if not player_names:
        raise ValueError(f"No players found.")

    # topics = sum([[t["name"] for t in p["topics"]] for p in players], [])
    # if not topics:
    #     raise ValueError(f"No topics found.")
    if not all(len(p["topics"]) >= 3 for p in players):
        raise ValueError(f"Not enough topics found, provide at least 3 topics per speaker.")
    
    topic_groups = [[t["name"] for t in p["topics"]] for p in players]

    generate_presentations(player_names=player_names,
                           players=players,
                           topic_groups=topic_groups,
                           images=True,
                           launch_first=True,
                           launch_all=True,
                           language="de")


if __name__ == "__main__":

    # Init communication with API
    parser = argparse.ArgumentParser("main.py")
    parser.add_argument("session_id", help="The ID of the session to be fetched via the API.", type=str)
    args = parser.parse_args()
    backend_mainloop(session_id=args.session_id)
    
    # Import topics from text file, comma-separated
    # with open(TEMPLATE_DIR / "topics" / "raimund.txt", "r", encoding="utf8") as f:
    #     topics = [t.strip() for t in f.read().strip().split(",")]
    #     print(topics)

    # Pool of random topics (GPT generated)
    # topics = json.load(open(TEMPLATE_DIR / "topics" / "topics-50-2.json"))

    # Use hard-coded list
    # topics = ["Gemüselasagne", "Ludwigshafen am Rhein", "Weltwirtschaftskrise"]
    # topics = ["Mutterschutz", "Weihnachtsbaumkanone", "Falafel"]

    # generate_presentations(speaker_names=["Raimund Hensen", "Katharina Rothhöft", "Weihnachtsmann", "Osterhase", "Harry Potter"],
    #                       #  topic_pool=["Kiribati", "Buß- und Bettag", "Schoko-Weihnachtsmänner"],
    #                        topic_pool=topics,
    #                        images=True,
    #                        launch_first=True,
    #                        launch_all=True,
    #                        language="de")

