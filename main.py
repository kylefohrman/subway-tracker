import pygame
import time
import threading
from dotenv import dotenv_values
from onebusaway import OnebusawaySDK
from datetime import datetime
import pytz
from clock_display import ClockDisplay

config = dotenv_values(".env")

API_KEY = config["API_KEY"]
REGION = config["REGION"]
STATION_NAME = config["STATION_NAME"]
TIME_ZONE = pytz.timezone(REGION)
BASE_URL = 'https://api.pugetsound.onebusaway.org/'
LINK_STOP_ID_ANGLE_LAKE = "40_99610" # Cap Hill Station to Angle Lake
LINK_STOP_ID_LYNNWOOD = "40_99603" # Cap Hill Station to Lynnwood
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
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Upcoming Arrivals")

# Colors and Fonts
WHITE = (255, 255, 255)
BLACK = (23, 29, 34)
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
    bar_height=BAR_HEIGHT,
    station_name = STATION_NAME
)

client = OnebusawaySDK(**{
    "api_key" : API_KEY,
    "base_url" : BASE_URL
    })

def parse_query(stop):
    response = client.arrival_and_departure.list(stop_id=stop, minutes_after=40, minutes_before=0)
    arrivals_and_departures = response.data.entry.arrivals_and_departures
    if len(arrivals_and_departures) == 0:
        response = client.arrival_and_departure.list(stop_id=stop, minutes_after=300, minutes_before=0)
        arrivals_and_departures = response.data.entry.arrivals_and_departures[:1]
    arr = []
    for arr_dep in arrivals_and_departures:
        arr.append({
            "route": arr_dep.route_short_name,
            "headsign": arr_dep.trip_headsign,
            "predicted_arrival_time": arr_dep.predicted_arrival_time,
            "predicted_departure_time": arr_dep.predicted_departure_time,
            "scheduled_arrival_time": arr_dep.scheduled_arrival_time,
            "scheduled_departure_time": arr_dep.scheduled_departure_time,
            "predicted": arr_dep.predicted,
            "status": arr_dep.status,
            "trip": arr_dep.trip_id
        })
    return arr

def fetch_transit_data():
    """Fetches data from OBA and updates the global data structure."""
    global global_arrival_data, is_fetching_data
    is_fetching_data = True

    try:
        # Without any optional parameters, uses the API default time window
        response_link_angle_lake = parse_query(LINK_STOP_ID_ANGLE_LAKE)
        response_link_lynnwood = parse_query(LINK_STOP_ID_LYNNWOOD)
        response_bus = parse_query(BUS_STOP_ID)

        ### TODO: Merge similar stops for visibility

        merged_responses = response_link_angle_lake + response_link_lynnwood + response_bus
        merged_responses = sorted(merged_responses, key=lambda x: x['scheduled_arrival_time'])

        global_arrival_data = merged_responses

    except Exception as e:
        print(f"An error occurred at {datetime.now(TIME_ZONE).strftime("%H:%M")}: {e}")

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

    # 3. Drawing/Rendering (High Frequency)
    screen.fill(BLACK) 
    clock_display.draw()
    y_offset = BAR_HEIGHT + 10

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
            ROW_TOP_Y = y_offset + (i * ROW_SPACING)

            # 2. Calculate the center Y-coordinate for all elements in this row
            ROW_CENTER_Y = ROW_TOP_Y + (ROW_SPACING // 2)

            if arrival.get('predicted', False):
                now = round(datetime.now(TIME_ZONE).timestamp())
                time_until = (arrival['predicted_arrival_time']/1000 - round(datetime.now(TIME_ZONE).timestamp()))
                time_diff = (arrival['predicted_arrival_time']/1000 - arrival['scheduled_arrival_time']/1000)
                if time_diff >= 60:
                    text_color = YELLOW
                elif time_diff <= -60:
                    text_color = GREEN
            else:
                # Calculate minutes until arrival in real-time
                time_until = (arrival['scheduled_arrival_time']/1000 - round(datetime.now(TIME_ZONE).timestamp()))

            minutes_until = int(time_until / 60) # truncate to minute
            if minutes_until > 60:
                minutes_str = datetime.fromtimestamp(arrival["scheduled_arrival_time"]/1000, TIME_ZONE).strftime("%H:%M")
            elif minutes_until < 1:
                minutes_str = "Arriving"
            else:
                minutes_str = f"{minutes_until} min"

            # --- B. Prepare Text Surfaces and Circle ---
        
            # 1. Route Number Circle
            route_number = str(arrival['route']) # Ensure it's a string
            
            # Blit the circle
            if "1 Line" in route_number:
                route_number = "1"
                line_color = LINE_1_COLOR
            elif "2 Line" in route_number:
                route_number = "2"
                line_color = LINE_2_COLOR
            elif "8" in route_number:
                route_number = "8"
                line_color = BUS_COLOR
            elif "11" in route_number:
                route_number = "11"
                line_color = BUS_COLOR
            elif "Streetcar" in route_number:
                route_number = 'S'
                line_color = STREETCAR_COLOR
            else:
                line_color = BLACK
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