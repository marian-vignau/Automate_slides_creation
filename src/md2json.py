#!/usr/bin/fades
import unicodedata
import pprint
import re
import argparse
import json


marks = dict(
    separator=["---"],
    subtitle=["title", "título", "titulo"],
    visual=["visual idea", "visual", "visuals", "ayuda visual"],
    notes=[
        "speaker notes",
        "notes",
        "teacher notes",
        "slide",
        "sample answer",
        "solution key",
        "notas para el presentador",
        "notas del orador",
        "notas",
    ],
    content=["text", "content", "subtitle"],
)


def show(*args, **kwargs):
    if VERBOSE:
        pprint.pprint(*args, **kwargs)


def clean_line(line: str):
    """Eliminate lines without content, outer parenthesis and enumerations."""
    line_ = line.replace("*", "").replace("`", "").replace("-", "").strip()
    if not line_:
        return None

    # process enumerations
    while len(line) > 1:
        if line.startswith("* ") or line.startswith("- "):
            line = line[1:].strip()
        elif line.startswith("("):
            line = line[1:].strip()
            if line.endswith(")"):
                line = line[:-1].strip()
        if line.startswith("** "):
            line = line[1:].strip()
        else:
            break
    return line


def chop_slides(md_file_path):
    """Separate slides in markdown file."""
    current_slide = []
    count_backticks = 0
    with open(md_file_path, "r", encoding="utf-8") as f:

        for line in f.readlines():
            line = line.strip()
            # sometimes, it adds backticks to show this is md
            if line.startswith("```"):
                count_backticks += 1
            #:while:w    continue
            # if count_backticks > 0 and count_backticks % 2 == 0:
            #    continue

            if line in marks["separator"] or "---" in line:
                if current_slide:
                    yield current_slide
                current_slide = []
            else:
                if c_line := clean_line(line):
                    current_slide.append(c_line)

        if current_slide:
            yield current_slide


def process_title(line: str):
    """Extract title and index from line."""
    i = 0
    for i in range(len(line)):
        if line[i] != "#":
            break
    title = line[i:]
    index = None

    if "Slide" in title:
        pos = title.find("Slide")
        index = title[pos : pos + len("Slide NNN")].replace(":", "").strip()
        if ":" in title[pos:]:
            title = title.split(":")[-1].strip()
        if " - " in title[pos:]:
            title = title.split(" – ")[-1]
    return title.strip(), index


def separate_title(slide_md, n_slide):
    """Separate title and index from slide data."""
    current_slide = {"index": [], "title": [], "data": []}
    for line in slide_md:
        # process titles
        if line.startswith("#"):
            title, index = process_title(line)
            if index:
                current_slide["index"] = [index]
            else:
                current_slide["index"] = [f"Slide {n_slide}"]
            current_slide["title"].append(title)

        elif current_slide is not None:
            current_slide["data"].append(line)
    return current_slide


def remove_emojis(line):
    # Regular expression pattern for matching emojis
    text = (
        line.replace("*", "")
        .replace("`", "")
        .replace("-", "")
        .replace("#", "")
        .lower()
        .strip()
    )
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f700-\U0001f77f"  # alchemical symbols
        "\U0001f780-\U0001f7ff"  # Geometric Shapes Extended
        "\U0001f800-\U0001f8ff"  # Supplemental Symbols and Pictographs
        "\U0001f900-\U0001f9ff"  # Supplemental Symbols and Pictographs
        "\U0001fa00-\U0001fa6f"  # Chess symbols
        "\U0001fa70-\U0001faff"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027b0"  # Dingbats
        "\U000024c2-\U0001f251"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub(r"", text)
    # 1) decompose characters into base + combining marks (NFD)
    # 2) throw away everything whose Unicode category starts with 'M' (Mark)
    # 3) re-compose what is left (NFKC keeps normal ASCII as-is)
    return unicodedata.normalize(
        "NFKC",
        unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii"),
    )


def parse_sections(data):
    """Reads Markdown in data and split in sections."""

    def add_to_section(section, line):
        if section in sections:
            if line.strip() and line.strip() != "*":
                sections[section].append(line)

    #  Process content and extract speaker notes and visual ideas
    sections = dict(
        subtitle=[],
        content=[],
        visual=[],
        notes=[],
    )
    section = "content"
    for line in data:
        processed = False
        if ":" in line:
            line_ = remove_emojis(line)
            show(line_)
            tag = line_.split(":")[0].replace(":", "").strip()
            for k in marks:
                if tag in marks[k]:
                    if k in sections:
                        section = k
                        add_to_section(section, line.split(":")[-1].strip())
                        processed = True
                    break
        if not processed:
            add_to_section(section, line)
    return sections


def clean_text(lines, remove_tags=False, remove_md=False):
    """Remove unwanted elements from a section."""
    clean = "||".join(lines)
    if remove_tags:
        clean = re.sub(r"\[[^>]+?\]", "", clean)
        clean = re.sub(r"\<[^>]+?\>", "", clean)
    if remove_md:
        clean = clean.replace("*", "").strip()
    #
    # Remove duplicated lines
    result = []
    viewed = set()
    for line in clean.split("||"):
        line_ = remove_emojis(line)
        if line_ and line_ not in viewed:
            result.append(line)
            viewed.add(line)
    return result


def polish_slide(slide: dict):
    """Final cleansing and formating."""
    for key, value in slide.items():
        if key in ["title", "content", "subtitle"]:
            slide[key] = clean_text(value, remove_tags=True)
        else:
            slide[key] = clean_text(value, remove_md=True)

    # if there are no titles, use the first line as title
    if not slide["title"]:
        if slide["content"]:
            slide["title"] = [slide["content"][0]]
            slide["content"] = slide["content"][1:]
    # if title has multiple lines, use the last ones as subtitle
    if len(slide["title"]) > 1:
        slide["subtitle"] = slide["title"][1:]
        slide["title"] = [slide["title"][0]]
    # if the content has only one line, use as subtitle
    if len(slide["content"]) == 1:
        if not slide.get("subtitle"):
            slide["subtitle"] = slide["content"]
            slide["content"] = []
    return slide


def parse_markdown(md_file_path):
    """Parse markdown and separate slide data in sections."""
    for n_slide, slide_md in enumerate(chop_slides(md_file_path), start=1):
        slide = separate_title(slide_md, n_slide)
        sections = parse_sections(slide.pop("data"))
        slide.update(sections)
        slide = polish_slide(slide)
        show(slide)
        show("-=- " * 3)
        yield slide


# Command-line interface setup
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Markdown to json")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="presentation.md",
        help="Path to the input Markdown file (default: presentation.md)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="presentation.json",
        help="Path to the output json file (default: presentation.json)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Prints the parsed slides (default: False)",
    )

    # add a template argument
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose
    slides_data = [slide for slide in parse_markdown(args.input)]
    with open(args.output, "w") as f:
        json.dump(slides_data, f, indent=4)
