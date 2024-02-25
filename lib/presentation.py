
from dataclasses import dataclass, field
from pathlib import Path
from pptx import Presentation as PptxPresentation


@dataclass
class Presentation:
    speaker: str
    topic: str
    wrong_topics: list[str]
    slide_style_flags: list[dict]
    speaker_style_flags: list[dict]
    speaker_instructions: list[str]
    prompt: str | None = None
    markdown: str | None = None
    contents: list[dict] = field(default_factory=lambda: [])
    images: list[dict] = field(default_factory=lambda: [])
    pptx_path: Path | None = None
    # pptx: PptxPresentation | None

