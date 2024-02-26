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

