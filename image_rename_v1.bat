@echo off
REM Der Dateiname baut sich aus dem Datum, der Uhrzeit und der Dateigröße zusammen
REM Vor dem @ ist das Datum. Nach dem @ die Uhrzeit (von Stunden bis 1/10 Sekunden). 
REM Nach dem # sind die letzten 3 Ziffern von der Dateigröße



setlocal enabledelayedexpansion

REM Pfad zum ExifTool (Es muss sichergestellt sein, dass ExifTool bei diesem Pfad installiert ist)
set "exiftoolPath=C:\exiftool.exe"

REM Schleife durch alle Bilddateien oder Videodateien im Ordner
for %%f in (*.jpg *.jpeg *.png *.bmp *.gif *.nef *.mp4 *.mov *.mkv *.avi) do (
    REM Aufnahmedatum aus den Metadaten extrahieren
    for /f "tokens=*" %%a in ('%exiftoolPath% -CreateDate -s -s -s "%%f"') do (
        set "aufnahmedatum=%%a"
        set "aufnahmedatum=!aufnahmedatum:~0,4!-!aufnahmedatum:~5,2!-!aufnahmedatum:~8,2!@!aufnahmedatum:~11,2!!aufnahmedatum:~14,2!!aufnahmedatum:~17,2!!aufnahmedatum:~20,1!"
    )

    REM die letzten 3 Ziffern der Dateigröße extrahieren
    for %%a in ("%%f") do (
        set "fileSize=%%~za"
        set "lastThreeDigits=!fileSize:~-3!"
    )

    REM die letzten 3 Ziffern der Dateigröße dem Dateinamen hinzu
    set "neuerName=!aufnahmedatum!#!lastThreeDigits!"

    REM Datei umbennen
    echo "%%f" zu "!neuerName!%%~xf" umbenennen
    ren "%%f" "!neuerName!%%~xf"
)

echo Bilder wurden umbenannt.
pause
