import argparse
import re
import sys
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
    "Replace some HTML tags and remove empty lines."
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
        description="Cleans a VTT file for use in IA prompting"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="Path to the input file in vtt format",
    )
    args = parser.parse_args()
    if not Path(args.input).exists:
        sys.exit(f"Input file {args.input} does not exist")
    preamble = {"WEBVTT", "Kind:", "Language:"}
    preamble_lines = 0
    for line in process_lines(args.input):
        if preamble_lines < len(preamble):
            if not any(line.startswith(p) for p in preamble):
                sys.exit(f"Input file {args.input} is not a vtt file {line}")
            preamble_lines += 1
        else:
            print(line)
