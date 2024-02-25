import os, sys
from pathlib import Path
from dotenv import load_dotenv

# sys.path.append(str(Path(os.getcwd()).parent))
load_dotenv()

import re
from datetime import datetime

TMP_DIR = Path(os.getcwd()) / "tmp"
TEMPLATE_DIR = Path(os.getcwd()) / "template"

PPTX_TEMPLATE_DIR = TEMPLATE_DIR / "pptx"

SEARCH_RESULTS_DIR = TMP_DIR / "search_results"
IMG_DIR = TMP_DIR / "img"
CHATS_DIR = TMP_DIR / "chats"
MARKDOWN_DIR = TMP_DIR / "md"
PPTX_DIR = TMP_DIR / "pptx"

STRFTIME_FULL = "%Y%m%d-%H%M%S"
NOW = lambda: datetime.now().strftime(STRFTIME_FULL)
ESCAPE_PATH = lambda q: re.sub(r"[^A-Za-z0-9]", "", q)

LANGUAGES = ["de", "en"]

