

from enum import Enum
import json
import requests
import time

from lib.generator import generate_presentations
from lib.utils import *
from lib.config import *

import argparse


class SessionState(Enum):
    INIT = 0
    READY = 1
    CLOSED = 2


def backend_mainloop(session_id: str):
    if "/" in session_id:
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
        print(f"Session state: {session_state.name}")
        if session_state == SessionState.CLOSED:
            generate_from_api(session)
            break
        
        time.sleep(3)


def generate_from_api(session: dict):
    
    players = session["players"]
    speaker_names = [p["name"] for p in players]
    if not speaker_names:
        raise ValueError(f"No players found.")

    topics = sum([[t["name"] for t in p["topics"]] for p in players], [])
    if not topics:
        raise ValueError(f"No topics found.")
    if len(topics) < 3 * len(speaker_names):
        raise ValueError(f"Not enough topics found, provide at least 3 topics per speaker.")

    random.shuffle(speaker_names)
    random.shuffle(topics)

    generate_presentations(speaker_names=speaker_names,
                           topic_pool=topics,
                           images=True,
                           launch_first=True,
                           launch_all=True,
                           language="de")


if __name__ == "__main__":
    
    # parser = argparse.ArgumentParser("main.py")
    # parser.add_argument("session_id", help="The ID of the session to be fetched via the API.", type=str)
    # args = parser.parse_args()
    # backend_mainloop(session_id=args.session_id)
    
    # Import topics from text file, comma-separated
    # with open(TEMPLATE_DIR / "topics" / "raimund.txt", "r", encoding="utf8") as f:
    #     topics = [t.strip() for t in f.read().strip().split(",")]
    #     print(topics)

    # Pool of random topics (GPT generated)
    topics = json.load(open(TEMPLATE_DIR / "topics" / "topics-50-2.json"))

    # Use hard-coded list
    # topics = ["Gemüselasagne", "Ludwigshafen am Rhein", "Weltwirtschaftskrise"]
    # topics = ["Mutterschutz", "Weihnachtsbaumkanone", "Falafel"]

    generate_presentations(speaker_names=["Raimund Hensen", "Barbara Muders"],
                          #  topic_pool=["Kiribati", "Buß- und Bettag", "Schoko-Weihnachtsmänner"],
                           topic_pool=topics,
                           images=True,
                           launch_first=True,
                           launch_all=True,
                           language="de")

