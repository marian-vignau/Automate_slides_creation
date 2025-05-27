import argparse
import sys
import re
from pathlib import Path


def filter_lines(input_file):
    with input_file.open("r") as f:
        before = ""
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            elif " --> " in line:
                continue
            elif line == before:
                continue
            else:
                yield line
                before = line


def process_lines(input_file):
    before = ""
    for line in filter_lines(input_file):
        plain_text = re.sub("<[^>]+>", " ", line)
        plain_text = re.sub(" +", " ", plain_text)
        plain_text = plain_text.strip()
        if plain_text != before:
            yield plain_text
            before = plain_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PowerPoint Presentation"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="Path to the input file in vtt format",
    )
    """
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default="presentation.pptx",
        help="Path to the output file.",
    )
    parser.add_argument(
        "--template",
        "-t",
        type=str,
        default="",
        help="Path to the template PowerPoint file (default: None)",
    )
    """
    # add a template argument
    args = parser.parse_args()
    if not Path(args.input).exists:
        sys.exit(f"Input file {args.input} does not exist")
    for line in process_lines(args.input):
        print(line)
