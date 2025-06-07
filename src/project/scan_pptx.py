#!/usr/bin/fades
from pathlib import Path
import argparse
from process_template import Layouts  # fades python-pptx
from rich.console import Console  # fades rich
from rich.table import Table
from functools import lru_cache
import debugpy  # fades
import platform

# debugpy.listen((platform.node(), 5678))
# print(f"debugpy listening on {platform.node()}:5678", flush=True)
# debugpy.wait_for_client()


def log(msg): ...


# Your processing function — this is where you'd do something useful with each .pptx file
@lru_cache
def process_pptx_file(filepath):
    layouts = Layouts(filepath)
    stats = {" ".join(sorted(k)): len(v) for k, v in layouts.map.items()}
    stats["Total"] = len(layouts.map)
    stats["Filename"] = filepath.name
    return stats


# Function to find all .pptx files and extract metadata
def collect_pptx_metadata(start_path):
    path = Path(start_path)
    stats_lists = []

    headers = set()
    for pptx_file in path.rglob("*.pptx"):
        if pptx_file.is_file():
            stats = process_pptx_file(pptx_file)
            stats_lists.append(stats)
            headers |= set(stats.keys())

    headers = sorted(list(headers))
    del headers[headers.index("Filename")]
    del headers[headers.index("Total")]
    headers.insert(0, "Filename")
    headers.append("Total")
    return stats_lists, headers


# Display metadata in a rich table
def display_metadata_table(data, headers):
    console = Console()

    table = Table(title="PowerPoint File Metadata", header_style="bold cyan")
    for header in headers:
        if header == "Filename":
            table.add_column(header, justify="left")
        else:
            table.add_column(header, justify="right")

    for item in data:
        row = []
        for header in headers:
            if header in item:
                row.append(str(item[header]))
            else:
                row.append("")

        table.add_row(*row)

    console.print(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract and display metadata from .pptx files."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to search for .pptx files (default: current directory)",
    )
    args = parser.parse_args()

    stats_list, headers = collect_pptx_metadata(args.path)
    display_metadata_table(stats_list, headers)
