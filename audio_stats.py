import os
import re
import logging
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
from pydub import AudioSegment

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(levelname)s - %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Regular expression to match filenames of the format YYYY-MM-DD hh.mm.ss
filename_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2}) (\d{2})\.(\d{2})\.(\d{2})')

def get_audio_duration(file_path):
    """Returns the duration of the audio file in seconds."""
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000  # Convert milliseconds to seconds

def parse_filename(file_name):
    """Extract the datetime from the filename based on the pattern."""
    match = filename_pattern.match(file_name)
    if match:
        date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}:{match.group(6)}"
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return None

def collect_audio_data(folder_path):
    """Collects the audio duration data from the folder."""
    audio_data = defaultdict(list)  # Dictionary to store durations for each day

    logging.info(f"Starting to collect audio data from folder: {folder_path}")

    for file_name in os.listdir(folder_path):
        if filename_pattern.match(file_name):
            file_path = os.path.join(folder_path, file_name)

            # Parse the recording time from the filename
            recording_time = parse_filename(file_name)
            if not recording_time:
                logging.warning(f"Could not parse recording time from filename: {file_name}")
                continue

            try:
                # Get the duration of the audio file
                duration = get_audio_duration(file_path)

                # Log information for each audio file in one line
                logging.info(f"File: {file_name} | Time: {recording_time} | Duration: {duration:.2f} seconds")
                
                # Add the duration to the corresponding date
                audio_data[recording_time].append(duration)

            except Exception as e:
                logging.error(f"Error processing file: {file_name} | Error: {e}")

    logging.info("Finished collecting audio data.")
    return audio_data

def create_monthly_plots(audio_data):
    """Create a beam diagram (bar plot) for each month."""
    monthly_data = defaultdict(lambda: defaultdict(list))  # Nested dictionary for year-month -> day -> durations

    logging.info("Starting to create monthly plots...")

    # Organize the data by year-month -> day
    for timestamp, durations in audio_data.items():
        year_month = timestamp.strftime('%Y-%m')
        day = timestamp.day
        monthly_data[year_month][day].extend(durations)

    # Plot each month's data
    for year_month, daily_durations in sorted(monthly_data.items()):
        days = sorted(daily_durations.keys())
        max_day = max(days)  # Determine the number of days in the month
        day_durations = [sum(daily_durations[day]) for day in days]  # Sum durations for each day

        logging.info(f"Creating plot for {year_month} with data for {len(days)} days.")

        # Plot the beam diagram
        plt.figure(figsize=(10, 6))
        plt.bar(days, day_durations, color='blue')
        plt.title(f'Audio Recording Time for {year_month}')
        plt.xlabel('Day of the Month')
        plt.ylabel('Total Recording Time (seconds)')
        plt.ylim(0, max(max(day_durations), 1))  # Ensure all plots have the same y-axis scale
        plt.xticks(range(1, max_day + 1))
        plt.grid(True)

        # Save the plot for this month
        plot_filename = f'audio_recording_{year_month}.png'
        plt.savefig(plot_filename)
        logging.info(f"Saved plot: {plot_filename}")
        plt.close()

    logging.info("Finished creating all monthly plots.")

# Main execution
if __name__ == "__main__":
    folder_path = os.getcwd()  # Use current working directory
    logging.info(f"Script started. Looking for audio files in folder: {folder_path}")
    
    audio_data = collect_audio_data(folder_path)
    create_monthly_plots(audio_data)
    
    logging.info("Script finished successfully.")
