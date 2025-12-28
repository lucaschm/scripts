import os

def explanation():
    explanation = """
    This script automatically transcribes multiple MP3 files. You will specify a 
    folder with these MP3 files in the next step. The script will save the transcripts 
    in a subfolder of your chosen folder. The name of this folder will be "transcripts". 

    The script will scan the "transcripts" folder for existing transcripts. MP3 files, 
    that already have a corresponding ".txt" file in the "transcripts" folder will not 
    be transcribed.

    Whisper from OpenAI is used to transcribe your audio. Whisper is a local 
    open source neural network, that uses your GPU (if you have one). Whisper 
    must be installed on this machine.


    """
    print(explanation)

# Function to check if a text file exists for a given audio file
def is_transcribed(folder_path, audio_file):
    text_file = audio_file.rsplit(".", 1)[0] + ".txt"
    is_transcribed = os.path.exists(os.path.join(folder_path, "transcripts", text_file))
    return is_transcribed

# Function to transcribe an audio file using whisper
def transcribe_audio(audio_file, output_dir):
    print(f"Transcribing {audio_file}...")
    # the whisper command you use to transcribe
    os.system(f"whisper \"{audio_file}\" --model turbo --output_dir {output_dir}")
    # Print message
    print(f"{audio_file} transcribed")

explanation()

# Folder containing audio files
folder_path = input("Input folder path: ")

# List all files in the folder
files = os.listdir(folder_path)

# Filter out only the audio files (assuming they are .mp3 files)
audio_files = [file for file in files if file.endswith(".mp3")]

# print all audiofiles
for audio_file in audio_files:
    print(audio_file)

# Iterate through each audio file
for audio_file in audio_files:
    # Check if a corresponding text file exists
    if not is_transcribed(folder_path, audio_file):
        # If not transcribed, transcribe the audio file
        transcribe_audio(os.path.join(folder_path, audio_file), os.path.join(folder_path, "transcripts"))
    else:
        print(f"'{audio_file}' is already transcribed.")

print("Transcription complete.")
input("Press Enter to close.")
