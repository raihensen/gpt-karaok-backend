from __future__ import annotations

import random
import urllib.parse

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


def random_derangement(xs: list, retries=100):
    """ Creates a random derangement of xs (every element ends up at different index than before). """
    n = len(xs)
    if n < 2:
        raise ValueError(f"random_derangement only works with at least two elements.")
    if retries == 0:
        raise ValueError(f"random_derangement reached maximum retries.")
    
    free = set(range(n))
    ys = {}
    for i, x in enumerate(xs):
        jchoice = free - {i}
        if not jchoice:
            return random_derangement(xs, retries - 1)
        j = random.choice(list(jchoice))
        ys[j] = x
        free.remove(j)
    # print(f"{retries} retries remaining.")
    return [y for j, y in sorted(list(ys.items()), key=lambda item: item[0])]


def random_chunk_derangement(xs: list, m: int, retries=100):
    """ Creates a random derangement of xs with no element ending up in the same chunk of size m. """
    n = len(xs)
    if n < 2:
        raise ValueError(f"random_chunk_derangement only works with at least two elements.")
    if m == 0 or m > n / 2 or n % m != 0:
        raise ValueError(f"random_chunk_derangement: Invalid value for chunk size m.")
    if retries == 0:
        raise ValueError(f"random_chunk_derangement reached maximum retries.")
    
    free = set(range(n))
    ys = {}
    for i, x in enumerate(xs):
        k = i // m
        jchoice = free - set(range(k * m, (k + 1) * m))
        if not jchoice:
            return random_chunk_derangement(xs, m)
        j = random.choice(list(jchoice))
        ys[j] = x
        free.remove(j)
    # print(f"{retries} retries remaining.")
    return [y for j, y in sorted(list(ys.items()), key=lambda item: item[0])]


