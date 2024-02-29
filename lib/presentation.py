
from dataclasses import dataclass, field
from pathlib import Path
from pptx import Presentation as PptxPresentation


@dataclass
class Presentation:
    speaker: str
    topic: str
    wrong_topics: list[str]
    slide_style_flags: list[dict] = field(default_factory=lambda: [])
    speaker_style_flags: list[dict] = field(default_factory=lambda: [])
    speaker_instructions: list[str] = field(default_factory=lambda: [])
    image_query_suffix: str | None = None
    prompt: str | None = None
    markdown: str | None = None
    contents: list[dict] = field(default_factory=lambda: [])
    images: list[dict] = field(default_factory=lambda: [])
    pptx_path: Path | None = None
    # pptx: PptxPresentation | None

    # DB connection
    session_id: str | None = None
    player_id: str | None = None
    player: dict | None = None
    topic_id: str | None = None


