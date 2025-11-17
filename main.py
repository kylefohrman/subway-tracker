import pygame
import time
import threading
from dotenv import dotenv_values
import onebusaway
from datetime import datetime
import pytz
from clock_display import ClockDisplay

config = dotenv_values(".env")

API_KEY = config["API_KEY"]
REGION = config["REGION"]
TIME_ZONE = pytz.timezone(REGION)
BASE_URL = 'https://api.pugetsound.onebusaway.org/api/'
LINK_STOP_ID = "40_99610" # Cap Hill Station
BUS_STOP_ID = "1_29266" # E Olive Way & Summit Ave E
STREETCAR_STOP_ID = "11175" # Broadway And Denny
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
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Subway Arrival Board")

# Colors and Fonts
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 100)
LINE_1_COLOR = (41,130,64)
LINE_2_COLOR = (0,162,224)
BUS_COLOR = (255,116,65)
STREETCAR_COLOR = (157,28,34)

FONT_PATH = 'fonts/Roboto/static/Roboto_Condensed-Bold.ttf'
CLOCK_FONT = 'fonts/Roboto/static/Roboto_Condensed-ExtraLight.ttf'
FONT_LARGE = pygame.font.Font(FONT_PATH, 60)
FONT_SMALL = pygame.font.Font(FONT_PATH, 42)
BAR_HEIGHT = 50

# Timing Variables
clock = pygame.time.Clock() # Used to limit FPS
FPS = 30

clock_display = ClockDisplay(
    screen=screen,
    screen_width=SCREEN_WIDTH,
    screen_height=SCREEN_HEIGHT,
    font_path=CLOCK_FONT,
    time_zone_str=REGION, # Use the time zone loaded from .env
    bar_height=BAR_HEIGHT
)

# client = onebusaway.OneBusAwayClient(
#     api_key=API_KEY,
#     base_url=BASE_URL
# )

def fetch_transit_data():
    """Fetches data from OBA and updates the global data structure."""
    global global_arrival_data, is_fetching_data
    is_fetching_data = True

    new_data = []

    try:
        # Without any optional parameters, uses the API default time window
        # response_link = client.arrival_and_departure.list(
        #     stop_id=LINK_STOP_ID
        #     # minutes_after=10
        # )

        # response_bus = client.arrival_and_departure.list(
        # stop_id=BUS_STOP_ID)

        # link_arrivals = response_link.data.entry.arrivals_and_departures
        # bus_arrivals = response_bus.data.entry.arrivals_and_departures

        ### TODO: Handle responses
        print("Transit client not yet initialized")

        # Using dummy data until I can obtain OneBusAway API key
        DATE=16
        global_arrival_data = [
            {
                'route': '2',
                'headsign': 'Lynwood',
                # Arrival at 6:04 PM (4 minutes from now)
                'predicted_arrival_time': 0,
                'predicted_departure_time': 0,
                'scheduled_arrival_time': datetime(2025, 11, DATE, 18, 4, 0, tzinfo=TIME_ZONE),
                'scheduled_departure_time': datetime(2025, 11, DATE, 18, 4, 0, tzinfo=TIME_ZONE),
                'predicted': False,
                'status': 'ON TIME'
            },
            {
                'route': '1',
                'headsign': 'Angle Lake',
                # Arrival at 6:04 PM (4 minutes from now)
                'predicted_arrival_time': datetime(2025, 11, DATE, 18, 9, 0, tzinfo=TIME_ZONE),
                'predicted_departure_time': datetime(2025, 11, DATE, 18, 9, 0, tzinfo=TIME_ZONE),
                'scheduled_arrival_time': datetime(2025, 11, DATE, 18, 8, 0, tzinfo=TIME_ZONE),
                'scheduled_departure_time': datetime(2025, 11, DATE, 18, 8, 0, tzinfo=TIME_ZONE),
                'predicted': True,
                'status': 'LATE'
            },
            {
                'route': '8',
                'headsign': 'Seattle Center',
                # Arrival at 6:15 PM (15 minutes from now)
                'predicted_arrival_time': datetime(2025, 11, DATE, 18, 13, 0, tzinfo=TIME_ZONE),
                'predicted_departure_time': datetime(2025, 11, DATE, 18, 13, 0, tzinfo=TIME_ZONE),
                'scheduled_arrival_time': datetime(2025, 11, DATE, 18, 15, 0, tzinfo=TIME_ZONE),
                'scheduled_departure_time': datetime(2025, 11, DATE, 18, 15, 0, tzinfo=TIME_ZONE),
                'predicted': True,
                'status': 'EARLY'
            },
            {
                'route': 'Streetcar',
                'headsign': 'Pioneer Square',
                # Arrival at 6:15 PM (15 minutes from now)
                'predicted_arrival_time': datetime(2025, 11, DATE, 18, 13, 0, tzinfo=TIME_ZONE),
                'predicted_departure_time': datetime(2025, 11, DATE, 18, 13, 0, tzinfo=TIME_ZONE),
                'scheduled_arrival_time': datetime(2025, 11, DATE, 18, 15, 0, tzinfo=TIME_ZONE),
                'scheduled_departure_time': datetime(2025, 11, DATE, 18, 15, 0, tzinfo=TIME_ZONE),
                'predicted': True,
                'status': 'EARLY'
            },
            {
                'route': '2',
                'headsign': 'Lynwood',
                # Arrival at 6:04 PM (4 minutes from now)
                'predicted_arrival_time': datetime(2025, 11, DATE, 18, 13, 0, tzinfo=TIME_ZONE),
                'predicted_departure_time': datetime(2025, 11, DATE, 18, 13, 0, tzinfo=TIME_ZONE),
                'scheduled_arrival_time': datetime(2025, 11, DATE, 18, 10, 0, tzinfo=TIME_ZONE),
                'scheduled_departure_time': datetime(2025, 11, DATE, 18, 10, 0, tzinfo=TIME_ZONE),
                'predicted': True,
                'status': 'ON TIME'
            },
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
    clock_display.draw()
    y_offset = BAR_HEIGHT + 20

    # Assuming FONT_LARGE is the largest element, calculate its height once
    FONT_HEIGHT = FONT_LARGE.get_height() 
    TEXT_CENTER_OFFSET = FONT_HEIGHT // 2
    ROUTE_CIRCLE_RADIUS = 35 # Increase this size for prominence (e.g., from 15 to 25)
    ROW_SPACING = 2*ROUTE_CIRCLE_RADIUS + 10 # Total height for the row area
    X_ROUTE = ROUTE_CIRCLE_RADIUS + 10 # X position for the circle center

    if global_arrival_data:
        # Loop through the GLOBAL data list updated by the thread
        for i, arrival in enumerate(global_arrival_data):
            text_color = WHITE
            # 1. Define the top edge of the current row block
            ROW_TOP_Y = BAR_HEIGHT + 20 + (i * ROW_SPACING)

            # 2. Calculate the center Y-coordinate for all elements in this row
            ROW_CENTER_Y = ROW_TOP_Y + (ROW_SPACING // 2)

            if arrival.get('predicted', False):
                time_until = arrival['predicted_arrival_time'] - datetime.now(TIME_ZONE)
                time_diff = arrival['predicted_arrival_time'] - arrival['scheduled_arrival_time']
                if time_diff.total_seconds() >= 60:
                    text_color = YELLOW
                elif time_diff.total_seconds() <= -60:
                    text_color = GREEN
            else:
                # Calculate minutes until arrival in real-time
                time_until = arrival['scheduled_arrival_time'] - datetime.now(TIME_ZONE)

            minutes_until = int(time_until.total_seconds() / 60)
            minutes_str = f"{minutes_until} min"

            # --- B. Prepare Text Surfaces and Circle ---
        
            # 1. Route Number Circle
            route_number = str(arrival['route']) # Ensure it's a string
            
            # Blit the circle
            if route_number == '1':
                line_color = LINE_1_COLOR
            elif route_number == '2':
                line_color = LINE_2_COLOR
            elif route_number == '8':
                line_color = BUS_COLOR
            elif route_number == 'Streetcar':
                route_number = 'S'
                line_color = STREETCAR_COLOR
            # Render the route number for placement inside the circle
            route_num_surface = FONT_LARGE.render(route_number, True, WHITE) # Use a smaller font for the number
            pygame.draw.circle(screen, line_color, (X_ROUTE, ROW_CENTER_Y), ROUTE_CIRCLE_RADIUS)

            # Center the route number text on the circle
            route_num_rect = route_num_surface.get_rect(center=(X_ROUTE, ROW_CENTER_Y))
            screen.blit(route_num_surface, route_num_rect)

            # 2. Headsign Text
            headsign_text = arrival['headsign']
            headsign_x_pos = X_ROUTE + ROUTE_CIRCLE_RADIUS + 10 # 10 pixels gap after the circle
            headsign_surface = FONT_LARGE.render(headsign_text, True, WHITE) # Use WHITE for headsign
            screen.blit(
                headsign_surface, 
                (headsign_x_pos, ROW_CENTER_Y - TEXT_CENTER_OFFSET) # Subtract half height
            )

            # 3. Minutes until Arrival Text
            minutes_text_surface = FONT_LARGE.render(minutes_str, True, text_color)
            minutes_x_pos = SCREEN_WIDTH - minutes_text_surface.get_width() - 10
            screen.blit(
                minutes_text_surface, 
                (minutes_x_pos, ROW_CENTER_Y - TEXT_CENTER_OFFSET)
            )

            # Optional: Add a line separator (e.g., a thin rectangle)
            # pygame.draw.line(screen, WHITE, (0, row_y + line_spacing - 5), (SCREEN_WIDTH, row_y + line_spacing - 5), 1)

    else:
        # Display a loading/error message if the list is empty
        loading_text = FONT_LARGE.render("Loading Data...", True, WHITE)
        screen.blit(loading_text, (SCREEN_WIDTH/2 - loading_text.get_width()/2, SCREEN_HEIGHT/2))

    pygame.display.flip()
    clock.tick(FPS)

print("Clean shutdown initiated. Thanks!")
pygame.quit()