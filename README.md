# Automate the presentations

## Why?

I found a playlist in youtube with the same syllabus of the course I'm giving.

Then I downloaded the video transcriptions, chopped the syllabus of my course in a file per unit and used ia to create the presentations.

## Preparations

The ia prompt uses unit plan, these are a simple and short schema for the class objectives.
This information should be stored in the input folder, in the UNIT-unit_plan.txt files.

The shell script will create the directory structure and download the video transcriptions from the youtube playlist.

`download.sh 'https://www.youtube.com/watch?v=tsHiZScKcb0&list=PL0DeyZPeOBfwqC56kOhDeWbJ8anp0XtNB'`

## How to use this scripts

For convenience, I'll set a environment variable with the unit number.

`set -x UNIT 12`

**Note**: All the python scripts are prepared for be used with fades and the shell scripts are prepared for be used with fish.

Install fades 
`sudo apt install fades`

### clean_vtt

This is needed to avoid junk data into the transcripts.

`fades clean_vtt.py -i input/Blue\ Interchange\ UNIT\ $UNIT.en.vtt > work/u$UNIT-transcript.txt`

### create_slides_ia

This creates the slides using AI. This uses openai library to access qwen models.
You need to setup your access keys to use this. The access keys must be added into the config.ini file.

`fades create_slides_ia.py --file work/u$UNIT-transcript.txt --output work/u$UNIT-slides.md --unit_plan input/u$UNIT-unit_plan.txt`

### md2json

After creating the slides design, this markdown must be parsed into json to be used by the presentation tool.

`fades md2json.py -i work/u$UNIT-slides.md -o work/u$UNIT-slides.json -v True` 

### create_w_template

This final script uses the json and a powerpoint template to create the final presentation in pptx format.

`fades create_w_template.py work/u$UNIT-slides.json ~/Templates/Story.pptx work/u$UNIT-slides.pptx`

Finally, the presentation is converted to odp and added to the results folder.

`libreoffice --headless --convert-to odp work/u$UNIT-slides.pptx --outdir results/`


