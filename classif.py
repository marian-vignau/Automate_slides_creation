import os


def find_pptx_files(directory):
    """Returns a list of .pptx files in the given directory."""
    try:
        pptx_files = [f for f in os.listdir(directory) if f.endswith(".pptx")]
        return pptx_files
    except FileNotFoundError:
        print(f"Directory not found: {directory}")
        return []
    except PermissionError:
        print(f"Permission denied: {directory}")
        return []


def classify_pptx_files(file):
    if "test-" in file:
        name = file.split("-", 1)[-1]
        if file.startswith("si"):
            return name, True
        elif file.startswith("no"):
            return name, False
    return None, None


def create_script(base_dir, pptx_files):
    for file in pptx_files:
        name, clasif = classify_pptx_files(file)
        if name:
            name = name.replace(" ", r"\ ").replace("'", r"\'")
            destiny = "Incompatible"
            if clasif:
                destiny = "Compatible"
            # print(f"Classifying {file} {destiny} '{name}'")
            yield f"mv {base_dir}/to_test/{name} {base_dir}/{destiny} \n"


def main():
    # Read the TEMP environment variable
    base_dir = os.getenv("TEMP")
    # On Windows, this is usually like C:\Users\...\AppData\Local\Temp
    if not base_dir:
        print("TEMP environment variable is not set.")
        return

    temp_dir = os.path.join(base_dir, "tested")
    print(f"Searching in directory: {temp_dir}")

    # Find PowerPoint files
    pptx_files = find_pptx_files(temp_dir)

    # Output the results
    if pptx_files:
        print(f"Found {len(pptx_files)} .pptx files:")
        with open("classify.sh", "w") as f:
            for line in create_script(base_dir, pptx_files):
                f.write(line)
                print(line)
    else:
        print("No .pptx files found.")


if __name__ == "__main__":
    main()
