import pygame
import time
import threading
from dotenv import dotenv_values
from onebusaway import OnebusawaySDK
from datetime import datetime, timedelta
import pytz
from clock_display import ClockDisplay
from collections import defaultdict
from math import floor
import requests
import json
from enum import Enum

config = dotenv_values(".env")

API_KEY = config["API_KEY"]
REGION = config["REGION"]
if REGION is None:
    REGION = "America/Los_Angeles"
STATION_NAME = config["STATION_NAME"]
TIME_ZONE = pytz.timezone(REGION)
BASE_URL = 'https://api.pugetsound.onebusaway.org/'
LINK_STOP_ID_ANGLE_LAKE = "40_99610" # Cap Hill Station to Angle Lake
LINK_STOP_ID_LYNNWOOD = "40_99603" # Cap Hill Station to Lynnwood
BUS_STOP_ID = "1_29266" # E Olive Way & Summit Ave E
STREETCAR_STOP_ID = "1_11175" # Broadway And Denny
DATA_REFRESH_RATE = 35 # Fetch data every 35 seconds
SERVICE_ALERTS_REFRESH_RATE = 60 # Fetch service alerts every minute
time_zone = pytz.timezone(REGION)

global_arrival_data: list[tuple[tuple[str, str], list[dict]]] = [] 
last_data_refresh_time = 0
is_fetching_data = False

global_alerts_data: list[str] = []
is_fetching_alerts = False
alert_index = 0
alert_thresholds = ["SEVERE"]
ALERTS_URL = "https://s3.amazonaws.com/st-service-alerts-prod/alerts_pb.json"

night_mode: dict[str, int] = {}
night_cache: dict = {}

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
ALERT_YELLOW = (255, 179, 34)
LIGHT_YELLOW = (255, 255, 0)
GREEN = (0, 255, 100)
RED = (255, 0, 0)
LIGHT_GREY = (128, 128, 128)
ALERT_GREY = (67, 65, 66)
LINE_1_COLOR = (41, 130, 64)
LINE_2_COLOR = (0, 162, 224)
BUS_COLOR = (255, 116, 65)
STREETCAR_COLOR = (157, 28, 34)

FONT_PATH = 'fonts/Roboto/static/Roboto_Condensed-Bold.ttf'
CLOCK_FONT = 'fonts/Roboto/static/Roboto_Condensed-ExtraLight.ttf'
FONT_LARGE = pygame.font.Font(FONT_PATH, 60)
FONT_SMALL = pygame.font.Font(FONT_PATH, 42)
FONT_ALERT = pygame.font.Font(FONT_PATH, 24)
BAR_HEIGHT = 50

ICON_SIZE = 150

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

try:
    WARNING_ICON = pygame.image.load('icons/alert-octagon.png')
    # Scale the icon to fit nicely in the alert bar
    WARNING_ICON = pygame.transform.scale(WARNING_ICON, (ICON_SIZE, ICON_SIZE))
except pygame.error as e:
    print(f"Could not load warning icon: {e}")
    WARNING_ICON = None # Handle case where icon loading fails

client = OnebusawaySDK(**{
    "api_key" : API_KEY,
    "base_url" : BASE_URL
    })

def wrap_text(text, font, max_width):
    """Wraps text to fit within a maximum pixel width."""
    lines = []
    words = text.split(' ')
    current_line = []
    for word in words:
        # Check the width if the new word is added
        if font.size(' '.join(current_line + [word]))[0] <= max_width:
            current_line.append(word)
        else:
            # Start a new line
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line)) # Add the last line
    return lines

def draw_alert_box(surface, alert_text):
    global global_alerts_data
    """
    Draws a light grey alert box near the bottom of the screen with a warning icon
    and wrapped text.
    """
    if not alert_text:
        return
    
    if len(global_alerts_data) > 1:
        alert_text = "(" + str(alert_index + 1) + "/" + str(len(global_alerts_data)) + ") " + alert_text

    ALERT_HEIGHT = ICON_SIZE # Increased height to accommodate wrapped text
    BOTTOM_OFFSET = 20
    SIDE_PADDING = 20
    ICON_PADDING = 20
    TEXT_START_X_OFFSET = ICON_PADDING + ICON_SIZE + 10

    alert_rect = pygame.Rect(
        0, 
        surface.get_height() - ALERT_HEIGHT - BOTTOM_OFFSET, 
        surface.get_width(), 
        ALERT_HEIGHT
    )

    # Draw the light grey background
    pygame.draw.rect(surface, ALERT_GREY, alert_rect)

    # --- Draw Icon ---
    if WARNING_ICON:
        icon_rect = WARNING_ICON.get_rect(midleft=(alert_rect.x, alert_rect.centery))
        surface.blit(WARNING_ICON, icon_rect)
    
    # --- Draw Wrapped Text ---
    # Calculate the maximum width available for the text
    max_text_width = alert_rect.width - TEXT_START_X_OFFSET - SIDE_PADDING
    
    # Wrap the text using the helper function
    wrapped_lines = wrap_text(alert_text, FONT_ALERT, max_text_width) # Use FONT_SMALL for better wrapping

    # Determine vertical starting position for centered multi-line text
    # Start drawing lines at a Y position so the whole block is vertically centered
    total_text_height = len(wrapped_lines) * FONT_ALERT.get_linesize()
    current_y = alert_rect.centery - (total_text_height // 2)

    for line in wrapped_lines:
        text_surface = FONT_ALERT.render(line, True, ALERT_YELLOW)
        # Position each line starting just after the icon area, aligned left
        surface.blit(text_surface, (alert_rect.x + TEXT_START_X_OFFSET, current_y))
        current_y += FONT_ALERT.get_linesize() # Move down for the next line

def parse_query(stop, transit_mode_enum, filter=None) -> dict[tuple[str, str], list[dict]]:
    global night_mode
    transit_mode = str(transit_mode_enum)
    # If the stop is in night mode, don't bother calling the API. Just return the cached value.
    if transit_mode in night_mode.keys():
        # If we are near expiration time of the cache, clear the cache. Exit night mode and start querying again as normal
        if night_mode[transit_mode] < datetime.now().timestamp():
            del night_mode[transit_mode]
            del night_cache[transit_mode]
            response = client.arrival_and_departure.list(stop_id=stop, minutes_after=35, minutes_before=0)
            arrivals_and_departures = response.data.entry.arrivals_and_departures
        else:
            # If nothing is in the cache, make a one-time query for the next 6 hours
            if transit_mode not in night_cache.keys():
                response = client.arrival_and_departure.list(stop_id=stop, minutes_after=420, minutes_before=0)
                arrivals_and_departures = response.data.entry.arrivals_and_departures
                arr = arrivals_and_departures[:1][0]
                night_cache[transit_mode] = arr
                # Set night mode to end 20 minutes before the first arrival
                night_mode[transit_mode] = round(arr.scheduled_arrival_time/1000 - (60*20))
            else:
                # Otherwise, pull from the existing cache
                arrivals_and_departures = night_cache[transit_mode]
    else:
        # If the stop is not in night mode, query for the next 35 minutes
        response = client.arrival_and_departure.list(stop_id=stop, minutes_after=35, minutes_before=0)
        arrivals_and_departures = response.data.entry.arrivals_and_departures
    if transit_mode in night_mode.keys():
        arrivals_and_departures = arrivals_and_departures[:1]
    arr = defaultdict(list)
    for arr_dep in arrivals_and_departures:
        if filter != None:
            if arr_dep.trip_headsign != filter:
                continue
        headsign = arr_dep.trip_headsign
        headsign_len = len(headsign)
        # If headsign is too long, first try to eliminate extra words. If that is not enough, truncate it 
        if headsign_len > 18:
            headsign_words = headsign.split(" ")
            headsign = headsign_words[0] + " " + headsign_words[1]
            if len(headsign) > 18:
                headsign = headsign[:13]
            headsign += "..."
        arr[(
            arr_dep.route_short_name,
            headsign
        )].append({
            "predicted_arrival_time": arr_dep.predicted_arrival_time,
            "predicted_departure_time": arr_dep.predicted_departure_time,
            "scheduled_arrival_time": arr_dep.scheduled_arrival_time,
            "scheduled_departure_time": arr_dep.scheduled_departure_time,
            "predicted": arr_dep.predicted,
            "status": arr_dep.status,
            "trip": arr_dep.trip_id
        })
    return dict(arr)

class TransitMode(Enum):
    ANGLE = "ANGLE_LAKE"
    LYNNWOOD = "LYNNWOOD"
    BUS = "BUS"
    STREETCAR = "STREETCAR"

def fetch_transit_data():
    """Fetches data from OBA and updates the global data structure."""
    global global_arrival_data, is_fetching_data
    is_fetching_data = True

    try:
        # Without any optional parameters, uses the API default time window
        buffer_time = int((datetime.now() + timedelta(minutes=30)).timestamp())
        response_link_angle_lake = parse_query(LINK_STOP_ID_ANGLE_LAKE, TransitMode.ANGLE)
        if len(response_link_angle_lake) == 0:
            night_mode[str(TransitMode.ANGLE)] = buffer_time
        response_link_lynnwood = parse_query(LINK_STOP_ID_LYNNWOOD, TransitMode.LYNNWOOD)
        if len(response_link_lynnwood) == 0:
            night_mode[str(TransitMode.LYNNWOOD)] = buffer_time
        response_bus = parse_query(BUS_STOP_ID, TransitMode.BUS)
        if len(response_bus) == 0:
            night_mode[str(TransitMode.BUS)] = buffer_time
        response_streetcar = parse_query(STREETCAR_STOP_ID, TransitMode.STREETCAR, "Pioneer Square")
        if len(response_streetcar) == 0:
            night_mode[str(TransitMode.STREETCAR)] = buffer_time

        merged_responses = []

        for headsign in response_link_lynnwood:
            merged_responses.append((headsign, response_link_lynnwood[headsign]))
        for headsign in response_link_angle_lake:
            merged_responses.append((headsign, response_link_angle_lake[headsign]))
        for headsign in response_bus:
            merged_responses.append((headsign, response_bus[headsign]))
        for headsign in response_streetcar:
            merged_responses.append((headsign, response_streetcar[headsign]))
        global_arrival_data = merged_responses

    except Exception as e:
        time_str = datetime.now(TIME_ZONE).strftime("%H:%M")
        print(f"An error occurred at {time_str}: {e}")

    is_fetching_data = False

def draw_multi_colored_text(surface, data, surface_width, start_y, right_offset):
    # --- STEP 1: Calculate the Total Width ---
    total_width = 0
    
    # We create a list of rendered surfaces and calculate the total width
    rendered_parts = []
    
    for text_part, color in data:
        # Render the text part (we need to do this to get the exact width)
        text_surface = FONT_LARGE.render(text_part, True, color)
        
        # Store the surface and its width
        rendered_parts.append((text_surface, text_surface.get_width()))
        
        # Accumulate the width
        total_width += text_surface.get_width()
        
    # --- STEP 2: Determine the Starting X-Coordinate ---
    # The starting X is the screen's right edge, minus the total text width, 
    # minus the desired offset.
    start_x = surface_width - total_width - right_offset
    
    # --- STEP 3: Draw the Text ---
    x_offset = start_x
    
    for text_surface, width in rendered_parts:
        # Blit (draw) the surface onto the screen
        surface.blit(text_surface, (x_offset, start_y))
        
        # Increment the x_offset by the width of the text we just drew
        x_offset += width

def fetch_service_alerts():
    global global_alerts_data, is_fetching_alerts, alert_index, alert_thresholds
    is_fetching_alerts = True
    global_alerts_data = []

    try:
        # Make the GET request to the URL
        response = requests.get(ALERTS_URL)

        # Check if the request was successful (status code 200-299)
        response.raise_for_status()

        # Parse the data, checking only for SEVERE alerts
        data = response.json()
        for entity in data["entity"]:
            if entity["alert"]["severity_level"] not in alert_thresholds:
                continue
            for translation in entity["alert"]["header_text"]["translation"]:
                if translation["language"] == "en":
                    global_alerts_data.append(translation["text"])
                    break

    except requests.exceptions.RequestException as e:
        # Handle any potential errors during the request (e.g., network issues, invalid URL)
        print(f"An error occurred: {e}")
    except json.JSONDecodeError:
        # Handle cases where the response body does not contain valid JSON
        print("Failed to decode JSON from the response.")

    if alert_index >= len(global_alerts_data) - 1:
        alert_index = 0
    else:
        alert_index += 1
    is_fetching_alerts = False

fetch_transit_data() 
fetch_service_alerts()
last_data_refresh_time = time.time()
last_alert_refresh_time = time.time()

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

    if current_time - last_alert_refresh_time > SERVICE_ALERTS_REFRESH_RATE and not is_fetching_alerts:
        threading.Thread(target=fetch_service_alerts, daemon=True).start()
        last_alert_refresh_time = current_time

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

            colored_arr: list[tuple[str, tuple]] = []
            arrival_times = arrival[1][:4]
            num_schedules = len(arrival_times) # Get the correct count

            for j, schedule in enumerate(arrival_times): # Use enumerate to get the index j
                # ... (Existing logic for time_until and text_color remains the same)

                if schedule.get('predicted', False):
                    # Calculate minutes until arrival in real-time
                    now = round(datetime.now(TIME_ZONE).timestamp())
                    time_until = (schedule['predicted_arrival_time']/1000 - round(datetime.now(TIME_ZONE).timestamp()))
                    time_diff = (schedule['predicted_arrival_time']/1000 - schedule['scheduled_arrival_time']/1000)
                    if time_diff >= 300:
                        text_color = RED
                    elif time_diff >= 90:
                        text_color = LIGHT_YELLOW
                    elif time_diff <= -60:
                        text_color = GREEN
                else:
                    # Calculate minutes until arrival from scheduled time
                    time_until = (schedule['scheduled_arrival_time']/1000 - round(datetime.now(TIME_ZONE).timestamp()))
                    text_color = LIGHT_GREY

                minutes_until = floor(time_until / 60) # truncate to minute
                if minutes_until > 60:
                    minutes_str = datetime.fromtimestamp(schedule["scheduled_arrival_time"]/1000, TIME_ZONE).strftime("%H:%M")
                    text_color = WHITE
                elif minutes_until < 1:
                    minutes_str = "Now"
                else:
                    minutes_str = f"{minutes_until}"
                
                # 1. Append the minutes string
                colored_arr.append((minutes_str, text_color))

                # 2. Append a comma and space if it's NOT the last schedule
                if j < num_schedules - 1:
                    colored_arr.append((", ", WHITE))
                
            # 3. Append the final " min" suffix ONLY ONCE at the end of all times, if not end of service
            if num_schedules > 0 and colored_arr[-1][0] != "Now" and ":" not in colored_arr[-1][0]:
                colored_arr.append((" min", WHITE))

            # --- B. Prepare Text Surfaces and Circle ---
        
            # 1. Route Number Circle
            route_number = str(arrival[0][0]) # Ensure it's a string
            
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
            headsign_text = arrival[0][1]
            headsign_x_pos = X_ROUTE + ROUTE_CIRCLE_RADIUS + 10 # 10 pixels gap after the circle
            headsign_surface = FONT_LARGE.render(headsign_text, True, WHITE) # Use WHITE for headsign
            screen.blit(
                headsign_surface, 
                (headsign_x_pos, ROW_CENTER_Y - TEXT_CENTER_OFFSET) # Subtract half height
            )

            # 3. Minutes until Arrival Text
            draw_multi_colored_text(screen, colored_arr, SCREEN_WIDTH, ROW_CENTER_Y - TEXT_CENTER_OFFSET, 10)

            # Optional: Add a line separator (e.g., a thin rectangle)
            # pygame.draw.line(screen, WHITE, (0, row_y + line_spacing - 5), (SCREEN_WIDTH, row_y + line_spacing - 5), 1)

    else:
        # Display a loading/error message if the list is empty
        loading_text = FONT_LARGE.render("Loading Data...", True, WHITE)
        screen.blit(loading_text, (SCREEN_WIDTH/2 - loading_text.get_width()/2, SCREEN_HEIGHT/2))

    if global_alerts_data:
        draw_alert_box(screen, global_alerts_data[alert_index])

    pygame.display.flip()
    clock.tick(FPS)

print("Clean shutdown initiated. Thanks!")
pygame.quit()
