
import re


def parse_md_line(line: str):
		# Headings
		if line.startswith("# "):
				return ("h1", line[2:])
		if line.startswith("## "):
				return ("h2", process_slide_title(line[3:].strip()))
		line = re.sub("^#+\s*", "", line)

		# Bullets
		for i in range(4):
				tabs = (i + 1) * "  "
				if line.startswith(tabs + "- ") or line.startswith(tabs + "* "):
						return ("bullet", line[2 * (i + 1) + 2:], i)
		line = line.strip()
		line = re.sub("^[\-\*] ", "", line).strip()

		# Normal text
		return ("text", line)


def process_slide_title(title: str):
		match = re.match(r"^Folie \d+: (.*)$", title)
		if match:
				title = match.groups()[0]
		return title


def parse_md_outline(md: str, topic: str = None):
		lines = [line.rstrip() for line in md.split("\n")]
		lines = [parse_md_line(line) for line in lines if line]
		if topic is None:
				assert lines[0][0] == "h1", "The topic is not correctly formatted."
				topic = lines[0][1]
		else:
				assert lines[0] == ("h1", topic), "The topic does not match or is not correctly formatted."
		lines = lines[1:]
		titles = [(i, line) for i, line in enumerate(lines) if line[0] == "h2"]
		contents = []
		for i, (j0, title) in enumerate(titles):
				j1 = titles[i + 1][0] if i < len(titles) - 1 else len(lines)
				contents.append({
						"title": title[1],
						"content": lines[j0 + 1:j1]
				})
		return topic, contents

