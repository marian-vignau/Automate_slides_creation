#!/usr/bin/fades
import pprint
import re
import argparse
import markdown2  # fades
import json


marks = dict(
    separator=["---"],
    title=["title"],
    visual=["visual idea", "visual", "visuals"],
    notes=["speaker notes", "notes", "slide", "sample answer", "solution key"],
    content=["text", "content", "subtitle"],
)


def show(*args, **kwargs):
    if VERBOSE:
        pprint.pprint(*args, **kwargs)


def processed_content(data: list) -> str:
    html_content = markdown2.markdown(
        "\n".join(x.replace("*", "").strip() for x in data if x.strip())
    )
    plain_text = re.sub("<[^>]+>", "", html_content)
    return plain_text.replace("*", "")


def extract_data(md_file_path):
    # Parse slides from Markdown
    current_slide = {"title": [], "data": []}
    count_backticks = 0
    with open(md_file_path, "r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("```"):
                count_backticks += 1
                continue
            if count_backticks > 0 and count_backticks % 2 == 0:
                continue
            if line.startswith("*"):
                line = line[1:].strip()
            if line.startswith("("):
                line = line[1:].strip()
                if line.endswith(")"):
                    line = line[:-1].strip()
            if not line:
                continue
            elif line in marks["separator"]:
                if current_slide:
                    yield current_slide
                current_slide = {"title": [], "data": []}
            elif line.startswith("#"):
                for i in range(len(line)):
                    if line[i] != "#":
                        break
                title = line[i:].strip()
                if "Slide" in title and ":" in title:
                    title = title.split(":")[-1].strip()
                if "Slide" in title and " – " in title:
                    title = title.split(" – ")[-1].strip()
                current_slide["title"].append(title)
            elif current_slide is not None:
                if line and line != "*":
                    current_slide["data"].append(line)

        if current_slide is not None:
            yield current_slide


def parse_markdown(md_file_path):
    """Reads Markdown file and parses it."""

    def add_to_section(section, line):
        if section in sections:
            if line.strip() and line.strip() != "*":
                sections[section].append(line)

    #  Process content and extract speaker notes and visual ideas
    for slide in extract_data(md_file_path):
        sections = dict(notes=[], content=[], visual=[], title=slide["title"])
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
        if not sections["title"]:
            if sections["content"]:
                sections["title"] = sections["content"][0]
                sections["content"] = sections["content"][1:]
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
