from __future__ import annotations

import random
import urllib.parse
from pathlib import Path
import os
import subprocess

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib.presentation import Presentation


# from https://stackoverflow.com/a/38020041
def uri_validator(x):
    try:
        result = urllib.parse.urlparse(x)
        return all([result.scheme, result.netloc])
    except:
        return False


def indent(s: str, n: int) -> str:
    return "\n".join([(n * "  ") + line for line in s.split("\n")])


def sample_minimal_repitions(population, k):
    size = len(population)
    if k <= size:
        return random.sample(population, k)
    sample = []
    for _ in range(k // size):
        sample += random.sample(population, len(population))
    return sample + random.sample(population, k % size)


def launch_presentations(presentations: list[Presentation]):
    ppt_exe = Path(os.environ.get('POWERPOINT_EXE_PATH'))

    print([(p.speaker, p.pptx_path) for p in presentations])

    for i, presentation in enumerate(presentations):
        # Launch slideshow in PowerPoint app
        assert presentation.pptx_path is not None, f"Presentation #{i + 1} ({presentation.speaker}) cannot be launched."
        cmd = f"{ppt_exe} /s \"{presentation.pptx_path}\""
        print(f"Launching presentation #{i + 1} ({presentation.speaker}) ...")
        subprocess.run((cmd))

