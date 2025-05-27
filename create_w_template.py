#!/usr/bin/fades
import json
from pathlib import Path
import sys

from pptx import Presentation  # fades python-pptx
from pptx.util import Inches
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE


def map_layouts(prs):
    available_layouts = {}
    for layout in prs.slide_layouts:
        name = layout.name
        available_layouts[name] = [name]
        available_layouts[name].append(name.replace("_", " "))
        available_layouts[name].append(name.lower().replace("_", " "))
    map = {"Title Slide": None, "Title and Content": None}
    for layout, values in available_layouts.items():
        for key in map:
            if key.lower() in values:
                map[key] = layout
    if not map["Title Slide"]:
        for layout, values in available_layouts.items():
            for alternative in ["title only", "title"]:
                if alternative.lower() in values:
                    map["Title Slide"] = layout
                    break
    if not map["Title and Content"]:
        for layout, values in available_layouts.items():
            for alternative in ["content", "object", "blank"]:
                if alternative.lower() in values:
                    map["Title and Content"] = layout
                    break

    if not map["Title Slide"] or not map["Title and Content"]:
        sys.exit("No suitable layouts found")
    return map


def create_presentation(template_path, json_path, output_path):
    # Load the template presentation
    prs = Presentation(template_path)
    map = map_layouts(prs)

    if len(prs.slides) > 0:
        print("Warning: Template already contains slides. I can't remove slides...")

    # Load the JSON data
    with open(json_path, "r") as f:
        slides_data = json.load(f)

    for slide_data in slides_data:
        # Determine slide layout
        title_parts = slide_data.get("title", [])
        if not title_parts:
            continue

        # Choose layout based on title (assuming first slide is title slide)
        if len(title_parts) > 1 and "Title Slide" in title_parts[1]:
            layout = prs.slide_layouts.get_by_name(map["Title Slide"])
        else:
            layout = prs.slide_layouts.get_by_name(map["Title and Content"])

        # Add slide
        slide = prs.slides.add_slide(layout)

        # Set title and subtitle
        title_shape = slide.shapes.title
        title_shape.text = title_parts[0].lstrip("# ").strip()

        if layout.name == map["Title Slide"] and len(title_parts) > 1:
            subtitle_placeholder = slide.placeholders[1]
            subtitle_placeholder.text = title_parts[1]

        # Add content (bullet points)
        content = slide_data.get("content", [])
        if content:
            content_placeholder = None
            for shape in slide.shapes:
                if shape.has_text_frame and shape.is_placeholder:
                    if shape.placeholder_format.idx == 1:  # Content placeholder
                        content_placeholder = shape
                        break

            if content_placeholder:
                text_frame = content_placeholder.text_frame
                text_frame.clear()

                for line in content:
                    line = line.strip()
                    p = text_frame.add_paragraph()
                    if line.startswith("-"):
                        text = line[1:].strip()  # Remove '- '
                        p.level = 0
                    else:
                        text = line
                    bold = False
                    for clean_text in text.split("**"):
                        # Basic markdown bold handling
                        run = p.add_run()
                        run.text = clean_text
                        run.font.bold = bold
                        bold = not bold

        notes = slide_data.get("notes", [])
        # Add images (if any)
        visuals = slide_data.get("visual", [])
        if visuals and len(slide.shapes) > 0:
            # Add image to the right of content (example placement)
            left = Inches(5)
            top = Inches(1.5)
            try:
                slide.shapes.add_picture(visuals[0], left, top, height=Inches(3))
            except Exception as e:
                notes.extend(["Visuals:"] + visuals)
                print(f"Error adding image: {e}")

        # Add speaker notes
        if notes:
            notes_slide = slide.notes_slide
            notes_slide.notes_text_frame.text = "\n".join(notes)

    # Save the presentation
    prs.save(output_path)


# Usage
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python create_w_template.py <source.json> <template.potx> <output.pptx>"
        )
        sys.exit(1)

    source_json = sys.argv[1]
    template_ppt = sys.argv[2]
    output_ppt = sys.argv[3]
    fn = Path(template_ppt).expanduser().resolve()
    if not fn.exists():
        sys.exit(f"Template file not found: {template_ppt}")

    create_presentation(
        template_path=str(fn), json_path=source_json, output_path=output_ppt
    )
    print(f"Template applied and saved to: {output_ppt}")
