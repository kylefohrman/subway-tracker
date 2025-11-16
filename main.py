import pygame
import time
import threading
from dotenv import dotenv_values
import onebusaway
from datetime import datetime
import pytz

config = dotenv_values(".env")

API_KEY = config["API_KEY"]
REGION = config["REGION"]
TIME_ZONE = pytz.timezone(REGION)
BASE_URL = 'https://api.pugetsound.onebusaway.org/api/'
LINK_STOP_ID = "40_99610" # Cap Hill Station
BUS_STOP_ID = "" # E Olive Way & Summit Ave E
DATA_REFRESH_RATE = 30 # Fetch data every 30 seconds
time_zone = pytz.timezone(REGION)

global_arrival_data = [] 
last_data_refresh_time = 0
is_fetching_data = False

# Initialize Pygame modules
pygame.init()
pygame.font.init() # Initialize the font module

# Display Setup
# Replace with the size of your Raspberry Pi screen/monitor
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Subway Arrival Board")

# Colors and Fonts
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)

# Load a font (or use pygame.font.SysFont(None, size))
try:
    FONT_LARGE = pygame.font.Font(None, 48) 
    FONT_SMALL = pygame.font.Font(None, 30)
except pygame.error as e:
    # Fallback if no font is found
    FONT_LARGE = pygame.font.SysFont('dejavusans', 48)
    FONT_SMALL = pygame.font.SysFont('dejavusans', 30)

# Timing Variables
clock = pygame.time.Clock() # Used to limit FPS
FPS = 30

# client = onebusaway.OneBusAwayClient(
#     api_key=API_KEY,
#     base_url=BASE_URL
# )

def fetch_transit_data():
    """Fetches data from OBA and updates the global data structure."""
    global global_arrival_data, is_fetching_data
    is_fetching_data = True

    try:
        # Without any optional parameters, uses the API default time window
        # response_data = client.get_arrivals_and_departures_for_stop(
        #     stop_id=LINK_STOP_ID
        #     # minutes_after=10
        # )

        # print(f"Successfully fetched {len(response_data.arrivalsAndDepartures)} arrivals/departures.")
        # print(response_data)
        print("Transit client not yet initialized")

        # Using dummy data until I can obtain OneBusAway API key
        global_arrival_data = [
            {
                'route': 'A',
                'headsign': 'University Station',
                # Arrival at 6:04 PM (4 minutes from now)
                'arrival_time': datetime(2025, 11, 15, 18, 4, 0, tzinfo=TIME_ZONE),
                'status': 'ON TIME'
            },
            {
                'route': 'C',
                'headsign': 'Downtown Express',
                # Arrival at 6:09 PM (9 minutes from now)
                'arrival_time': datetime(2025, 11, 15, 18, 9, 0, tzinfo=TIME_ZONE),
                'status': 'LATE'
            },
            {
                'route': 'A',
                'headsign': 'Airport',
                # Arrival at 6:15 PM (15 minutes from now)
                'arrival_time': datetime(2025, 11, 15, 18, 15, 0, tzinfo=TIME_ZONE),
                'status': 'ON TIME'
            },
            {
                'route': 'B',
                'headsign': 'Redmond via I-90',
                # Arrival at 6:22 PM (22 minutes from now)
                'arrival_time': datetime(2025, 11, 15, 18, 22, 0, tzinfo=TIME_ZONE),
                'status': 'EARLY'
            },
            {
                'route': 'C',
                'headsign': 'Downtown Express',
                # Arrival at 6:28 PM (28 minutes from now)
                'arrival_time': datetime(2025, 11, 15, 18, 28, 0, tzinfo=TIME_ZONE),
                'status': 'ON TIME'
            }
        ]

    except Exception as e:
        print(f"An error occurred: {e}")

    is_fetching_data = False

fetch_transit_data() 
last_data_refresh_time = time.time()

running = True
while running:
    # --- 1. Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 2. Data Update (Low Frequency, using THREADING)
    current_time = time.time()
    if current_time - last_data_refresh_time > DATA_REFRESH_RATE and not is_fetching_data:
        # Start the API call in a new thread so the main loop doesn't freeze
        threading.Thread(target=fetch_transit_data, daemon=True).start()
        last_data_refresh_time = current_time
        print("Starting threaded data refresh...")

    # 3. Drawing/Rendering (High Frequency)
    screen.fill(BLACK) 
    y_offset = 20

    if global_arrival_data:
        # Loop through the GLOBAL data list updated by the thread
        for i, arrival in enumerate(global_arrival_data):
            
            # Calculate minutes until arrival in real-time
            time_until = arrival['arrival_time'] - datetime.now(TIME_ZONE)
            minutes_until = int(time_until.total_seconds() / 60)

            # ... (Rest of your drawing code using minutes_until, arrival['route'], etc.) ...
            
            # Example drawing using the new variables:
            color = RED if arrival['status'] == 'LATE' else GREEN
            minutes_text = FONT_LARGE.render(f"{minutes_until} min", True, color)
            
            row_y = y_offset + (i * 60)
            screen.blit(minutes_text, (SCREEN_WIDTH - 150, row_y))

    else:
        # Display a loading/error message if the list is empty
        loading_text = FONT_LARGE.render("Loading Data...", True, WHITE)
        screen.blit(loading_text, (SCREEN_WIDTH/2 - loading_text.get_width()/2, SCREEN_HEIGHT/2))

    pygame.display.flip()
    clock.tick(FPS)

print("Clean shutdown initiated. Thanks!")
pygame.quit()