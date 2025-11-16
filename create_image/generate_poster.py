import json
import requests
from PIL import Image, ImageOps, ImageDraw, ImageFont
from io import BytesIO
from datetime import datetime
import os
from datetime import timedelta
import string

# Function to download an image from a URL
def download_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        raise Exception(f"Failed to download image from {url}")


def convert_to_12hr_format(time_obj):
    """Convert a datetime object to 12-hour time format."""
    return time_obj.strftime('%I:%M %p')  # Convert to 12-hour format with AM/PM

def is_british_summer_time(date):
    """Check if the given date is in British Summer Time."""
    # Last Sunday in March
    last_sunday_march = datetime(date.year, 3, 31) - timedelta(days=datetime(date.year, 3, 31).weekday() + 1)
    # Last Sunday in October
    last_sunday_october = datetime(date.year, 10, 31) - timedelta(days=datetime(date.year, 10, 31).weekday() + 1)

    return last_sunday_march <= date <= last_sunday_october

def convert_time_zones(utc_time_str):
    try:
        # Convert string to datetime object assuming input is in UTC
        utc_time = datetime.strptime(utc_time_str, '%H:%M:%S')

        # Get the current date to check for DST
        current_date = datetime.now()

        # Determine if the current date is in British Summer Time
        if is_british_summer_time(current_date):
            # British Summer Time (UTC+1)
            uk_time = utc_time + timedelta(hours=1)
        else:
            # Greenwich Mean Time (UTC+0)
            uk_time = utc_time

        # Convert both times to 12-hour format
        utc_time_formatted = convert_to_12hr_format(utc_time)
        uk_time_formatted = convert_to_12hr_format(uk_time)

        return utc_time_formatted, uk_time_formatted

    except ValueError:
        return None, None  # Return None if the input time format is invalid


def custom_sort(source):
    # Prioritize all United Kingdom and United States entries
    if source.startswith("United Kingdom"):
        return (0, source)
    elif source.startswith("United States"):
        return (1, source)
    # Sort all other sources alphabetically
    return (2, source)


def create_first_image(event_name, away_team_logo=None, home_team_logo=None, venue=None, date_event=None, local_time_formatted=None, utc_time_formatted=None):
    width, height = 1024, 341  # New size for the first image
    background = Image.new("RGB", (width, height), (255, 255, 255))  # White background

    # Resize logos to smaller size if they are provided
    if away_team_logo:
        away_team_logo = ImageOps.contain(away_team_logo, (200, 200))
    if home_team_logo:
        home_team_logo = ImageOps.contain(home_team_logo, (200, 200))

    # Create ImageDraw object for drawing text and underline
    draw = ImageDraw.Draw(background)

    # Load the Gagalin font (.otf) and adjust font size dynamically for the header to fit the width
    try:
        font_path = "Gagalin.otf"
        max_font_size = 100  # Starting font size to try
        min_font_size = 20  # Minimum font size if the text is too wide
        font = ImageFont.truetype(font_path, max_font_size)
        
        while draw.textbbox((0, 0), event_name, font=font)[2] > width - 40 and max_font_size > min_font_size:
            max_font_size -= 5  # Reduce font size gradually
            font = ImageFont.truetype(font_path, max_font_size)
        
        sub_font = ImageFont.truetype(font_path, 40)  # Smaller font size for local time and UTC
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font if the custom font is not available
        sub_font = ImageFont.load_default()  # Fallback for smaller text

    # Calculate text size and position for the header at the top
    header_bbox = draw.textbbox((0, 0), event_name, font=font)
    header_width = header_bbox[2] - header_bbox[0]
    header_position = ((width - header_width) // 2, 10)  # Set y-position for the header

    # Add header text at the top
    draw.text(header_position, event_name, font=font, fill="black")

    # Draw underline below the event name
    underline_start = (header_position[0], header_position[1] + header_bbox[3] + 5)  # 5 pixels below text
    underline_end = (header_position[0] + header_width, header_position[1] + header_bbox[3] + 5)  # Same y, full width
    draw.line([underline_start, underline_end], fill="black", width=5)  # Thickness of the underline

    # Dynamically adjust venue text size to fit
    max_venue_font_size = 40
    venue_font = ImageFont.truetype(font_path, max_venue_font_size) if venue else None

    # Define a safe area for the text to avoid overlapping with logos
    safe_margin = 260  # The space taken by the logos + some padding
    safe_width = width - 2 * safe_margin  # Reduced width to fit within the logos
    if venue:
        while draw.textbbox((0, 0), f"Venue: {venue}", font=venue_font)[2] > safe_width and max_venue_font_size > 20:
            max_venue_font_size -= 2
            venue_font = ImageFont.truetype(font_path, max_venue_font_size)

    # Calculate positions for venue, date_event, local time, and UTC time with equal spacing
    vertical_start = 150  # Start further down
    line_spacing = 50  # Equal spacing between each line

    # Add the venue text if available
    if venue:
        venue_text = f"Venue: {venue}"
        venue_bbox = draw.textbbox((0, 0), venue_text, font=venue_font)
        venue_width = venue_bbox[2] - venue_bbox[0]
        venue_position = ((width - venue_width) // 2, vertical_start)
        draw.text(venue_position, venue_text, font=venue_font, fill="black")
        vertical_start += line_spacing

    # Add the date_event text if available
    if date_event:
        date_event_text = f"Date: {date_event}"
        date_event_bbox = draw.textbbox((0, 0), date_event_text, font=sub_font)
        date_event_width = date_event_bbox[2] - date_event_bbox[0]
        date_event_position = ((width - date_event_width) // 2, vertical_start)
        draw.text(date_event_position, date_event_text, font=sub_font, fill="black")
        vertical_start += line_spacing

    # Add the local time text if available
    if local_time_formatted:
        local_time_text = f"UK Time: {local_time_formatted}"
        local_time_bbox = draw.textbbox((0, 0), local_time_text, font=sub_font)
        local_time_width = local_time_bbox[2] - local_time_bbox[0]
        local_time_position = ((width - local_time_width) // 2, vertical_start)
        draw.text(local_time_position, local_time_text, font=sub_font, fill="black")
        vertical_start += line_spacing

    # Add the UTC time text if available
    if utc_time_formatted:
        utc_time_text = f"UTC Time: {utc_time_formatted}"
        utc_time_bbox = draw.textbbox((0, 0), utc_time_text, font=sub_font)
        utc_time_width = utc_time_bbox[2] - utc_time_bbox[0]
        utc_time_position = ((width - utc_time_width) // 2, vertical_start)
        draw.text(utc_time_position, utc_time_text, font=sub_font, fill="black")

    # Paste the logos closer to the edges, now move them to the bottom if provided
    logo_y_position = height - 210  # Position logos 10 pixels from the bottom
    
    if away_team_logo:
        if away_team_logo.mode in ('RGBA', 'LA'):
            background.paste(away_team_logo, (10, logo_y_position), away_team_logo)  # Left logo moved to the bottom
        else:
            background.paste(away_team_logo, (10, logo_y_position))  # No mask needed

    if home_team_logo:
        if home_team_logo.mode in ('RGBA', 'LA'):
            background.paste(home_team_logo, (width - 210, logo_y_position), home_team_logo)  # Right logo moved to the bottom
        else:
            background.paste(home_team_logo, (width - 210, logo_y_position))  # No mask needed

    # Save the resulting image
    background.save(f"{event_name}_first.png")


def create_second_image(event_name, sources):
    # Constants
    width = 1024  # Fixed width
    min_height = 341  # Minimum height
    default_line_height = 50  # Default line height
    max_sources_per_image = 10  # Max number of sources per image, used to calculate number of images

    def wrap_text(text, font, max_width, draw):
        lines = []
        words = text.split(' ')
        current_line = []
        for word in words:
            current_line.append(word)
            line_text = ' '.join(current_line)
            if draw.textbbox((0, 0), line_text, font=font)[2] > max_width:
                current_line.pop()  # Remove the last word and add the line
                lines.append(' '.join(current_line))
                current_line = [word]  # Start a new line with the last word
        lines.append(' '.join(current_line))  # Add the last line
        return lines

    def add_spaces(sources):
        # Add spaces between country and channel name for formatting
        formatted_sources = []
        for source in sources:
            if ':' in source:
                country, channel = source.split(':', 1)
                formatted_source = f"{country}:  {channel.strip()}"
                formatted_sources.append(formatted_source)
            else:
                formatted_sources.append(source)
        return formatted_sources

    def calculate_image_height(sources, font, draw):
        # Measure total height required for all sources
        total_height = 0
        for source in sources:
            wrapped_lines = wrap_text(source.strip(), font, width - 40, draw)
            total_height += default_line_height * len(wrapped_lines)  # Account for each wrapped line
        return max(min_height, total_height + 40)  # Add padding and ensure height is at least the minimum

    # Format sources with spaces
    sources.sort(key=custom_sort)
    sources = add_spaces(sources)

    # Load a font (adjust size dynamically based on the number of sources)
    try:
        font = ImageFont.truetype("OpenSans-Bold.otf", 40)  # Use a smaller font size for pagination
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font if the custom font is not available

    # Create a dummy image to initialize the draw object
    dummy_image = Image.new("RGB", (width, 1), (255, 255, 255))
    draw = ImageDraw.Draw(dummy_image)

    # Calculate the number of images needed
    num_images = -(-len(sources) // max_sources_per_image)  # Ceiling division

    # Calculate how many sources per image (equally distributed)
    sources_per_image = len(sources) // num_images
    extra_sources = len(sources) % num_images  # Sources that couldn't be divided equally

    # Loop over each image
    current_index = 0
    for i in range(num_images):
        # Calculate the number of sources for this image
        num_sources_this_image = sources_per_image + (1 if i < extra_sources else 0)

        # Get the chunk of sources for the current image
        chunk_sources = sources[current_index:current_index + num_sources_this_image]
        current_index += num_sources_this_image

        # Create a blank image with the appropriate height
        height = calculate_image_height(chunk_sources, font, draw)
        background = Image.new("RGB", (width, height), (255, 255, 255))  # White background
        draw = ImageDraw.Draw(background)

        # Calculate total height of all text lines
        total_text_height = 0
        for source in chunk_sources:
            total_text_height += default_line_height

        # Centering sources vertically
        vertical_position = (height - total_text_height) // 2  # Center the text block vertically

        for source in chunk_sources:
            # Treat the entire line (country + channel) as a single block
            line_bbox = draw.textbbox((0, 0), source.strip(), font=font)
            line_width = line_bbox[2] - line_bbox[0]

            # Center-align the entire line (country + channel)
            draw.text(((width - line_width) // 2, vertical_position), source.strip(), font=font, fill="black")

            vertical_position += default_line_height  # Move to the next line

        # Save the resulting image
        save_path = f"{event_name}_second_{i + 1}.png"
        background.save(save_path)


def create_third_image(event_name, league_banner_url):
    # Download the banner image
    banner_image = download_image(league_banner_url)

    # Resize the banner to fit the width of the final image while maintaining aspect ratio
    banner_width = 1024  # Width of the merged images
    banner_height = int(banner_image.height * (banner_width / banner_image.width))
    banner_image = banner_image.resize((banner_width, banner_height), Image.LANCZOS)  # Use Image.LANCZOS for high-quality resizing

    # Create a white background for the third image (banner area)
    width, height = 1024, banner_height  # Adjust height based on banner size
    background = Image.new("RGB", (width, height), (255, 255, 255))  # White background

    # Paste the banner in the center of the third image
    background.paste(banner_image, (0, 0))  # Banner image now fills the entire width

    # Save the third image as event_name_third.png
    background.save(f"{event_name}_third.png")


def merge_images(event_name, sport, league):
    # File paths for images
    first_image_path = f"{event_name}_first.png"
    third_image_path = f"{event_name}_third.png"

    # Get today's date using the existing get_today_date function
    today_date = get_today_date()

    # Create directory structure 'date/sport/league'
    save_dir = os.path.join(today_date, sport, league)
    os.makedirs(save_dir, exist_ok=True)  # Create directories if they don't exist

    # Check if the first image exists
    if os.path.isfile(first_image_path):
        first_image = Image.open(first_image_path)
    else:
        print(f"First image not found: {first_image_path}")
        first_image = None

    # Check if the third image exists
    if os.path.isfile(third_image_path):
        third_image = Image.open(third_image_path)
    else:
        print(f"Third image not found: {third_image_path}")
        third_image = None

    # List all second images
    second_image_files = [f for f in os.listdir() if f.startswith(f"{event_name}_second_") and f.endswith(".png")]
    
    if not second_image_files:
        print(f"No second images found for event: {event_name}")
        return

    second_image_files.sort()  # Optional: sort files if needed

    # Process each second image
    for idx, second_image_file in enumerate(second_image_files):
        second_image_path = os.path.join(os.getcwd(), second_image_file)
        if not os.path.isfile(second_image_path):
            print(f"Second image file not found: {second_image_path}")
            continue

        second_image = Image.open(second_image_path)

        # Determine total height based on available images
        total_height = 0
        if first_image:
            total_height += first_image.height
        total_height += second_image.height
        if third_image:
            total_height += third_image.height

        # Determine width based on the widest image
        width = 0
        if first_image:
            width = max(width, first_image.width)
        width = max(width, second_image.width)
        if third_image:
            width = max(width, third_image.width)
        
        # Create a new blank image to hold the merged result
        merged_image = Image.new("RGB", (width, total_height))

        current_height = 0
        
        # Paste the first image if available
        if first_image:
            merged_image.paste(first_image, (0, current_height))
            current_height += first_image.height
        
        # Paste the second image
        merged_image.paste(second_image, (0, current_height))
        current_height += second_image.height
        
        # Paste the third image if available
        if third_image:
            merged_image.paste(third_image, (0, current_height))

        # Save the merged image in the created directory
        save_path = os.path.join(save_dir, f"{event_name}_poster_{idx + 1}.png")
        merged_image.save(save_path)
        print(f"Saved merged image to {save_path}")

        # Clean up the individual second image
        os.remove(second_image_path)

    # Clean up the first and third images if needed
    if first_image:
        os.remove(first_image_path)
    if third_image:
        os.remove(third_image_path)


# Function to get today's date in YYYY-MM-DD format
def get_today_date():
    return datetime.now().strftime('%Y-%m-%d')


# Function to check if the file exists in the folder
def get_file_path(folder_path):
    today_date = get_today_date()
    file_name = f"{today_date}.json"
    file_path = os.path.join(folder_path, file_name)
    
    # Check if the file exists
    if os.path.exists(file_path):
        return file_path
    else:
        print(f"File {file_name} does not exist.")
        return None


# Main function to get match information
def get_match_information(folder_path):
    file_path = get_file_path(folder_path)
    
    if file_path:
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Loop over all the top-level keys (different sports)
        all_sports_matches = {}
        for sport, matches in data.items():
            print(f"Processing sport: {sport}")
            
            # Store matches for each sport in a dictionary
            all_sports_matches[sport] = matches

        return all_sports_matches  # Return all sports with their respective matches
    else:
        print("File not found.")
        return None


def main():
    folder_path = "."  # Specify your folder path
    
    # Get match information from the JSON file
    try:
        sports_matches = get_match_information(folder_path)
    except Exception as err:
        print(f"Couldn't load the json")
        print(err)

    # Iterate through each sport and its matches to create posters
    if sports_matches:
        for sport, matches in sports_matches.items():
            print(f"Processing matches for sport: {sport}")

            for match_data in matches:
                
                for match_name, match_info in match_data.items():  # Use the match name as key
                    try:
                        # Extract the URLs for home and away team logos dynamically
                        home_team_logo_url = match_info['strHomeTeamBadge']
                        away_team_logo_url = match_info['strAwayTeamBadge']

                        # Extract event details from the JSON
                        event_name = match_name.rstrip(':')  # Use match name directly, remove trailing colon if present
                        
                        # Define the invalid characters (e.g., /, \, :, *, ?, ", <, >, |)
                        invalid_chars = '/\\:*?"<>|'

                        # Create a translation map that replaces each invalid character with an underscore (_)
                        replacement_map = str.maketrans(invalid_chars, '-' * len(invalid_chars))

                        # Sanitize the event_name by replacing invalid characters with underscores
                        event_name = event_name.translate(replacement_map)

                        venue = match_info['Venue']
                        utc_time = match_info['UTC']
                        date_event = match_info['dateEvent']
                        date_event = date_event.replace('-','/')

                        sources = match_info['Sources']
                        if sources:
                            sources = sources.replace(' ,', ',').replace(' , ', ',').replace(': ', ':')  # Clean up spaces
                            sources_list = [source.strip() for source in sources.split(",")]  # Strip leading/trailing spaces after split

                        else:
                            sources = ['No sources found for this event']

                        utc_time_formatted, uk_time_formatted = convert_time_zones(utc_time)

                        home_team_logo = download_image(home_team_logo_url) if home_team_logo_url else None
                        away_team_logo = download_image(away_team_logo_url) if away_team_logo_url else None

                        league_banner_url = match_info['league_banner']
                        league_name = match_info['strLeague']

                        create_first_image(event_name, away_team_logo, home_team_logo, venue, date_event, uk_time_formatted, utc_time_formatted)
                        create_second_image(event_name, sources_list)

                        if league_banner_url:
                            create_third_image(event_name, league_banner_url)
                        
                        if league_name is None:
                            league_name = 'No_league'
                        merge_images(event_name, sport, league_name)
                    except Exception as err:
                        event_name = match_name.rstrip(':')
                        print(f"Couldn't generate poster for {event_name}")
                        print(err)
    else:
        print("No match information found for today.")

if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error running the code")
        print(err)