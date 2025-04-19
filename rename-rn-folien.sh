#!/bin/bash
# a script that renames EVERY file in the folder with the following rule: 
# first 2 characters are "RN" and second 2 charcters are taken from the first 2 characters of the original filename



while true; do
    read -p "Bist du sicher, dass du dieses Skript ausführen willst. Es benennt Dateien um (dabei können auch Dateien verloren gehen). Bitte lies erst den Quelltext, bevor du fortfährst. (Antworte mit y wenn du das Skript ausführen willst) " yn
    case $yn in
        [Yy]* ) break;;
        * ) exit;;
    esac
done

# Set the directory where your files are located
folder_path="/mnt/c/Users/jalit/Desktop/rnpdf"

# Iterate through all files in the directory
for filename in "$folder_path"/*; do
    if [ -f "$filename" ]; then
        # Extract the first two characters of the original name
        file_basename=$(basename "$filename")
		file_extension=".${filename##*.}"
        first_two_chars="${file_basename:0:2}"
        new_name="RN$first_two_chars$file_extension"
        new_path="$folder_path/$new_name"
        mv "$filename" "$new_path"
        echo "Renamed: $file_basename to $new_name"
    fi
done
