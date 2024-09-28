import os
import re
import logging
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
import calendar

# Configure logging without timestamps
logging.basicConfig(
    level=logging.INFO, 
    format='%(levelname)s - %(message)s'
)

# Regular expression to match filenames of the format YYYY-MM-DD hh.mm.ss
filename_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2}) (\d{2})\.(\d{2})\.(\d{2})')

def get_audio_duration(file_path):
    """Returns the duration of the audio file in seconds, or None if there's an error."""
    try:
        audio = AudioSegment.from_file(file_path)
        return len(audio) / 1000  # Convert milliseconds to seconds
    except CouldntDecodeError:
        logging.error(f"Could not decode audio file: {file_path}")
        return None
    except Exception as e:
        logging.error(f"Error reading audio file: {file_path} | Error: {e}")
        return None

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

            # Get the duration of the audio file
            duration = get_audio_duration(file_path)
            if duration is not None:
                # Log information for each audio file in one line
                logging.info(f"File: {file_name} | Time: {recording_time} | Duration: {duration:.2f} seconds")
                # Add the duration to the corresponding date
                audio_data[recording_time.date()].append(duration)

    logging.info("Finished collecting audio data.")
    return audio_data

def create_monthly_plots(audio_data):
    """Create a beam diagram (bar plot) for each month."""
    monthly_data = defaultdict(lambda: defaultdict(list))  # Nested dictionary for year-month -> day -> durations

    logging.info("Starting to create monthly plots...")

    # Organize the data by year-month -> day
    for date, durations in audio_data.items():
        year_month = date.strftime('%Y-%m')
        day = date.day
        monthly_data[year_month][day].extend(durations)

    # Determine the global y-axis scale (maximum duration in minutes)
    max_duration_seconds = max(
        (sum(durations) for daily_durations in monthly_data.values() for durations in daily_durations.values()), 
        default=0
    )
    max_duration_minutes = max_duration_seconds / 60 if max_duration_seconds > 0 else 1  # Avoid zero y-axis scaling

    # Define colors for multiple segments in bars
    colors = plt.cm.get_cmap('tab20', 20)  # Colormap to use different colors for up to 20 segments

    # Plot each month's data
    for year_month, daily_durations in sorted(monthly_data.items()):
        days_in_month = calendar.monthrange(int(year_month[:4]), int(year_month[5:]))[1]
        days = list(range(1, days_in_month + 1))  # Ensure all days of the month are included
        all_durations = [daily_durations.get(day, []) for day in days]  # Fill missing days with empty lists

        logging.info(f"Creating plot for {year_month} with data for {len(days)} days.")

        # Plot the beam diagram with segmented bars
        plt.figure(figsize=(10, 6))
        bottom = [0] * days_in_month  # To stack the segments on top of each other

        for i in range(max(len(durations) for durations in all_durations)):  # Number of stacked segments
            segment_durations = [
                (durations[i] / 60 if i < len(durations) else 0) for durations in all_durations
            ]  # Convert to minutes, handle missing segments
            plt.bar(days, segment_durations, bottom=bottom, color=colors(i), label=f'Audio {i + 1}')
            bottom = [b + d for b, d in zip(bottom, segment_durations)]

        # Ensure all plots have the same y-axis scale
        plt.ylim(0, max_duration_minutes)

        plt.title(f'Audio Recording Time for {year_month}')
        plt.xlabel('Day of the Month')
        plt.ylabel('Total Recording Time (minutes)')
        plt.xticks(range(1, days_in_month + 1))  # Ensure all days of the month are visible
        plt.grid(True)

        # Add a legend for the segments if there are multiple audios on a day
        if any(len(durations) > 1 for durations in all_durations):
            legend_elements = [Patch(facecolor=colors(i), label=f'Audio {i+1}') for i in range(max(len(d) for d in all_durations))]
            plt.legend(handles=legend_elements, title="Segments")

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
