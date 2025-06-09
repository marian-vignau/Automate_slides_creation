#!/usr/bin/fades
import pprint
import re
import argparse
import markdown2  # fades
import json


marks = dict(
    separator=["---"],
    title=["title", "título"],
    visual=["visual idea", "visual", "visuals"],
    notes=[
        "speaker notes",
        "notes",
        "slide",
        "sample answer",
        "solution key",
        "notas para el presentador",
        "notas",
    ],
    content=["text", "content", "subtitle"],
)


def show(*args, **kwargs):
    if VERBOSE:
        pprint.pprint(*args, **kwargs)


def extract_data(md_file_path):
    # Parse slides from Markdown
    current_slide = {"title": [], "data": [], "index": []}
    count_backticks = 0
    n_slides = 1
    with open(md_file_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("```"):
                count_backticks += 1
                continue

            if count_backticks > 0 and count_backticks % 2 == 0:
                continue
            elif line in marks["separator"] or "---" in line:
                if current_slide:
                    yield current_slide
                current_slide = {"title": [], "data": [], "index": []}
                n_slides += 1
                continue
            line_ = line.replace("*", "").replace("`", "").replace("-", "").strip()
            if not line_:
                continue
            if line.startswith("- "):
                line = line[1:].strip()
            if line.startswith("("):
                line = line[1:].strip()
                if line.endswith(")"):
                    line = line[:-1].strip()
            if line.startswith("* "):
                line = line[1:].strip()

            if line.startswith("#"):
                for i in range(len(line)):
                    if line[i] != "#":
                        break
                title = line[i:].strip()
                if "Slide" in title:
                    pos = title.find("Slide")
                    current_slide["index"] = [title[pos : pos + len("Slide NNN")]]
                    if ":" in title[pos:]:
                        title = title.split(":")[-1].strip()
                    if " - " in title[pos:]:
                        title = title.split(" – ")[-1].strip()
                elif not current_slide["index"]:
                    current_slide["index"] = [f"Slide {n_slides}"]
                current_slide["title"].append(title)
            elif current_slide is not None:
                current_slide["data"].append(line)

        if current_slide is not None:
            yield current_slide


def clean_text(lines, remove_tags=True, remove_md=True):
    clean = "||".join(lines)
    if remove_tags:
        clean = re.sub(r"\[[^>]+?\]", "", clean)
        clean = re.sub(r"\<[^>]+?\>", "", clean)
    if remove_md:
        clean = clean.replace("*", "").strip()
    result = []
    viewed = set()
    for line in clean.split("||"):
        line_ = (
            line.replace("*", "")
            .replace("`", "")
            .replace("-", "")
            .replace("#", "")
            .lower()
            .strip()
        )
        if line_ and line_ not in viewed:
            result.append(line)
            viewed.add(line)
    return result


def parse_markdown(md_file_path):
    """Reads Markdown file and parses it."""

    def add_to_section(section, line):
        if section in sections:
            if line.strip() and line.strip() != "*":
                sections[section].append(line)

    #  Process content and extract speaker notes and visual ideas
    for slide in extract_data(md_file_path):
        sections = dict(
            index=slide["index"],
            title=slide["title"],
            subtitle=[],
            content=[],
            visual=[],
            notes=[],
        )
        section = "content"
        for line in slide["data"]:
            processed = False
            line_ = line.lower().replace("*", "").strip()
            if ":" in line_:
                tag = line_.split(":")[0]

                for k in marks:
                    if tag in marks[k]:
                        if k in sections:
                            section = k
                            add_to_section(section, line.split(":")[-1].strip())
                            processed = True
                        break
            if not processed:
                add_to_section(section, line)

        for key, value in sections.items():
            if key in ["title", "content"]:
                sections[key] = clean_text(value, remove_md=False)
            else:
                sections[key] = clean_text(value, remove_tags=False)

        if not sections["title"]:
            if sections["content"]:
                sections["title"] = sections["content"][0]
                sections["content"] = sections["content"][1:]
        if len(sections["title"]) > 1:
            sections["subtitle"] = sections["title"][1:]
            sections["title"] = [sections["title"][0]]
        if len(sections["content"]) == 1:
            if not sections.get("subtitle"):
                sections["subtitle"] = sections["content"]
                sections["content"] = []

        show(sections)
        show(slide.pop("data"))
        show("---")

        yield sections


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
        help="Path to the output json file (default: presentation.pptx)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        type=bool,
        default=False,
        help="Prints the parsed slides (default: False)",
    )

    # add a template argument
    args = parser.parse_args()

    global VERBOSE
    VERBOSE = args.verbose
    slides_data = [slide for slide in parse_markdown(args.input)]
    with open(args.output, "w") as f:
        json.dump(slides_data, f, indent=4)
