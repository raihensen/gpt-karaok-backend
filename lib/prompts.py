

import json
import random
from typing import Callable

from openai import OpenAI
from lib.google_images import google_image_search
from lib.markdown import parse_md_outline

from lib.openai_access import openai_request
from lib.pptx_factory import make_pptx

from pathlib import Path

from lib.presentation import Presentation

if __name__ == "__main__":
    import sys, os
    sys.path.append(str(Path(os.getcwd())))
    sys.path.append(str(Path(os.getcwd()).parent))

from lib.config import *
from lib.utils import *


def generate_prompts(openai_client,
                     speaker_names,
                     topic_pool,
                     language,
                     num_slides=5,
                     num_bullets_min=4,
                     num_bullets_max=6,
                     num_wrong_topics=2):

    num_presentations = len(speaker_names)
    slide_numbers = range(1, num_slides + 1)

    def random_slide_number(start=None, end=None):
        return random.randint(max(1, start) if start is not None else 1,
                              min(end, max(slide_numbers)) if end is not None else max(slide_numbers))

    def random_slide_numbers(k, start=None, end=None, sort=True):
        numbers = [i for i in slide_numbers if (start is None or i >= start) and (end is None or i <= end)]
        if len(numbers) < k:
            raise ValueError(f"random_slide_numbers: Could not sample slide numbers with k={k}, start={start}, end={end} (not enough slides).")
        ix = random.sample(numbers, k)
        if sort:
            ix = sorted(ix)
        return ix

    def prompt_random_slide_numbers(lang, k=None, numbers=None, sort=True):
        if k is not None and numbers is None:
          numbers = random_slide_numbers(k, sort=sort)
          if k == 1:
              return numbers[0]
        k = len(numbers)
        if lang == "de":
            return ("Folien " if k > 1 else "Folie ") + ", ".join([str(i) for i in numbers[:-1]]) + f" und {numbers[-1]}"
        if lang == "en":
            return ("slides " if k > 1 else "slide ") + ", ".join([str(i) for i in numbers[:-1]]) + f" and {numbers[-1]}"
        raise ValueError(f"prompt_random_slide_numbers: Undefined language {lang}.")

    def prompt_foreign_language():
        a = 2
        b = 2
        ix = random_slide_numbers(a, sort=True)
        languages = random.sample(["nl", "sv", "es", "tr", "sk", "jp"], a)
        return {
            "de": " ".join([f"On slide {i}, write {b} of the bullets in the language with ISO code '{lang}'." for i, lang in zip(ix, languages)]) + " Benutze nur das lateinische Alphabet.",
            "en": " ".join([f"Schreibe auf Folie {i} bitte {b} der Stichpunkte auf der Sprache mit dem ISO-Code '{lang}'." for i, lang in zip(ix, languages)]) + " Use the latin alphabet only.",
        }

    def prompt_wrong_topic(wrong_topics):
        b = 2
        ix = random_slide_numbers(k=len(wrong_topics))
        return {
            "de": f'Bitte sorge dafür, dass die {prompt_random_slide_numbers(lang="de", numbers=ix)} je {b} Stichpunkt{"e" if b > 1 else ""} mit komplett falschen Fakten enthalten, die das Thema der Präsentation mit jeweils einem anderen Thema verbinden. Diese Themen sind: ' + ", ".join([f"Folie {i}: \"{t}\"" for i, t in zip(ix, wrong_topics)]) + ".",
            "en": f'Please make {prompt_random_slide_numbers(lang="en", numbers=ix)} contain {b} bullet point{"s" if b > 1 else ""} with made up facts, somehow connecting the presentation topic with another topic. These topics are: ' + ", ".join([f"slide {i}: \"{t}\"" for i, t in zip(ix, wrong_topics)]) + "."
        }


    SLIDE_STYLE_FLAGS = [{
        "flag": "TECHNICAL",
        "target": "prompt",
        "prompt": {
            "de": "Verwende bitte viele Fachbegriffe, die das Publikum eventuell nicht versteht.",
            "en": "Please make the presentation use many technical terms that the audience might not understand."
        }
    }, {
        "flag": "FOREIGN_LANGUAGE",
        "target": "prompt",
        "prompt": prompt_foreign_language
    }, {
        "flag": "POETIC",
        "target": "prompt",
        "prompt": {
            "de": "Ab Folie 2, versuche dass die Stichpunkte Paarreime bilden.",
            "en": "Beginning on slide 2, try to make the bullet points rhyme (adjacent rhymes)."
        }
    }, {
        "flag": "EXCESSIVE_INDENTS",
        "target": "prompt",
        "prompt": {
            "de": "Rücke die Stichpunkte unnötig ein, bis zu 4 Level. Die Gruppierung soll keinen Sinn ergeben und optisch keinem wiederkehrenden Muster folgen.",
            "en": "Please indent the bullet points excessively, up to 4 levels. The grouping and indent level should not make any sense."
        }
    }, {
        "flag": "KARAOKE",
        "target": "prompt",
        "prompt": lambda: {
            "de": f"Replace the bullets of slide {random_slide_number(start=3)} by a few lines of lyrics of a very famous song that is good to sing along.",
            "en": f"Ersetze die Stichpunkte von Folie {random_slide_number(start=3)} durch ein paar Zeilen eines sehr bekannten Songs, zu dem man gut mitsingen kann."
        }
    }, {
        "flag": "MEMES",
        "target": "image_query",
        "query_suffix": {"de": "meme", "en": "meme"}
    }]

    SPEAKER_STYLE_FLAGS = [{
        "flag": "IMITATION",
        "target": "speaker",
        "instruction": {
            "en": "Try to imitate a celebrity of your choice.",
            "de": "Fange ab Folie 2 an, beim Reden einen Promi deiner Wahl zu imitieren."
        }
    }, {
        "flag": "ROLEPLAY",
        "target": "speaker",
        "instruction": lambda: {
            "en": f"Role play: Act like a {random.choice(['super hero', 'time traveller born 200 years ago', 'beauty influencer', 'news announcer'])}.",
            "de": f"Rollenspiel: Du bist ein*e {random.choice(['Superheld*in', 'Zeitreisende*r von vor 200 Jahren', 'Beauty-Influencer*in', 'Nachrichtensprecher*in'])}.",
        }
    }]

    def make_prompt(topic, prompt_additions):
        return {
            "de": f'''Generiere aus Stichpunkten bestehende Inhalte für PowerPoint-Folien zum Thema "{topic}", im Markdown-Format. Die Präsentation soll {num_slides} Folien enthalten und pro Folie {f"{num_bullets_min}-{num_bullets_max}" if num_bullets_min != num_bullets_max else num_bullets_min} Stichpunkte. Der Präsentationsstil soll locker, aber dennoch informativ sein.
    {prompt_additions}
    Baue 2-3 Witze in den Inhalt ein.
    Formatiere die Antwort im Markdown-Format! Verwende Überschrift 1 für den Präsentationstitel, Überschrift 2 für Folientitel, und Aufzählungen für die Stichpunkte. Die Antwort soll ausschließlich Markdown sein, füge keine weiteren Erklärungen hinzu!'''
        }

    slide_style_flags = sample_minimal_repitions(SLIDE_STYLE_FLAGS, k=num_presentations)
    speaker_style_flags = sample_minimal_repitions(SPEAKER_STYLE_FLAGS, k=num_presentations)
    m = 1 + num_wrong_topics
    topic_sample = sample_minimal_repitions(topic_pool, k=num_presentations * m)
    topics = [t for i, t in enumerate(topic_sample) if i % m == 0]
    wrong_topicss = [topic_sample[i * m + 1:(i + 1) * m] if num_wrong_topics else [] for i in range(num_presentations)]

    presentations = []
    for topic, wrong_topics, speaker_name, slide_style_flag, speaker_style_flag in zip(topics,
                                                                                       wrong_topicss,
                                                                                       speaker_names,
                                                                                       slide_style_flags,
                                                                                       speaker_style_flags):
        
        # Apply style flags
        slide_style_prompt = None
        slide_wrong_topic_prompt = None
        image_query_suffix = None
        if slide_style_flag["target"] == "prompt":
            slide_style_prompt = slide_style_flag["prompt"]
            if isinstance(slide_style_prompt, Callable):
                slide_style_prompt = slide_style_prompt()
            slide_style_prompt = slide_style_prompt[language]
            if not isinstance(slide_style_prompt, str):
                slide_style_prompt = None
        elif slide_style_flag["target"] == "image_query":
            image_query_suffix = slide_style_flag["query_suffix"]
            if isinstance(image_query_suffix, Callable):
                image_query_suffix = image_query_suffix()
            image_query_suffix = image_query_suffix[language]
            if not isinstance(image_query_suffix, str):
                image_query_suffix = None
        speaker_style_instruction = speaker_style_flag["instruction"]
        if isinstance(speaker_style_instruction, Callable):
            speaker_style_instruction = speaker_style_instruction()
        speaker_style_instruction = speaker_style_instruction[language]
        if not isinstance(speaker_style_instruction, str):
            speaker_style_instruction = None

        if wrong_topics:
            slide_wrong_topic_prompt = prompt_wrong_topic(wrong_topics)[language]
        
        prompt_additions = "\n".join([p for p in [slide_wrong_topic_prompt, slide_style_prompt] if p is not None])
        prompt = make_prompt(topic, prompt_additions)[language]
        # print(prompt)

        presentations.append(Presentation(topic=topic,
                                          speaker=speaker_name,
                                          wrong_topics=wrong_topics,
                                          slide_style_flags=[slide_style_flag] if slide_style_flags else [],
                                          speaker_style_flags=[speaker_style_flags] if speaker_style_flags else [],
                                          speaker_instructions=[speaker_style_instruction] if speaker_style_instruction else [],
                                          prompt=prompt))

        # presentations.
        
        # print(speaker_name)
        # print(f"  Topic: {topic}")
        # print("  Prompt:\n" + indent(prompt, 4))
        # print()
        # if wrong_topics:
        #     print(f"  Wrong topics: {', '.join(wrong_topics)}")
        #     print(f"  Wrong topics prompt: {slide_wrong_topic_prompt}")
        # if slide_style_prompt:
        #     print("  Slide style prompt: " + slide_style_prompt)
        # if image_query_suffix:
        #     print("  Image query suffix: " + image_query_suffix)
        # if speaker_style_instruction:
        #     print("  Speaker style instruction: " + speaker_style_instruction)
    return presentations

if __name__ == "__main__":
    
    # f = open(TEMPLATE_DIR / "pp_karaoke.txt", "r", encoding="utf8")
    # tt = [t.strip() for t in f.read().strip().split(",")]
    # print(tt)

    # tt = ["Gemüselasagne", "Ludwigshafen am Rhein", "Weltwirtschaftskrise"]
    tt = ["Kiribati", "Buß- und Bettag", "Schoko-Weihnachtsmänner"]

    openai_client = OpenAI()
    generate_prompts(openai_client,
                     speaker_names=["Raimund Hensen"],
                     #  topic_pool=json.load(open(TEMPLATE_DIR / "topics-50-2.json")), language="de")
                     topic_pool=tt, language="de")



# num_imgs = min(len(contents), len(imgs))
# slide_imgs = random.sample(imgs, num_imgs)
# img_slides = random.sample(contents, num_imgs)

# for slide, img in zip(img_slides, slide_imgs):
#     slide["img"] = img
    
