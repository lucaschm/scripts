import os

def convert_to_mp3(input_file, output_file):
    command = f'ffmpeg -i "{input_file}" -vn -acodec libmp3lame -q:a 4 "{output_file}"'
    os.system(command)

def main():
    print("This script will scan a given folder and create MP3 files in this folder based on the MP4 files in this folder." +
          "No file will be deleted, or overwritten. If an MP3 file already exists with the same name of an MP4 file, it will not be converted.")
    input_folder = input("Input folder: ")
    output_folder = input_folder

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Loop through all files in the input folder
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".mp4"):
            input_file = os.path.join(input_folder, file_name)
            output_file = os.path.join(output_folder, os.path.splitext(file_name)[0] + ".mp3")

            # Skip conversion if the output file already exists
            if os.path.exists(output_file):
                print(f"Skipped: {output_file} already exists.")
                continue

            convert_to_mp3(input_file, output_file)
            print(f"Converted: {input_file} -> {output_file}")

if __name__ == "__main__":
    main()