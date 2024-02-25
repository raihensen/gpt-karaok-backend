
from pptx import Presentation
from pptx.util import Cm, Pt
from PIL import UnidentifiedImageError

from lib.google_images import GoogleImage
from lib.utils import *
from lib.config import *


def set_font(element, name: str = None, size: int = None, bold: bool = None, italic: bool = None):
		t = type(element).__name__
		if t == "SlidePlaceholder":
				element = element.text_frame.paragraphs[0]
		font = element.font
		if name is not None:
				font.name = name
		if size is not None:
				font.size = Pt(size)
		if bold is not None:
				font.bold = bold
		if italic is not None:
				font.italic = italic


def make_pptx(pptx,
							topic: str,
							speaker: str,
							contents: list,
							title_font={"name": "Aptos", "size": 48},
							speaker_font={"name": "Aptos", "size": 36},
							slide_title_font={"name": "Aptos", "size": 36},
							content_font={"name": "Aptos", "size": 20}):
		
		if pptx:
				with open(pptx, "rb") as f:
						prs = Presentation(f)
		else:
				prs = Presentation()
		prs.core_properties.language = "de"
		title_slide_layout = prs.slide_layouts[0]
		bullet_slide_layout = prs.slide_layouts[1]
		bullet_img_slide_layout = prs.slide_layouts[2]
		
		slide = prs.slides.add_slide(title_slide_layout)
		e_title = slide.shapes.title
		e_title.text = topic
		set_font(e_title, **title_font)
		e_speaker = slide.placeholders[1]

		e_speaker.text = speaker
		set_font(e_speaker, **speaker_font)
		
		for i, content in enumerate(contents):
				img: GoogleImage = content.get("img", None)
				
				layout = bullet_slide_layout if img is None else bullet_img_slide_layout
				slide = prs.slides.add_slide(layout)
				shapes = slide.shapes
				
				e_slide_title = shapes.title
				e_slide_title.text = content["title"]
				set_font(e_slide_title.text_frame.paragraphs[0], **slide_title_font)

				if img is not None:
						ext = str(img.local_path).split(".")[-1]
						if ext.lower() not in ["bmp", "gif", "jpg", "jpeg", "png"]:
								continue
						max_width, max_height = 11.5, 12.57
						x, y = 20.3, 5
						aspect = img.width / img.height
						if aspect < max_width / max_height:
								size = {"height": Cm(max_height)}
								w = aspect * max_height
								# align right
								x += max_width - w
						else:
								size = {"width": Cm(max_width)}
								h = max_width / aspect
								# align vertical middle
								y += (max_height - h) / 2
						try:
								slide.shapes.add_picture(str(img.local_path), left=Cm(x), top=Cm(y), **size)
						except Exception:
								pass
				
				body_shape = shapes.placeholders[1]
				tf = body_shape.text_frame
				p = tf.paragraphs[0]
				for j, (pstyle, text, *args) in enumerate(content["content"]):
						if j > 0:
								p = tf.add_paragraph()
						if pstyle == "bullet" and len(args):
								p.level = args[0]
						set_font(p, **content_font)

						parts = [("normal" if k % 2 == 0 else "bold", s) for k, s in enumerate(text.split("**"))]

						for rstyle, s in parts:
								run = p.add_run()
								run.text = s
								if rstyle == "bold":
										set_font(run, bold=True)
		
		# path = PPTX_DIR / f"pptx-{NOW()}-{ESCAPE_PATH(speaker)}-{ESCAPE_PATH(topic)}.pptx"
		path = PPTX_DIR / f"pptx-{NOW()}-{ESCAPE_PATH(speaker)}.pptx"
		prs.save(path)
		return path

