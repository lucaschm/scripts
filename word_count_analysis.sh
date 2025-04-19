#!/bin/bash
# zählt am meisten verwendete Wörter aus data.txt und listet diese in einer Datei (dataout.txt) auf.

while true; do
    read -p "Bist du sicher, dass du dieses Skript ausführen willst. Es liest und schreibt Dateien. (Antworte mit y wenn du das Skript ausführen willst) " yn
    case $yn in
        [Yy]* ) break;;
        * ) exit;;
    esac
done


sed 's/\W/\n/g' data.txt | 
sed '/^$/d' | 
tr '[:upper:]' '[:lower:]' | 
sort | 
uniq -c | 
sort > dataout.txt
