import os
from mutagen.flac import FLAC

def extract_album_art(input_dir, output_dir=None):
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".flac"):
                flac_path = os.path.join(root, file)

                try:
                    audio = FLAC(flac_path)

                    if not audio.pictures:
                        print(f"No album art: {flac_path}")
                        continue

                    for i, picture in enumerate(audio.pictures):
                        # Determine extension
                        ext = "jpg"
                        if picture.mime == "image/png":
                            ext = "png"

                        # Build output filename
                        base_name = os.path.splitext(file)[0]
                        image_name = f"{base_name}_cover_{i}.{ext}"

                        if output_dir:
                            save_path = os.path.join(output_dir, image_name)
                        else:
                            save_path = os.path.join(root, image_name)

                        with open(save_path, "wb") as img:
                            img.write(picture.data)

                        print(f"Extracted: {save_path}")

                except Exception as e:
                    print(f"Error processing {flac_path}: {e}")

if __name__ == "__main__":
    input_folder = input("Enter path to your FLAC collection: ").strip()
    output_folder = input("Enter output folder (leave empty to save next to files): ").strip()

    if not output_folder:
        output_folder = None

    extract_album_art(input_folder, output_folder)