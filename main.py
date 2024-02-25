

import json

from lib.generator import generate_presentations
from lib.utils import *
from lib.config import *


# Import topics from text file, comma-separated
# with open(TEMPLATE_DIR / "topics" / "raimund.txt", "r", encoding="utf8") as f:
#     topics = [t.strip() for t in f.read().strip().split(",")]
#     print(topics)

# Pool of random topics (GPT generated)
topics = json.load(open(TEMPLATE_DIR / "topics" / "topics-50-2.json"))

# Use hard-coded list
# topics = ["Gemüselasagne", "Ludwigshafen am Rhein", "Weltwirtschaftskrise"]

if __name__ == "__main__":
    
    generate_presentations(speaker_names=["Raimund Hensen", "Reinhard Hensen"],
                          #  topic_pool=["Kiribati", "Buß- und Bettag", "Schoko-Weihnachtsmänner"],
                           topic_pool=topics,
                           images=False,
                           language="de")

