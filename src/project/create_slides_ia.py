#!/usr/bin/fades

from typing import Dict
from pathlib import Path
import argparse
import subprocess
import configparser
import json
import sys
import openai  # fades

# Configuration file path
CONFIG_FILE = Path("config.ini")
PROMPT_TEMPLATES_FILE = Path("prompt_templates.json")


def initialize_config() -> configparser.ConfigParser:
    """Initializes and loads the configuration file."""
    config = configparser.ConfigParser()

    # Default configuration values
    default_config = {
        "AI_SERVICE": {
            "api_key": "your_openai_api_key",
            "api_base": "https://your-qwen-endpoint.com/v1",
            "model_name": "qwen-max",
        }
    }

    # Load or create the configuration file
    if not CONFIG_FILE.exists():
        config.read_dict(default_config)
        with CONFIG_FILE.open("w") as f:
            config.write(f)
        sys.exit("No config file found. Creating one...")
    else:
        config.read(CONFIG_FILE)

    return config


def load_prompt_templates(file_path: Path = PROMPT_TEMPLATES_FILE) -> Dict[str, str]:
    """
    Loads prompt templates from a JSON file.

    Args:
        file_path (Path): Path to the file containing prompt templates.

    Returns:
        Dict[str, str]: A dictionary of prompt templates.
    """
    if not file_path.exists():
        print(f"No prompt templates found at {file_path}. Using default templates.")
        return {}

    with file_path.open("r", encoding="utf-8") as f:
        templates = json.load(f)
    print(f"Prompt templates loaded from {file_path}")
    return templates


def check_prompt_templates(file_path: Path = PROMPT_TEMPLATES_FILE) -> Dict[str, str]:
    """Stores a dictionary of prompt templates to a JSON file.

    Args:
        templates (Dict[str, str]): A dictionary of prompt templates.
        file_path (Path): Path to the file where templates will be stored."""

    # prompt_template = load_prompt_templates()
    prompt_template = dict()
    flag = False
    if not prompt_template.get("create_slide", ""):
        flag = True

        prompt_template["create_slides"] = PROMPT_TEMPLATE

    if flag:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(prompt_template, f, indent=4)
        print(f"Prompt templates saved to {file_path}")
    return prompt_template


def update_config(
    config: configparser.ConfigParser, section: str, key: str, value: str
) -> None:
    """Updates a specific key in the configuration file."""
    config[section][key] = value
    with CONFIG_FILE.open("w") as f:
        config.write(f)


def get_clipboard_content() -> str:
    """Gets the content of the clipboard using xclip."""
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError("Failed to retrieve clipboard content.")
    except FileNotFoundError:
        raise RuntimeError("xclip utility not found. Please install xclip.")


def read_file(file_path: Path) -> str:
    """Reads the content of a file."""
    return file_path.read_text(encoding="utf-8")


def write_file(file_path: Path, content: str) -> None:
    """Writes content to a file."""
    file_path.write_text(content, encoding="utf-8")


def generate_chat_completion(prompt: str, config: configparser.ConfigParser) -> str:
    """Generates a chat completion using the Qwen API."""
    client = openai.OpenAI(
        api_key=config["AI_SERVICE"]["api_key"],
        base_url=config["AI_SERVICE"]["api_base"],
    )

    response = client.chat.completions.create(
        model=config["AI_SERVICE"]["model_name"],
        messages=[
            {"role": "system", "content": "You are an experienced teacher."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content


def main() -> None:
    # Initialize configuration
    config = initialize_config()
    templates = check_prompt_templates()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Process a video transcription and creates a slide deck."
    )
    parser.add_argument(
        "--unit_plan", "-u", type=Path, required=False, help="Path to the unit plan."
    )
    parser.add_argument(
        "--file", "-f", type=Path, help="Path to the video transcription."
    )
    parser.add_argument(
        "--output", "-o", type=Path, help="Path to the slides markdown file."
    )
    args = parser.parse_args()

    input_file = Path(args.file or " ")
    if not args.unit_plan:
        unit_plan_text = get_clipboard_content()
    else:
        unit_plan = Path(args.unit_plan)
        if not unit_plan.exists():
            sys.exit(f"Error: Unit plan file not found at {unit_plan}")
        unit_plan_text = read_file(unit_plan)
    if not input_file.exists():
        sys.exit(f"Error: Input file not found at {input_file}")

    prompt_templates = load_prompt_templates()
    prompt = prompt_templates["create_slides"].format(
        unit_plan=unit_plan_text, transcription=read_file(args.file)
    )
    write_file(Path("last_prompt.txt"), prompt)
    print(f"Prompt has {len(prompt)} characters and {len(prompt.split('\n'))} lines")
    slides = generate_chat_completion(prompt, config)

    write_file(args.output, slides)


if __name__ == "__main__":
    main()

PROMPT_TEMPLATE = """
You are going to teach this content:
{unit_plan}.

Your class is 1 hour long and you are going to teach remotly.
Create a slide deck with 25 slides with short and easy sentences.
You can include some unicode emojis mixed in the content to improve the visuals.
Add some slides that are for students to practice the content.
Add speaker notes bellow each slide to include
* include the solution key for the exercises
* suggests some visuals.
* additional explanations to review and teach.

Create a markdown file and hide all the traces of your presence.

You have a video transcription as guide on how to teach this content.

{transcription} """
