function process_templates
    # Check if folder exists

    if not test -d $TEMP/to_test/
        echo "Error: Folder '$folder' does not exist."
        return 1
    end

    # Loop through all files in the folder
    for file in $TEMP/to_test/*.pptx
        if test -f $file
            echo "Processing file: $file"
            set output $TEMP/tested/test-(basename $file)
            # Replace the following line with your actual command
            # For example, let's just print the file content
            echo $output
            python src/create_w_template.py work/u$UNIT-slides.json $file $output
        end
    end
end
