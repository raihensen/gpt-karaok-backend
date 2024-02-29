
from abc import ABC
from dataclasses import dataclass
import functools
import math
import random
from typing import Callable, Dict

from openai import OpenAI

from lib.presentation import Presentation
from lib.config import *
from lib.utils import *


@dataclass
class StyleFlag:
    name: str
    definition: Dict[str, str | Callable[[], str]]

    def process(self, language: str):
        p = self.definition.get(language, None)
        if p is None:
            raise ValueError(f"{type(self).__name__} '{self.name}': Undefined language {language}.")
        if isinstance(p, Callable):
            p = p()
        if not isinstance(p, str):
            raise ValueError(f"{type(self).__name__} '{self.name}': Result is not a string.")
        return p

@dataclass
class SlideStyleFlag(StyleFlag):
    pass
@dataclass
class PromptStyleFlag(SlideStyleFlag):
    pass
@dataclass
class ImageQueryStyleFlag(SlideStyleFlag):
    pass
@dataclass
class SpeakerStyleFlag(StyleFlag):
    pass


def generate_prompts(presentations: list[Presentation],
                     language: str,
                     num_slides=5,
                     num_bullets_min=4,
                     num_bullets_max=6,
                     num_wrong_topics=2):

    num_presentations = len(presentations)
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

    def prompt_foreign_language(current_language: str):
        i = random_slide_number(start=2, end=num_slides)
        if current_language == "de":
            lang1 = random.choice(["Niederländisch", "Schwedisch", "Spanisch", "Türkisch", "Slowakisch", "Japanisch"])
            return f"Schreibe Folie {i} bitte auf {lang1}. Benutze nur das lateinische Alphabet."
        if current_language == "en":
            lang1 = random.choice(["Dutch", "Swedish", "Spanish", "Turkish", "Slovak", "Japanese"])
            return f"Write slide {i} in the {lang1} language. Use the latin alphabet only."
        raise ValueError(f"prompt_foreign_language: Undefined language {current_language}.")

    def prompt_wrong_topic(wrong_topics):
        b = 2
        ix = random_slide_numbers(k=len(wrong_topics))
        return {
            "de": f'Bitte sorge dafür, dass die {prompt_random_slide_numbers(lang="de", numbers=ix)} je {b} Stichpunkt{"e" if b > 1 else ""} mit komplett falschen Fakten enthalten, die das Thema der Präsentation mit jeweils einem anderen Thema verbinden. Diese Themen sind: ' + ", ".join([f"Folie {i}: \"{t}\"" for i, t in zip(ix, wrong_topics)]) + ".",
            "en": f'Please make {prompt_random_slide_numbers(lang="en", numbers=ix)} contain {b} bullet point{"s" if b > 1 else ""} with made up facts, somehow connecting the presentation topic with another topic. These topics are: ' + ", ".join([f"slide {i}: \"{t}\"" for i, t in zip(ix, wrong_topics)]) + "."
        }


    SLIDE_STYLE_FLAGS = [
        PromptStyleFlag(name="TECHNICAL", definition={
            "de": "Verwende bitte viele Fachbegriffe, die das Publikum eventuell nicht versteht.",
            "en": "Please make the presentation use many technical terms that the audience might not understand."
        }),
        PromptStyleFlag(name="FOREIGN_LANGUAGE", definition={
            "de": functools.partial(prompt_foreign_language, current_language=language),
            "en": functools.partial(prompt_foreign_language, current_language=language),
        }),
        PromptStyleFlag(name="POETIC", definition={
            "de": "Ab Folie 2, versuche dass die Stichpunkte Paarreime bilden.",
            "en": "Beginning on slide 2, try to make the bullet points rhyme (adjacent rhymes)."
        }),
        PromptStyleFlag(name="EXCESSIVE_INDENTS", definition={
            "de": "Rücke die Stichpunkte unnötig ein, bis zu 4 Level. Die Gruppierung soll keinen Sinn ergeben und optisch keinem wiederkehrenden Muster folgen.",
            "en": "Please indent the bullet points excessively, up to 4 levels. The grouping and indent level should not make any sense."
        }),
        PromptStyleFlag(name="KARAOKE", definition={
            "de": lambda: f"Ersetze die Stichpunkte von Folie {random_slide_number(start=3)} durch ein paar Zeilen eines sehr bekannten Songs, zu dem man gut mitsingen kann.",
            "en": lambda: f"Replace the bullets of slide {random_slide_number(start=3)} by a few lines of lyrics of a very famous song that is good to sing along.",
        }),
        ImageQueryStyleFlag(name="MEMES", definition={"de": "meme", "en": "meme"}),
        ImageQueryStyleFlag(name="CHINA", definition={"de": "china", "en": "china"}),
        ImageQueryStyleFlag(name="UGLY", definition={"de": "hässlich", "en": "ugly"}),
        ImageQueryStyleFlag(name="PINK", definition={"de": "pink", "en": "pink"}),
    ]
    
    ROLEPLAY = [SpeakerStyleFlag(name="ROLEPLAY", definition={
        "en": lambda: f"Role play: Act like a {role['en']}.",
        "de": lambda: f"Rollenspiel: Du bist ein*e {role['de']}.",
    }) for role in [
        {"en": "super hero", "de": "Superheld*in"},
        {"en": "way too motivated fitness coach", "de": "viel zu motivierter Fitnesscoach"},
        {"en": "time traveller born 200 years ago", "de": "Zeitreisende*r von vor 200 Jahren"},
        {"en": "news announcer", "de": "Nachrichtensprecher*in"},
        {"en": "beauty influencer and sneakily include a hidden advertisement", "de": "Beauty-Influencer*in und baust eine versteckte Werbung ein"},
    ]]
    RANDOM_WORDS = [SpeakerStyleFlag(name="RANDOM_WORDS", definition={
        "en": lambda: f"Use the word '{word['en']}' at least 3 times.",
        "de": lambda: f"Verwende mindestens 3 Mal das Wort '{word['de']}'.",
    }) for word in [
        {"en": "zucchini", "de": "Zucchini"},
        {"en": "tired", "de": "müde"},
        {"en": "tired", "de": "müde"},
        {"en": "tired", "de": "müde"},
        {"en": "tired", "de": "müde"},
    ]]
    SPEAKER_STYLE_FLAGS = [
        SpeakerStyleFlag(name="IMITATION", definition={
            "en": "Starting on Slide 2, try to imitate a celebrity of your choice.",
            "de": "Fange ab Folie 2 an, beim Reden einen Promi deiner Wahl zu imitieren."
        }),
        SpeakerStyleFlag(name="SPEECHLESS", definition={
            "en": "On slide 3 you suddenly lose your voice but continue moving your mouth.",
            "de": "Verstumme auf Folie 3 plötzlich beim Reden, bewege den Mund aber weiter."
        }),
        SpeakerStyleFlag(name="ACCENT", definition={
            "en": "Talk with a funny accent.",
            "de": "Spreche mit einem witzigen Akzent/Dialekt."
        }),
        SpeakerStyleFlag(name="DRAWING", definition={
            "en": "Use the drawing function on your slides to explain the concepts of your talk.",
            "de": "Benutze die 'Zeichnen'-Funktion auf den Folien, um den Inhalt genauer zu erklären."
        }),
        SpeakerStyleFlag(name="STORYTELLING", definition={
            "en": "Explain some slide by telling the audience made up stories/experiences from your own life.",
            "de": "Erzähle erfundene Geschichten/Erfahrungen aus deinem eigenen Leben, um die Vortragsinhalte näherzubringen."
        }),
        SpeakerStyleFlag(name="MIMIC", definition={
            "en": "Repeat any movements or sounds from the audience. If someone coughs, you cough, If they applaude, you applaude.",
            "de": "Wiederhole jede Bewegung / jedes Geräusch aus dem Publikum. Wenn jemand hustest, hustest du. Wenn jemandd klatscht, klatschst du auch."
        }),
        *random.sample(ROLEPLAY, min(len(ROLEPLAY), round(.25 * len(presentations)))),
        *random.sample(RANDOM_WORDS, min(len(RANDOM_WORDS), round(.25 * len(presentations)))),
    ]

    PROMPT = {
        "de": lambda topic, prompt_additions: "\n".join([
            f'Generiere aus Stichpunkten bestehende Inhalte für PowerPoint-Folien zum Thema "{topic}", im Markdown-Format.',
            f'Die Präsentation soll {num_slides} Folien enthalten und pro Folie {f"{num_bullets_min}-{num_bullets_max}" if num_bullets_min != num_bullets_max else num_bullets_min} Stichpunkte.',
            'Der Präsentationsstil soll locker, aber dennoch informativ sein.',
            f'{prompt_additions}',
            'Baue 2-3 Witze in den Inhalt ein.',
            'Formatiere die Antwort im Markdown-Format! Verwende Überschrift 1 für den Präsentationstitel, Überschrift 2 für Folientitel, und Aufzählungen für die Stichpunkte. Die Antwort soll ausschließlich Markdown sein, füge keine weiteren Erklärungen hinzu!'
        ])
    }

    slide_style_flags = sample_minimal_repitions(SLIDE_STYLE_FLAGS, k=num_presentations)
    speaker_style_flags = sample_minimal_repitions(SPEAKER_STYLE_FLAGS, k=num_presentations)

    for presentation, slide_style_flag, speaker_style_flag in zip(presentations,
                                                                  slide_style_flags,
                                                                  speaker_style_flags):
        
        topic, wrong_topics = presentation.topic, presentation.wrong_topics
        presentation.slide_style_flags = [slide_style_flag] if slide_style_flag else []
        presentation.speaker_style_flags = [speaker_style_flag] if speaker_style_flag else []

        # Apply style flags
        slide_style_prompt = None
        slide_wrong_topic_prompt = None
        image_query_suffix = None

        if isinstance(slide_style_flag, PromptStyleFlag):
            slide_style_prompt = slide_style_flag.process(language=language)
        if isinstance(slide_style_flag, ImageQueryStyleFlag):
            image_query_suffix = slide_style_flag.process(language=language)
        if wrong_topics:
            slide_wrong_topic_prompt = prompt_wrong_topic(wrong_topics)[language]
        
        if isinstance(speaker_style_flag, SpeakerStyleFlag):
            presentation.speaker_instruction = speaker_style_flag.process(language=language)

        prompt_additions = "\n".join([p for p in [slide_wrong_topic_prompt, slide_style_prompt] if p is not None])
        if language not in PROMPT:
            raise ValueError(f"promt creation: Undefined language {language}.")
        presentation.prompt = PROMPT[language](topic=topic, prompt_additions=prompt_additions)
        
        
        # print(speaker_name)
        # print(f"  Topic: {topic}")
        # print("  Prompt:\n" + indent(presentation.prompt, 4))
        # print()
        # if wrong_topics:
        #     print(f"  Wrong topics: {', '.join(wrong_topics)}")
        #     print(f"  Wrong topics prompt: {slide_wrong_topic_prompt}")
        # if slide_style_prompt:
        #     print("  Slide style prompt: " + slide_style_prompt)
        # if image_query_suffix:
        #     print("  Image query suffix: " + image_query_suffix)
        # if presentation.speaker_instruction:
        #     print("  Speaker style instruction: " + presentation.speaker_instruction)


if __name__ == "__main__":
    
    # f = open(TEMPLATE_DIR / "pp_karaoke.txt", "r", encoding="utf8")
    # tt = [t.strip() for t in f.read().strip().split(",")]
    # print(tt)

    # tt = ["Gemüselasagne", "Ludwigshafen am Rhein", "Weltwirtschaftskrise"]
    tt = ["Kiribati", "Buß- und Bettag", "Schoko-Weihnachtsmänner"]



# num_imgs = min(len(contents), len(imgs))
# slide_imgs = random.sample(imgs, num_imgs)
# img_slides = random.sample(contents, num_imgs)

# for slide, img in zip(img_slides, slide_imgs):
#     slide["img"] = img
    
